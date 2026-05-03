import time
from typing import Any

import httpx
from pydantic import ValidationError

from common.telemetry import get_meter, get_tracer, metric_attributes
from orchestrator.config import Settings
from orchestrator.errors import ServiceDependencyError, ToolExecutionError
from orchestrator.logger import get_logger
from orchestrator.schemas import (
    FlightsResponse,
    HotelsResponse,
    ToolDescriptor,
    ToolRegistryResponse,
    WeatherResponse,
)

logger = get_logger("mcp_client")
tracer = get_tracer("travel-orchestrator.mcp_client")
meter = get_meter("travel-orchestrator.mcp_client")
tool_call_counter = meter.create_counter(
    "travel.mcp.tool.calls",
    description="Number of MCP tool calls from the orchestrator.",
)
tool_call_failures = meter.create_counter(
    "travel.mcp.tool.failures",
    description="Number of failed MCP tool calls from the orchestrator.",
)
tool_call_duration = meter.create_histogram(
    "travel.mcp.tool.duration",
    unit="s",
    description="Duration of MCP tool calls from the orchestrator.",
)
tool_registry_duration = meter.create_histogram(
    "travel.mcp.list_tools.duration",
    unit="s",
    description="Duration of MCP tool registry requests.",
)
tool_registry_failures = meter.create_counter(
    "travel.mcp.list_tools.failures",
    description="Number of failed MCP tool registry requests.",
)

TOOL_RESPONSE_MODELS = {
    "flights": FlightsResponse,
    "hotels": HotelsResponse,
    "weather": WeatherResponse,
}


class MCPClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.mcp_base_url
        self.timeout = settings.mcp_timeout_seconds

    async def list_tools(self) -> list[ToolDescriptor]:
        start = time.time()
        with tracer.start_as_current_span("mcp.list_tools"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(f"{self.base_url}/tools")
                    res.raise_for_status()
                    data = ToolRegistryResponse.model_validate(res.json())
            except httpx.HTTPStatusError as exc:
                tool_registry_failures.add(1, metric_attributes(operation="list_tools"))
                raise ServiceDependencyError(
                    f"MCP tool registry request failed with status {exc.response.status_code}.",
                    error_type="upstream_unavailable",
                    status_code=502,
                ) from exc
            except httpx.TimeoutException as exc:
                tool_registry_failures.add(1, metric_attributes(operation="list_tools"))
                raise ServiceDependencyError(
                    "MCP tool registry request timed out.",
                    error_type="timeout",
                    status_code=504,
                ) from exc
            except httpx.HTTPError as exc:
                tool_registry_failures.add(1, metric_attributes(operation="list_tools"))
                raise ServiceDependencyError(
                    "MCP tool registry request failed.",
                    error_type="upstream_unavailable",
                    status_code=502,
                ) from exc
            except Exception:
                tool_registry_failures.add(1, metric_attributes(operation="list_tools"))
                raise
        tool_registry_duration.record(time.time() - start)
        return data.tools

    async def call_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        start = time.time()
        logger.info(f"Calling tool: {tool_name}")
        attributes = metric_attributes(tool_name=tool_name)
        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("travel.tool_name", tool_name)
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        f"{self.base_url}/tools/{tool_name}",
                        json=payload,
                    )
                    res.raise_for_status()
                    data = self._validate_tool_response(tool_name, res.json())
            except httpx.HTTPStatusError as exc:
                tool_call_failures.add(1, attributes)
                raise self._tool_error_from_http(tool_name, exc) from exc
            except httpx.TimeoutException as exc:
                tool_call_failures.add(1, attributes)
                raise ToolExecutionError(
                    tool_name=tool_name,
                    error_type="timeout",
                    detail=f"MCP tool '{tool_name}' timed out.",
                    status_code=504,
                    retryable=True,
                ) from exc
            except httpx.HTTPError as exc:
                tool_call_failures.add(1, attributes)
                raise ToolExecutionError(
                    tool_name=tool_name,
                    error_type="upstream_unavailable",
                    detail=f"MCP tool '{tool_name}' is unavailable.",
                    status_code=502,
                    retryable=True,
                ) from exc
            except Exception:
                tool_call_failures.add(1, attributes)
                raise
        duration = round(time.time() - start, 3)
        tool_call_counter.add(1, attributes)
        tool_call_duration.record(time.time() - start, attributes)
        logger.info(f"Tool {tool_name} responded in {duration}s")
        return data

    def _validate_tool_response(self, tool_name: str, payload: Any) -> dict[str, Any]:
        model = TOOL_RESPONSE_MODELS.get(tool_name)
        if model is None:
            if not isinstance(payload, dict):
                raise ToolExecutionError(
                    tool_name=tool_name,
                    error_type="bad_response",
                    detail=f"MCP tool '{tool_name}' returned an unexpected response payload.",
                    status_code=502,
                    retryable=False,
                )
            return payload
        try:
            return model.model_validate(payload).model_dump(by_alias=True)
        except ValidationError as exc:
            raise ToolExecutionError(
                tool_name=tool_name,
                error_type="bad_response",
                detail=f"MCP tool '{tool_name}' returned an invalid response payload.",
                status_code=502,
                retryable=False,
            ) from exc

    def _tool_error_from_http(self, tool_name: str, exc: httpx.HTTPStatusError) -> ToolExecutionError:
        status_code = exc.response.status_code
        detail = self._extract_response_detail(exc.response)
        error_type, api_status, retryable = self._classify_http_status(status_code)

        return ToolExecutionError(
            tool_name=tool_name,
            error_type=error_type,
            detail=detail or f"MCP tool '{tool_name}' failed with status {status_code}.",
            status_code=api_status,
            retryable=retryable,
        )

    def _classify_http_status(self, status_code: int) -> tuple[str, int, bool]:
        if status_code == 404:
            return ("not_found", 404, False)
        if status_code in {400, 422}:
            return ("invalid_input", status_code, False)
        if 500 <= status_code <= 599:
            return ("upstream_unavailable", 502, True)
        return ("internal_error", 502, False)

    def _extract_response_detail(self, response: httpx.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            return text or None
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
        return None
