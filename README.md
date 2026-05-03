# Agentic Travel Planner

Agentic travel-planning demo built with:
- a LangGraph-based orchestrator
- a FastAPI MCP server
- OpenTelemetry-based observability

## Overview

The application models a simple planning workflow:
- load user memory
- generate a tool plan
- execute MCP tool calls
- review the result
- persist updated memory

The repo is intentionally small, but the structure is production-oriented enough to demonstrate:
- agent orchestration
- service-to-service tool invocation
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

### 2. Start the MCP server

```bash
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8001
```

### 3. Run the orchestrator

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
```

For full telemetry configuration, see [docs/observability/README.md](docs/observability/README.md).

## Notes

- The orchestrator and MCP server should run as separate processes.
- In production, prefer app -> collector -> backend instead of exporting directly from the app to a hosted backend.
- If telemetry code changes, restart the MCP server so new tracing/metric behavior is active.
