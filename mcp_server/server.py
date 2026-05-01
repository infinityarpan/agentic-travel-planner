# mcp_server/server.py

import logging
from fastapi import FastAPI, Header

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("mcp_server")

app = FastAPI()


def trace_prefix(trace_id):
    return f"[{trace_id}] " if trace_id else ""


# Mock tools
@app.post("/tools/flights")
def search_flights(payload: dict, x_trace_id: str | None = Header(default=None)):
    logger.info(f"{trace_prefix(x_trace_id)}Processing flights request")
    return {
        "flights": [
            {"airline": "IndiGo", "price": 5000},
            {"airline": "Air India", "price": 6500}
        ]
    }


@app.post("/tools/hotels")
def search_hotels(payload: dict, x_trace_id: str | None = Header(default=None)):
    logger.info(f"{trace_prefix(x_trace_id)}Processing hotels request")
    return {
        "hotels": [
            {"name": "Sea View Resort", "price": 3000},
            {"name": "Budget Inn", "price": 1500}
        ]
    }


@app.post("/tools/weather")
def get_weather(payload: dict, x_trace_id: str | None = Header(default=None)):
    logger.info(f"{trace_prefix(x_trace_id)}Processing weather request")
    return {
        "weather": "Sunny, 30°C"
    }


# Tool registry
@app.get("/tools")
def list_tools(x_trace_id: str | None = Header(default=None)):
    logger.info(f"{trace_prefix(x_trace_id)}Listing tools")
    return {
        "tools": [
            {"name": "flights", "endpoint": "/tools/flights"},
            {"name": "hotels", "endpoint": "/tools/hotels"},
            {"name": "weather", "endpoint": "/tools/weather"},
        ]
    }
