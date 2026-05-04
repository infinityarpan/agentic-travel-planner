# Travel Platform Backend Simulator

Fresh-start travel planning backend built around:
- a thin AI orchestrator for trip-brief extraction
- deterministic trip-package assembly
- business-realistic internal mock services for travel search

## Overview

The application models a travel-platform backend that:
- interprets a natural-language travel request into a normalized trip brief
- queries internal search services for flights, hotels, activities, local transport, food, and weather
- assembles ranked trip packages
- persists run history and learned user preferences to SQLite

This phase intentionally stops at:
- search
- recommendation
- package assembly

Booking and payment are deferred.

## Repository Layout

```text
orchestrator/   API, trip-brief agent, package builder, persistence, MCP client
mcp_server/     Internal mock backend services for search domains
docs/           Component-specific notes
```

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Minimum variables:

```bash
OPENAI_API_KEY=your-key
MCP_BASE_URL=http://127.0.0.1:8001
TRAVEL_DB_PATH=travel_planner.db
DEFAULT_USER_ID=user_1
INTERPRETER_MODEL=gpt-4o-mini
```

### 3. Start the mock backend services

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
  -d "{\"user_query\":\"Plan a relaxed 3-night Goa trip for 2 people under 35000 with good food\",\"user_id\":\"user_1\"}"
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

## Current Domain Services

The internal mock backend currently exposes:
- `flight_search`
- `hotel_search`
- `activity_search`
- `local_transport_search`
- `food_search`
- `weather_search`

All of them are mocked, but their behavior is designed to resemble an internal travel-platform backend rather than a toy API.
