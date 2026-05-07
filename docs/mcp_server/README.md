# Mock Backend Services

## Purpose

The MCP server now acts as an internal travel-platform backend simulator.

It does not mimic third-party vendors directly. Instead, it exposes internal domain services with business-realistic mock behavior.

## Entry Point

- [mcp_server/server.py](/d:/agentic_travel_planner/mcp_server/server.py)

## Current Service Catalog

### `GET /tools`

Returns the available internal service catalog.

### `POST /tools/flight_search`

Returns route-aware flight offers with fare tiers, pricing, baggage, and availability.

### `POST /tools/hotel_search`

Returns destination-specific hotel offers with comfort levels, nightly pricing, amenities, and occupancy limits.

### `POST /tools/activity_search`

Returns destination activities aligned to trip style and interests.

### `POST /tools/local_transport_search`

Returns local transport options such as private cab, self-drive car, scooter, or city pass.

### `POST /tools/food_search`

Returns dining recommendations with cuisine style and estimated spend.

### `POST /tools/weather_search`

Returns mocked destination weather summaries so package assembly stays fully controlled.

## Mock Behavior Goals

The mocks should remain:
- destination-specific
- budget-sensitive
- internally consistent across services
- capable of empty-result and over-budget scenarios

This layer is meant to feel like a real internal backend used by a travel planner.
