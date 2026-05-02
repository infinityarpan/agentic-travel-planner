import logging
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.telemetry import configure_tracing, instrument_fastapi

configure_tracing("travel-mcp-server")
logger = logging.getLogger("mcp_server")

app = FastAPI()
instrument_fastapi(app)


@app.post("/tools/flights")
def search_flights(payload: dict):
    logger.info("Processing flights request")
    return {
        "flights": [
            {"airline": "IndiGo", "price": 5000},
            {"airline": "Air India", "price": 6500}
        ]
    }


@app.post("/tools/hotels")
def search_hotels(payload: dict):
    logger.info("Processing hotels request")
    return {
        "hotels": [
            {"name": "Sea View Resort", "price": 3000},
            {"name": "Budget Inn", "price": 1500}
        ]
    }


@app.post("/tools/weather")
def get_weather(payload: dict):
    logger.info("Processing weather request")
    return {
        "weather": "Sunny, 30°C"
    }


@app.get("/tools")
def list_tools():
    logger.info("Listing tools")
    return {
        "tools": [
            {"name": "flights", "endpoint": "/tools/flights"},
            {"name": "hotels", "endpoint": "/tools/hotels"},
            {"name": "weather", "endpoint": "/tools/weather"},
        ]
    }
