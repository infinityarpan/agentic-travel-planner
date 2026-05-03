# orchestrator/mcp_client.py

import httpx
import time
from common.telemetry import get_meter, get_tracer, metric_attributes
from logger import get_logger

MCP_BASE_URL = "http://127.0.0.1:8001"

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

class MCPClient:

    async def list_tools(self):
        start = time.time()
        with tracer.start_as_current_span("mcp.list_tools"):
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.get(f"{MCP_BASE_URL}/tools")
                    res.raise_for_status()
                    data = res.json()
                    if "tools" not in data or not isinstance(data["tools"], list):
                        raise RuntimeError(
                            f"Unexpected MCP response from {MCP_BASE_URL}/tools: {data}"
                        )
            except Exception:
                tool_registry_failures.add(1, metric_attributes(operation="list_tools"))
                raise
        tool_registry_duration.record(time.time() - start)
        return data["tools"]

    async def call_tool(self, tool_name, payload):
        start = time.time()
        logger.info(f"Calling tool: {tool_name} | payload: {payload}")
        attributes = metric_attributes(tool_name=tool_name)
        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("travel.tool_name", tool_name)
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        f"{MCP_BASE_URL}/tools/{tool_name}",
                        json=payload,
                    )
                    res.raise_for_status()
                    data = res.json()
                    if not isinstance(data, dict):
                        raise RuntimeError(
                            f"Unexpected MCP response from {MCP_BASE_URL}/tools/{tool_name}: {data}"
                        )
            except Exception:
                tool_call_failures.add(1, attributes)
                raise
        duration = round(time.time() - start, 3)
        tool_call_counter.add(1, attributes)
        tool_call_duration.record(time.time() - start, attributes)
        logger.info(f"Tool {tool_name} responded in {duration}s")
        return data
