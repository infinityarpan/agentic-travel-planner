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
- generates timestamp-aware itineraries after package selection
- persists run history and learned user preferences to SQLite

This phase intentionally stops at:
- search
- recommendation
- package assembly
- itinerary generation

Booking and payment are deferred.

## Repository Layout

```text
orchestrator/   API, trip-brief agent, package builder, persistence, MCP client
mcp_server/     Internal mock backend services for search domains
frontend/       Minimal browser UI served by the orchestrator API
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

The orchestrator also serves the frontend UI. Once both services are running, open:

```text
http://127.0.0.1:8000/
```

The UI lets you submit a natural-language trip request, compare generated packages, select a package, view the itinerary, and inspect recent runs and user memory.

If port `8000` is already occupied, start the orchestrator on another port:

```bash
uvicorn orchestrator.api:app --host 127.0.0.1 --port 8010
```

Then open:

```text
http://127.0.0.1:8010/
```

### 5. Run with Docker Compose

Create a local `.env` file with at least your OpenAI key:

```bash
OPENAI_API_KEY=your-key
```

The `.env` file is ignored by Git and excluded from the Docker image context.

Then build and start both services:

```bash
docker compose up --build
```

Compose starts:
- mock backend at `http://127.0.0.1:8001`
- orchestrator API and frontend UI at `http://127.0.0.1:8000`

The containerized orchestrator stores SQLite data in the `travel-data` Docker volume at `/app/data/travel_planner.db`.

To stop the stack:

```bash
docker compose down
```

To also remove persisted Docker volume data:

```bash
docker compose down -v
```

### 6. Call the planner API directly

```bash
curl -X POST http://127.0.0.1:8000/plan-trip \
  -H "Content-Type: application/json" \
  -d "{\"user_query\":\"Plan a relaxed Goa trip for 2 people under 35000 with good food\",\"user_id\":\"user_1\",\"start_date\":\"2026-11-12\",\"end_date\":\"2026-11-15\"}"
```

### 7. Select a package and generate the itinerary

```bash
curl -X POST http://127.0.0.1:8000/runs/1/select-package \
  -H "Content-Type: application/json" \
  -d "{\"package_id\":\"goa-CCU-GOA-F1-GOA-H1\"}"
```

### 8. Inspect persisted runs and memory

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
They now also carry internal timing data such as schedule windows, travel times, and hotel timing constraints for itinerary generation.
