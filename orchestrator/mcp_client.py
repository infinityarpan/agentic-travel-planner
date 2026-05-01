# orchestrator/mcp_client.py

import httpx
import time
from logger import get_logger

MCP_BASE_URL = "http://127.0.0.1:8001"

logger = get_logger("mcp_client")

class MCPClient:

    async def list_tools(self, trace_id=None):
        headers = {"X-Trace-Id": trace_id} if trace_id else None
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{MCP_BASE_URL}/tools", headers=headers)
            res.raise_for_status()
            data = res.json()
            if "tools" not in data:
                raise RuntimeError(
                    f"Unexpected MCP response from {MCP_BASE_URL}/tools: {data}"
                )
        return data["tools"]

    async def call_tool(self, tool_name, payload, trace_id=None):
        start = time.time()
        trace_prefix = f"[{trace_id}] " if trace_id else ""
        headers = {"X-Trace-Id": trace_id} if trace_id else None
        logger.info(f"{trace_prefix}Calling tool: {tool_name} | payload: {payload}")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{MCP_BASE_URL}/tools/{tool_name}",
                json=payload,
                headers=headers
            )
            res.raise_for_status()
        duration = round(time.time() - start, 3)
        logger.info(f"{trace_prefix}Tool {tool_name} responded in {duration}s")
        return res.json()
