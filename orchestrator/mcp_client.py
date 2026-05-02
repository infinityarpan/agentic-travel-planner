# orchestrator/mcp_client.py

import httpx
import time
from common.telemetry import get_tracer
from logger import get_logger

MCP_BASE_URL = "http://127.0.0.1:8001"

logger = get_logger("mcp_client")
tracer = get_tracer("travel-orchestrator.mcp_client")

class MCPClient:

    async def list_tools(self):
        with tracer.start_as_current_span("mcp.list_tools"):
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{MCP_BASE_URL}/tools")
                res.raise_for_status()
                data = res.json()
                if "tools" not in data:
                    raise RuntimeError(
                        f"Unexpected MCP response from {MCP_BASE_URL}/tools: {data}"
                    )
        return data["tools"]

    async def call_tool(self, tool_name, payload):
        start = time.time()
        logger.info(f"Calling tool: {tool_name} | payload: {payload}")
        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("travel.tool_name", tool_name)
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{MCP_BASE_URL}/tools/{tool_name}",
                    json=payload,
                )
                res.raise_for_status()
        duration = round(time.time() - start, 3)
        logger.info(f"Tool {tool_name} responded in {duration}s")
        return res.json()
