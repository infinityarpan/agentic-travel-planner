# Orchestrator

## Purpose

The orchestrator is now both:
- the workflow engine for the travel-planning flow
- the FastAPI backend API that exposes synchronous trip planning

## Main Components

### Entry point

- [orchestrator/main.py](/d:/agentic_travel_planner/orchestrator/main.py)

Responsibilities:
- run a local CLI smoke flow against the same service layer used by the API

### API

- [orchestrator/api.py](/d:/agentic_travel_planner/orchestrator/api.py)

Responsibilities:
- initialize tracing/metrics/log correlation for the orchestrator service
- expose `POST /plan-trip`
- expose `GET /health` and `GET /ready`
- expose `GET /runs`, `GET /runs/{run_id}`, and `GET /users/{user_id}/memory`
- validate request/response payloads with Pydantic

### Service

- [orchestrator/service.py](/d:/agentic_travel_planner/orchestrator/service.py)

Responsibilities:
- create planner run records
- invoke the LangGraph workflow
- persist final run results
- shape the API response
- load persisted run history and user memory for API reads

### Graph definition

- [orchestrator/graph.py](/d:/agentic_travel_planner/orchestrator/graph.py)

Responsibilities:
- define node ordering
- define entry point
- define routing after critic evaluation

### Nodes

- [orchestrator/nodes.py](/d:/agentic_travel_planner/orchestrator/nodes.py)

Responsibilities:
- wrap business operations in graph nodes
- create business spans for each node
- record node-level metrics
- emit correlated logs

Node flow:
- `memory_load`
- `planner`
- `executor`
- `critic`
- `memory_save`

### Agents

- [orchestrator/agents.py](/d:/agentic_travel_planner/orchestrator/agents.py)

Responsibilities:
- build LLM prompts
- request planning and critic decisions from OpenAI
- execute MCP calls concurrently via the executor agent

### MCP client

- [orchestrator/mcp_client.py](/d:/agentic_travel_planner/orchestrator/mcp_client.py)

Responsibilities:
- call `/tools`
- call tool endpoints
- record tool-call metrics
- create MCP helper spans
- surface request/response failures

### Memory

- [orchestrator/memory.py](/d:/agentic_travel_planner/orchestrator/memory.py)

Responsibilities:
- persist user memory to SQLite
- persist planner run metadata and final results

## State Model

Workflow state is defined in:
- [orchestrator/state.py](/d:/agentic_travel_planner/orchestrator/state.py)

Current state fields:
- `run_id`
- `user_query`
- `user_id`
- `plan`
- `results`
- `feedback`
- `attempts`
- `memory`
- `memory_after`
- `status`

## Observability Behavior

The orchestrator contributes:
- root workflow span
- per-node spans
- MCP helper spans
- node metrics
- graph run metrics
- MCP client metrics
- logs with trace/span correlation

## Operational Notes

- The orchestrator reads runtime configuration from environment variables.
- `OPENAI_API_KEY` is required at startup.
- The orchestrator persists to SQLite via `TRAVEL_DB_PATH`.
- The orchestrator assumes the MCP server is reachable at `MCP_BASE_URL`.
- In production, prefer pointing OTLP to a collector rather than directly to a backend.
- If this component is split into more services later, keep `parentbased_traceidratio` sampling to preserve distributed trace consistency.
