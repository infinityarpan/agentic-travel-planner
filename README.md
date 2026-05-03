# Agentic Travel Planner

Agentic travel-planning demo built with:
- a LangGraph-based orchestrator
- a FastAPI MCP server
- OpenTelemetry-based observability

## Overview

The application models a travel-planning workflow behind a synchronous backend API:
- load user memory from SQLite
- generate a tool plan with an LLM
- execute MCP tool calls
- review the result
- persist updated memory and run history

The repo is intentionally small, but now demonstrates:
- agent orchestration behind a FastAPI service
- service-to-service tool invocation
- validated API and tool contracts
- traces, metrics, and correlated logs

## Repository Layout

```text
common/         Shared utilities, including telemetry bootstrap
orchestrator/   LangGraph workflow, agents, MCP client, memory, logging
mcp_server/     FastAPI MCP server with mock tool endpoints
docs/           Component-specific documentation
```

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Minimum variables for the orchestrator:

```bash
OPENAI_API_KEY=your-key
MCP_BASE_URL=http://127.0.0.1:8001
TRAVEL_DB_PATH=travel_planner.db
DEFAULT_USER_ID=user_1
```

### 3. Start the MCP server

```bash
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8001
```

### 4. Start the orchestrator API

```bash
uvicorn orchestrator.api:app --host 127.0.0.1 --port 8000
```

### 5. Call the planner API

```bash
curl -X POST http://127.0.0.1:8000/plan-trip \
  -H "Content-Type: application/json" \
  -d "{\"user_query\":\"Plan Goa trip under 20000 in nice weather\",\"user_id\":\"user_1\"}"
```

### 6. Inspect persisted runs and memory

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/1
curl http://127.0.0.1:8000/users/user_1/memory
```

### Optional: run the CLI smoke flow

```bash
python orchestrator/main.py
```

## Observability

The repo currently supports:
- traces via OpenTelemetry
- metrics via OpenTelemetry
- Python logs enriched with active `trace_id` and `span_id`

Telemetry is env-driven, OTLP-capable, and development-friendly with local fallback behavior.

See the component docs for details:
- [Observability](docs/observability/README.md)
- [Orchestrator](docs/orchestrator/README.md)
- [MCP Server](docs/mcp_server/README.md)

## Environment Variables

Common runtime variables:

```bash
APP_ENV=development
APP_VERSION=dev
OTEL_SERVICE_NAME=travel-orchestrator
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
APP_OTEL_SAMPLER=always_on
APP_OTEL_SAMPLER_ARG=1.0
APP_OTEL_METRICS_ENABLED=true
PLANNER_MODEL=gpt-4o-mini
CRITIC_MODEL=gpt-4o-mini
```

For full telemetry configuration, see [docs/observability/README.md](docs/observability/README.md).

## Notes

- The orchestrator and MCP server should run as separate processes.
- In production, prefer app -> collector -> backend instead of exporting directly from the app to a hosted backend.
- If telemetry code changes, restart the MCP server so new tracing/metric behavior is active.
