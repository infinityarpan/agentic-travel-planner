import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from orchestrator.logger import configure_logging
from orchestrator.schemas import (
    ActivitySearchRequest,
    ActivitiesResponse,
    FlightSearchRequest,
    FlightsResponse,
    FoodResponse,
    FoodSearchRequest,
    HotelSearchRequest,
    HotelsResponse,
    LocalTransportResponse,
    LocalTransportSearchRequest,
    ToolRegistryResponse,
    WeatherResponse,
    WeatherSearchRequest,
)
from mcp_server.mock_backend import (
    search_activities,
    search_flights,
    search_food,
    search_hotels,
    search_local_transport,
    search_weather,
)

configure_logging()
logger = logging.getLogger("mcp_server")

app = FastAPI(title="Travel Platform Mock Backend", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tools/flight_search", response_model=FlightsResponse)
def flight_search(payload: FlightSearchRequest):
    logger.info("Processing flight_search request")
    try:
        return search_flights(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tools/hotel_search", response_model=HotelsResponse)
def hotel_search(payload: HotelSearchRequest):
    logger.info("Processing hotel_search request")
    try:
        return search_hotels(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tools/activity_search", response_model=ActivitiesResponse)
def activity_search(payload: ActivitySearchRequest):
    logger.info("Processing activity_search request")
    try:
        return search_activities(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tools/local_transport_search", response_model=LocalTransportResponse)
def local_transport_search(payload: LocalTransportSearchRequest):
    logger.info("Processing local_transport_search request")
    try:
        return search_local_transport(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tools/food_search", response_model=FoodResponse)
def food_search(payload: FoodSearchRequest):
    logger.info("Processing food_search request")
    try:
        return search_food(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tools/weather_search", response_model=WeatherResponse)
def weather_search(payload: WeatherSearchRequest):
    logger.info("Processing weather_search request")
    try:
        return search_weather(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/tools", response_model=ToolRegistryResponse)
def list_tools():
    logger.info("Listing tools")
    return {
        "tools": [
            {"name": "flight_search", "endpoint": "/tools/flight_search"},
            {"name": "hotel_search", "endpoint": "/tools/hotel_search"},
            {"name": "activity_search", "endpoint": "/tools/activity_search"},
            {"name": "local_transport_search", "endpoint": "/tools/local_transport_search"},
            {"name": "food_search", "endpoint": "/tools/food_search"},
            {"name": "weather_search", "endpoint": "/tools/weather_search"},
        ]
    }
