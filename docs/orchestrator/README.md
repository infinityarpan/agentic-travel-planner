# Orchestrator

## Purpose

The orchestrator is the workflow engine for the travel-planning flow. It coordinates:
- user memory loading
- planning
- MCP tool execution
- result review
- memory persistence

## Main Components

### Entry point

- [orchestrator/main.py](/d:/agentic_travel_planner/orchestrator/main.py)

Responsibilities:
- initialize tracing/metrics/log correlation
- build the LangGraph workflow
- create the initial workflow state
- run the graph under a root span

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
- load and save user memory to a JSON file
- persist simple user preferences derived from results

## State Model

Workflow state is defined in:
- [orchestrator/state.py](/d:/agentic_travel_planner/orchestrator/state.py)

Current state fields:
- `user_query`
- `user_id`
- `plan`
- `results`
- `feedback`
- `attempts`
- `memory`

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

- The orchestrator assumes the MCP server is reachable at `http://127.0.0.1:8001`.
- In production, prefer pointing OTLP to a collector rather than directly to a backend.
- If this component is split into more services later, keep `parentbased_traceidratio` sampling to preserve distributed trace consistency.
