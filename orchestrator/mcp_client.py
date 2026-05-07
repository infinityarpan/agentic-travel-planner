from typing import Any

import httpx

from orchestrator.config import Settings
from orchestrator.logger import get_logger
from orchestrator.schemas import (
    ActivitiesResponse,
    FlightsResponse,
    FoodResponse,
    HotelsResponse,
    LocalTransportResponse,
    ToolDescriptor,
    ToolRegistryResponse,
    WeatherResponse,
)

logger = get_logger("mcp_client")

TOOL_RESPONSE_MODELS = {
    "flight_search": FlightsResponse,
    "hotel_search": HotelsResponse,
    "activity_search": ActivitiesResponse,
    "local_transport_search": LocalTransportResponse,
    "food_search": FoodResponse,
    "weather_search": WeatherResponse,
}


class MCPClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.mcp_base_url

    async def list_tools(self) -> list[ToolDescriptor]:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/tools")
            res.raise_for_status()
            data = ToolRegistryResponse.model_validate(res.json())
        return data.tools

    async def call_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"Calling tool: {tool_name}")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/tools/{tool_name}",
                json=payload,
            )
            res.raise_for_status()
            data = self._validate_tool_response(tool_name, res.json())
        logger.info(f"Tool {tool_name} responded successfully")
        return data

    def _validate_tool_response(self, tool_name: str, payload: Any) -> dict[str, Any]:
        model = TOOL_RESPONSE_MODELS.get(tool_name)
        if model is None:
            if not isinstance(payload, dict):
                raise ValueError(f"Tool '{tool_name}' returned an unexpected response payload.")
            return payload
        return model.model_validate(payload).model_dump()
