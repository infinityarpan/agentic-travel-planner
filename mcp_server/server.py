import logging
import sys
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.telemetry import configure_tracing, get_meter, instrument_fastapi, metric_attributes
from orchestrator.config import Settings
from orchestrator.schemas import (
    FlightSearchRequest,
    FlightsResponse,
    HotelSearchRequest,
    HotelsResponse,
    ToolRegistryResponse,
    WeatherRequest,
    WeatherResponse,
)

settings = Settings.from_env()
configure_tracing("travel-mcp-server")
logger = logging.getLogger("mcp_server")
meter = get_meter("travel-mcp-server")
request_counter = meter.create_counter(
    "travel.mcp.server.requests",
    description="Number of requests handled by the MCP server.",
)
request_failures = meter.create_counter(
    "travel.mcp.server.failures",
    description="Number of failed requests handled by the MCP server.",
)
request_successes = meter.create_counter(
    "travel.mcp.server.successes",
    description="Number of successful requests handled by the MCP server.",
)
request_duration = meter.create_histogram(
    "travel.mcp.server.duration",
    unit="s",
    description="Duration of MCP server requests in seconds.",
)

app = FastAPI(title="Travel MCP Server", version="1.0.0")
instrument_fastapi(app)


def record_request_metrics(tool_name, start_time, failed=False):
    attributes = metric_attributes(tool_name=tool_name)
    request_counter.add(1, attributes)
    if failed:
        request_failures.add(1, attributes)
    else:
        request_successes.add(1, attributes)
    request_duration.record(time.time() - start_time, attributes)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tools/flights", response_model=FlightsResponse)
def search_flights(payload: FlightSearchRequest):
    start = time.time()
    failed = False
    logger.info("Processing flights request")
    try:
        flights = [
            {"airline": "IndiGo", "price": 5000},
            {"airline": "Air India", "price": 6500},
        ]
        if payload.airline:
            flights = [flight for flight in flights if flight["airline"].lower() == payload.airline.lower()] or flights
        if payload.budget is not None:
            flights = [flight for flight in flights if flight["price"] <= payload.budget] or flights
        return {"flights": flights}
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("flights", start, failed=failed)


@app.post("/tools/hotels", response_model=HotelsResponse)
def search_hotels(payload: HotelSearchRequest):
    start = time.time()
    failed = False
    logger.info("Processing hotels request")
    try:
        hotels = [
            {"name": "Sea View Resort", "price": 3000},
            {"name": "Budget Inn", "price": 1500},
        ]
        if payload.budget is not None:
            hotels = [hotel for hotel in hotels if hotel["price"] <= payload.budget] or hotels
        return {"hotels": hotels}
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("hotels", start, failed=failed)


@app.post("/tools/weather", response_model=WeatherResponse)
def get_weather(payload: WeatherRequest):
    start = time.time()
    failed = False
    logger.info("Processing weather request")
    try:
        if not settings.weather_enabled:
            raise HTTPException(status_code=503, detail="Weather integration is disabled.")

        with httpx.Client(timeout=settings.weather_timeout_seconds) as client:
            geocode = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": payload.location, "count": 1},
            )
            geocode.raise_for_status()
            geocode_data = geocode.json()
            results = geocode_data.get("results") or []
            if not results:
                raise HTTPException(status_code=404, detail=f"Location '{payload.location}' not found.")

            location = results[0]
            forecast = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": "temperature_2m,weather_code",
                },
            )
            forecast.raise_for_status()
            current = forecast.json().get("current", {})
            description = _describe_weather_code(current.get("weather_code"))
            temperature = current.get("temperature_2m")
            return {"weather": f"{description}, {temperature}°C"}
    except HTTPException:
        failed = True
        raise
    except Exception as exc:
        failed = True
        raise HTTPException(status_code=502, detail=f"Weather lookup failed: {exc}") from exc
    finally:
        record_request_metrics("weather", start, failed=failed)


@app.get("/tools", response_model=ToolRegistryResponse)
def list_tools():
    start = time.time()
    failed = False
    logger.info("Listing tools")
    try:
        return {
            "tools": [
                {"name": "flights", "endpoint": "/tools/flights"},
                {"name": "hotels", "endpoint": "/tools/hotels"},
                {"name": "weather", "endpoint": "/tools/weather"},
            ]
        }
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("tools_registry", start, failed=failed)


def _describe_weather_code(code):
    mapping = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        80: "Rain showers",
        95: "Thunderstorm",
    }
    return mapping.get(code, "Unknown weather")
