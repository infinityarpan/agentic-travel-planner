# MCP Server

## Purpose

The MCP server exposes tool endpoints used by the orchestrator. In the current repo it is a small FastAPI service with:
- flights
- hotels
- weather via a live Open-Meteo integration
- tool registry

## Entry Point

- [mcp_server/server.py](/d:/agentic_travel_planner/mcp_server/server.py)

Responsibilities:
- expose FastAPI routes
- emit plain application logs

## Endpoints

### `GET /tools`

Returns the tool registry used by the orchestrator planner.

### `POST /tools/flights`

Returns mocked flight results, optionally filtered by preferred airline or budget.

### `POST /tools/hotels`

Returns mocked hotel results, optionally filtered by budget.

### `POST /tools/weather`

Returns live weather results for the requested location.

## Runtime Assumptions

- The server is intended to run as a separate process from the orchestrator.
- The orchestrator currently expects it on `127.0.0.1:8001`.
- The server uses plain Python logging for request visibility.
