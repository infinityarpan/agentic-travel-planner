# Orchestrator

## Purpose

The orchestrator is the API-facing layer of the travel-platform simulator.

It is intentionally thin:
- AI interprets the user request into a structured trip brief
- deterministic logic builds service requests, assembles packages, ranks outcomes, and learns preferences

## Main Components

### API

- [orchestrator/api.py](/d:/agentic_travel_planner/orchestrator/api.py)

Responsibilities:
- expose `POST /plan-trip`
- expose `GET /health`
- expose `GET /runs`, `GET /runs/{run_id}`, and `GET /users/{user_id}/memory`
- validate request and response payloads

### Trip Brief Agent

- [orchestrator/agents.py](/d:/agentic_travel_planner/orchestrator/agents.py)

Responsibilities:
- extract origin, destination, budget, duration, style, and assumptions from natural language

### Service Client

- [orchestrator/mcp_client.py](/d:/agentic_travel_planner/orchestrator/mcp_client.py)

Responsibilities:
- call the internal backend service catalog
- validate service response contracts

### Package Builder

- [orchestrator/package_builder.py](/d:/agentic_travel_planner/orchestrator/package_builder.py)

Responsibilities:
- combine compatible offers into ranked trip packages
- compute budget fit and total estimated cost
- choose the recommended package

### Persistence

- [orchestrator/memory.py](/d:/agentic_travel_planner/orchestrator/memory.py)

Responsibilities:
- persist user preference memory
- persist normalized trip briefs, service traces, ranked packages, and selected recommendations

## Output Model

The main API response is product-oriented:
- normalized `trip_brief`
- ranked `trip_packages`
- `recommended_package`
- `cost_breakdown`
- `assumptions`

This layer should read like a backend for a travel product, not like raw tool execution logs.
