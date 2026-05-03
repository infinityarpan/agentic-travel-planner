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
- initialize telemetry
- expose FastAPI routes
- emit correlated logs
- record request metrics

## Endpoints

### `GET /tools`

Returns the tool registry used by the orchestrator planner.

### `POST /tools/flights`

Returns mocked flight results, optionally filtered by preferred airline or budget.

### `POST /tools/hotels`

Returns mocked hotel results, optionally filtered by budget.

### `POST /tools/weather`

Returns live weather results for the requested location.

## Observability Behavior

The server contributes:
- automatic FastAPI spans
- correlated logs with trace/span IDs
- per-endpoint metrics for:
  - total requests
  - successful requests
  - failed requests
  - request duration

Metric attribute used:
- `tool_name`

## Runtime Assumptions

- The server is intended to run as a separate process from the orchestrator.
- The orchestrator currently expects it on `127.0.0.1:8001`.
- Restart the server after telemetry changes so new instrumentation is active.

## Future Production Direction

When deployed behind real infrastructure:
- keep app code responsible for endpoint behavior and app-level telemetry
- let the collector/platform enrich infra metadata
- prefer collector-based export over direct backend export
