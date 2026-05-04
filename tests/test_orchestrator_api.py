import os

from fastapi.testclient import TestClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from orchestrator.api import create_app
from orchestrator.config import Settings
from orchestrator.schemas import ToolDescriptor, TripBrief
from orchestrator.service import TravelPlannerService


def build_service(tmp_path):
    settings = Settings(
        openai_api_key="test-key",
        interpreter_model="gpt-4o-mini",
        mcp_base_url="http://127.0.0.1:8001",
        database_path=str(tmp_path / "travel_planner.db"),
        default_user_id="user_1",
    )
    return TravelPlannerService(settings)


def stub_success(service: TravelPlannerService):
    async def fake_interpret(user_query, memory):
        return TripBrief(
            origin="Kolkata",
            destination="Goa",
            duration_nights=3,
            traveler_count=2,
            total_budget=35000,
            trip_style="relaxed",
            interests=["beaches", "seafood"],
            food_preferences=["seafood"],
            constraints=["under budget"],
            travel_month=11,
            assumptions=["Assumed a 3-night weekend break."],
        )

    async def fake_list_tools():
        return [
            ToolDescriptor(name="flight_search", endpoint="/tools/flight_search"),
            ToolDescriptor(name="hotel_search", endpoint="/tools/hotel_search"),
            ToolDescriptor(name="activity_search", endpoint="/tools/activity_search"),
            ToolDescriptor(name="local_transport_search", endpoint="/tools/local_transport_search"),
            ToolDescriptor(name="food_search", endpoint="/tools/food_search"),
            ToolDescriptor(name="weather_search", endpoint="/tools/weather_search"),
        ]

    async def fake_call_tool(tool_name, payload):
        fixtures = {
            "flight_search": {
                "offers": [
                    {
                        "id": "CCU-GOA-F1",
                        "airline": "SkyJet",
                        "tier": "saver",
                        "origin": "Kolkata",
                        "destination": "Goa",
                        "total_price": 12800,
                        "duration_hours": 2.9,
                        "baggage_kg": 15,
                        "seats_left": 7,
                        "availability_status": "available",
                        "explanation": "Value flight for Goa demand.",
                    },
                    {
                        "id": "CCU-GOA-F2",
                        "airline": "Vista Air",
                        "tier": "flex",
                        "origin": "Kolkata",
                        "destination": "Goa",
                        "total_price": 15100,
                        "duration_hours": 3.1,
                        "baggage_kg": 20,
                        "seats_left": 5,
                        "availability_status": "available",
                        "explanation": "Flexible fare for Goa demand.",
                    },
                ]
            },
            "hotel_search": {
                "offers": [
                    {
                        "id": "GOA-H1",
                        "name": "Palm Cove Residency",
                        "comfort_level": "economy",
                        "nightly_rate": 2800,
                        "total_price": 8400,
                        "star_rating": 3.4,
                        "area": "Calangute",
                        "max_occupancy": 2,
                        "amenities": ["wifi", "breakfast"],
                        "availability_status": "available",
                        "explanation": "Budget-friendly beach stay.",
                    },
                    {
                        "id": "GOA-H2",
                        "name": "Harbor Breeze Suites",
                        "comfort_level": "comfort",
                        "nightly_rate": 4200,
                        "total_price": 12600,
                        "star_rating": 4.1,
                        "area": "Candolim",
                        "max_occupancy": 3,
                        "amenities": ["pool", "breakfast", "beach shuttle"],
                        "availability_status": "available",
                        "explanation": "Balanced comfort near the beach.",
                    },
                ]
            },
            "activity_search": {
                "items": [
                    {
                        "id": "GOA-A1",
                        "name": "Sunset Cruise",
                        "category": "leisure",
                        "duration_hours": 2.5,
                        "price_total": 2400,
                        "indoor": False,
                        "family_friendly": True,
                        "recommended_for": ["relaxed", "romantic"],
                        "explanation": "Good fit for relaxed beach evenings.",
                    },
                    {
                        "id": "GOA-A2",
                        "name": "Beach Shack Evening",
                        "category": "food",
                        "duration_hours": 2.0,
                        "price_total": 1500,
                        "indoor": False,
                        "family_friendly": True,
                        "recommended_for": ["foodie", "relaxed"],
                        "explanation": "Good fit for relaxed food-led evenings.",
                    },
                ]
            },
            "local_transport_search": {
                "options": [
                    {
                        "id": "GOA-T1",
                        "mode": "private cab",
                        "total_price": 3800,
                        "convenience_score": 9.1,
                        "coverage": "Door-to-door comfort",
                        "explanation": "Comfort-focused option.",
                    },
                    {
                        "id": "GOA-T2",
                        "mode": "rental scooter",
                        "total_price": 1800,
                        "convenience_score": 7.2,
                        "coverage": "Beach hopping",
                        "explanation": "Great for casual local movement.",
                    },
                ]
            },
            "food_search": {
                "items": [
                    {
                        "id": "GOA-FD1",
                        "name": "Fisherman's Wharf Dinner",
                        "cuisine": "Goan seafood",
                        "meal_type": "dinner",
                        "price_band": "premium",
                        "estimated_cost_per_person": 1400,
                        "neighborhood": "Cavelossim",
                        "explanation": "Signature seafood meal.",
                    },
                    {
                        "id": "GOA-FD2",
                        "name": "Beach Shack Thali",
                        "cuisine": "coastal Indian",
                        "meal_type": "lunch",
                        "price_band": "budget",
                        "estimated_cost_per_person": 500,
                        "neighborhood": "Baga",
                        "explanation": "Value local lunch.",
                    },
                ]
            },
            "weather_search": {
                "summary": {
                    "destination": "Goa",
                    "expected_condition": "Sunny",
                    "avg_temp_c": 30,
                    "season_tag": "peak",
                    "trip_advisory": "Popular season with stronger demand and higher prices.",
                }
            },
        }
        return fixtures[tool_name]

    service.interpreter.interpret = fake_interpret
    service.mcp_client.list_tools = fake_list_tools
    service.mcp_client.call_tool = fake_call_tool


def test_health(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}


def test_plan_trip_validation_error(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post("/plan-trip", json={})

    assert response.status_code == 422


def test_plan_trip_returns_package_and_persists_memory(tmp_path):
    service = build_service(tmp_path)
    stub_success(service)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan a relaxed Goa trip under 35000 for 2 people", "user_id": "user_1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["trip_brief"]["destination"] == "Goa"
    assert len(payload["trip_packages"]) >= 1
    assert payload["recommended_package"]["flight"]["destination"] == "Goa"
    assert payload["recommended_package"]["cost_breakdown"]["grand_total"] > 0
    assert payload["memory_updated"]["preferred_airline_tier"] in {"saver", "flex", "premium"}
    assert payload["memory_updated"]["hotel_comfort_level"] in {"economy", "comfort", "premium"}

    run_response = client.get(f"/runs/{payload['run_id']}")
    assert run_response.status_code == 200
    assert run_response.json()["recommended_package"]["hotel"]["name"]
    assert run_response.json()["trip_brief"]["trip_style"] == "relaxed"

    runs_response = client.get("/runs", params={"user_id": "user_1"})
    assert runs_response.status_code == 200
    assert len(runs_response.json()["runs"]) == 1

    memory_response = client.get("/users/user_1/memory")
    assert memory_response.status_code == 200
    assert memory_response.json()["memory"]["activity_style"] == "relaxed"


def test_missing_run_returns_404(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.get("/runs/999")

    assert response.status_code == 404
    assert response.json()["error_type"] == "not_found"


def test_no_viable_package_maps_to_500(tmp_path):
    service = build_service(tmp_path)

    async def fake_interpret(user_query, memory):
        return TripBrief(
            origin="Kolkata",
            destination="Goa",
            duration_nights=3,
            traveler_count=2,
            total_budget=10000,
            trip_style="relaxed",
            interests=["beaches"],
            food_preferences=[],
            constraints=[],
            travel_month=11,
            assumptions=[],
        )

    async def fake_list_tools():
        return [
            ToolDescriptor(name="flight_search", endpoint="/tools/flight_search"),
            ToolDescriptor(name="hotel_search", endpoint="/tools/hotel_search"),
            ToolDescriptor(name="activity_search", endpoint="/tools/activity_search"),
            ToolDescriptor(name="local_transport_search", endpoint="/tools/local_transport_search"),
            ToolDescriptor(name="food_search", endpoint="/tools/food_search"),
            ToolDescriptor(name="weather_search", endpoint="/tools/weather_search"),
        ]

    async def fake_call_tool(tool_name, payload):
        fixtures = {
            "flight_search": {"offers": []},
            "hotel_search": {"offers": []},
            "activity_search": {"items": []},
            "local_transport_search": {"options": []},
            "food_search": {"items": []},
            "weather_search": {
                "summary": {
                    "destination": "Goa",
                    "expected_condition": "Sunny",
                    "avg_temp_c": 30,
                    "season_tag": "peak",
                    "trip_advisory": "Popular season.",
                }
            },
        }
        return fixtures[tool_name]

    service.interpreter.interpret = fake_interpret
    service.mcp_client.list_tools = fake_list_tools
    service.mcp_client.call_tool = fake_call_tool
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 10000", "user_id": "user_1"},
    )

    assert response.status_code == 500
    assert "No flight offers available" in response.json()["detail"]
    assert response.json()["error_type"] == "internal_error"
