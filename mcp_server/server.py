import logging
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from orchestrator.config import Settings
from orchestrator.logger import configure_logging
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
configure_logging()
logger = logging.getLogger("mcp_server")

app = FastAPI(title="Travel MCP Server", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tools/flights", response_model=FlightsResponse)
def search_flights(payload: FlightSearchRequest):
    logger.info("Processing flights request")
    flights = [
        {"airline": "IndiGo", "price": 5000},
        {"airline": "Air India", "price": 6500},
    ]
    if payload.airline:
        flights = [flight for flight in flights if flight["airline"].lower() == payload.airline.lower()] or flights
    if payload.budget is not None:
        flights = [flight for flight in flights if flight["price"] <= payload.budget] or flights
    return {"flights": flights}


@app.post("/tools/hotels", response_model=HotelsResponse)
def search_hotels(payload: HotelSearchRequest):
    logger.info("Processing hotels request")
    hotels = [
        {"name": "Sea View Resort", "price": 3000},
        {"name": "Budget Inn", "price": 1500},
    ]
    if payload.budget is not None:
        hotels = [hotel for hotel in hotels if hotel["price"] <= payload.budget] or hotels
    return {"hotels": hotels}


@app.post("/tools/weather", response_model=WeatherResponse)
def get_weather(payload: WeatherRequest):
    logger.info("Processing weather request")
    with httpx.Client() as client:
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
        return {"weather": f"{description}, {temperature} deg C"}


@app.get("/tools", response_model=ToolRegistryResponse)
def list_tools():
    logger.info("Listing tools")
    return {
        "tools": [
            {"name": "flights", "endpoint": "/tools/flights"},
            {"name": "hotels", "endpoint": "/tools/hotels"},
            {"name": "weather", "endpoint": "/tools/weather"},
        ]
    }


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
