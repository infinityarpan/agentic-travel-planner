import logging
import sys
import time
from pathlib import Path

from fastapi import FastAPI

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.telemetry import configure_tracing, get_meter, instrument_fastapi, metric_attributes

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

app = FastAPI()
instrument_fastapi(app)


def record_request_metrics(tool_name, start_time, failed=False):
    attributes = metric_attributes(tool_name=tool_name)
    request_counter.add(1, attributes)
    if failed:
        request_failures.add(1, attributes)
    else:
        request_successes.add(1, attributes)
    request_duration.record(time.time() - start_time, attributes)


@app.post("/tools/flights")
def search_flights(payload: dict):
    start = time.time()
    failed = False
    logger.info("Processing flights request")
    try:
        return {
            "flights": [
                {"airline": "IndiGo", "price": 5000},
                {"airline": "Air India", "price": 6500}
            ]
        }
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("flights", start, failed=failed)


@app.post("/tools/hotels")
def search_hotels(payload: dict):
    start = time.time()
    failed = False
    logger.info("Processing hotels request")
    try:
        return {
            "hotels": [
                {"name": "Sea View Resort", "price": 3000},
                {"name": "Budget Inn", "price": 1500}
            ]
        }
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("hotels", start, failed=failed)


@app.post("/tools/weather")
def get_weather(payload: dict):
    start = time.time()
    failed = False
    logger.info("Processing weather request")
    try:
        return {
            "weather": "Sunny, 30°C"
        }
    except Exception:
        failed = True
        raise
    finally:
        record_request_metrics("weather", start, failed=failed)


@app.get("/tools")
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
