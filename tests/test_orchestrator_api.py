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
    async def fake_interpret(user_query, memory, start_date=None, end_date=None):
        return TripBrief(
            origin="Kolkata",
            destination="Goa",
            start_date=start_date or "2026-11-12",
            end_date=end_date or "2026-11-15",
            duration_nights=3,
            traveler_count=2,
            total_budget=35000,
            trip_style="relaxed",
            interests=["beaches", "seafood"],
            food_preferences=["seafood"],
            constraints=["under budget"],
            travel_month=11,
            assumptions=["Assumed a 3-night weekend break."],
            arrival_time_preference="afternoon",
            departure_time_preference="evening",
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
                        "outbound_departure_time": "09:10",
                        "outbound_arrival_time": "12:05",
                        "inbound_departure_time": "17:20",
                        "inbound_arrival_time": "20:15",
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
                        "outbound_departure_time": "10:00",
                        "outbound_arrival_time": "12:55",
                        "inbound_departure_time": "16:40",
                        "inbound_arrival_time": "19:35",
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
                        "zone": "beach_strip",
                        "max_occupancy": 2,
                        "amenities": ["wifi", "breakfast"],
                        "availability_status": "available",
                        "check_in_window": {"label": "hotel check-in", "start_time": "14:00", "end_time": "22:00"},
                        "check_out_window": {"label": "hotel check-out", "start_time": "06:00", "end_time": "11:00"},
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
                        "zone": "beach_strip",
                        "max_occupancy": 3,
                        "amenities": ["pool", "breakfast", "beach shuttle"],
                        "availability_status": "available",
                        "check_in_window": {"label": "hotel check-in", "start_time": "14:00", "end_time": "22:00"},
                        "check_out_window": {"label": "hotel check-out", "start_time": "06:00", "end_time": "11:00"},
                        "explanation": "Balanced comfort near the beach.",
                    },
                ]
            },
            "activity_search": {
                "items": [
                    {
                        "id": "GOA-A1",
                        "name": "Sunrise Beach Walk",
                        "category": "leisure",
                        "zone": "beach_strip",
                        "duration_hours": 1.5,
                        "price_total": 1200,
                        "indoor": False,
                        "family_friendly": True,
                        "recommended_for": ["relaxed", "romantic"],
                        "slots": [{"label": "sunrise", "start_time": "06:15", "end_time": "07:45"}],
                        "explanation": "Good fit for relaxed beach mornings.",
                    },
                    {
                        "id": "GOA-A2",
                        "name": "Sunset Cruise",
                        "category": "leisure",
                        "zone": "beach_strip",
                        "duration_hours": 2.5,
                        "price_total": 2400,
                        "indoor": False,
                        "family_friendly": True,
                        "recommended_for": ["relaxed", "romantic"],
                        "slots": [{"label": "sunset", "start_time": "17:15", "end_time": "19:45"}],
                        "explanation": "Good fit for relaxed evenings.",
                    },
                    {
                        "id": "GOA-A3",
                        "name": "Old Goa Heritage Walk",
                        "category": "culture",
                        "zone": "heritage_quarter",
                        "duration_hours": 3.0,
                        "price_total": 1800,
                        "indoor": False,
                        "family_friendly": True,
                        "recommended_for": ["cultural", "family"],
                        "slots": [{"label": "morning", "start_time": "10:00", "end_time": "13:00"}],
                        "explanation": "Good fit for a daytime culture stop.",
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
                        "transfer_buffer_minutes": 12,
                        "explanation": "Comfort-focused option.",
                    },
                    {
                        "id": "GOA-T2",
                        "mode": "rental scooter",
                        "total_price": 1800,
                        "convenience_score": 7.2,
                        "coverage": "Beach hopping",
                        "transfer_buffer_minutes": 10,
                        "explanation": "Great for casual local movement.",
                    },
                ],
                "zone_travel_minutes": {
                    "airport": {"beach_strip": 55, "heritage_quarter": 70},
                    "beach_strip": {"airport": 55, "heritage_quarter": 30},
                    "heritage_quarter": {"airport": 70, "beach_strip": 30},
                },
            },
            "food_search": {
                "items": [
                    {
                        "id": "GOA-FD1",
                        "name": "Beach Shack Thali",
                        "cuisine": "coastal Indian",
                        "meal_type": "lunch",
                        "zone": "beach_strip",
                        "price_band": "budget",
                        "estimated_cost_per_person": 500,
                        "neighborhood": "Baga",
                        "meal_slots": [{"meal_type": "lunch", "start_time": "13:00", "end_time": "14:30"}],
                        "explanation": "Value local lunch.",
                    },
                    {
                        "id": "GOA-FD2",
                        "name": "Fisherman's Wharf Dinner",
                        "cuisine": "Goan seafood",
                        "meal_type": "dinner",
                        "zone": "beach_strip",
                        "price_band": "premium",
                        "estimated_cost_per_person": 1400,
                        "neighborhood": "Cavelossim",
                        "meal_slots": [{"meal_type": "dinner", "start_time": "19:30", "end_time": "21:00"}],
                        "explanation": "Signature seafood meal.",
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


def test_plan_trip_validation_error_for_reversed_dates(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={
            "user_query": "Plan Goa trip",
            "user_id": "user_1",
            "start_date": "2026-11-15",
            "end_date": "2026-11-12",
        },
    )

    assert response.status_code == 422


def test_plan_trip_returns_packages_without_selected_itinerary(tmp_path):
    service = build_service(tmp_path)
    stub_success(service)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={
            "user_query": "Plan a relaxed Goa trip under 35000 for 2 people",
            "user_id": "user_1",
            "start_date": "2026-11-12",
            "end_date": "2026-11-15",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["trip_brief"]["start_date"] == "2026-11-12"
    assert payload["trip_brief"]["end_date"] == "2026-11-15"
    assert payload["selected_package_id"] is None
    assert payload["itinerary"] == []
    assert len(payload["trip_packages"]) >= 1
    assert payload["trip_packages"][0]["itinerary_preview"]


def test_select_package_generates_itinerary_and_persists_it(tmp_path):
    service = build_service(tmp_path)
    stub_success(service)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    plan_response = client.post(
        "/plan-trip",
        json={
            "user_query": "Plan a relaxed Goa trip under 35000 for 2 people",
            "user_id": "user_1",
            "start_date": "2026-11-12",
            "end_date": "2026-11-15",
        },
    )
    payload = plan_response.json()
    package_id = payload["recommended_package"]["package_id"]

    select_response = client.post(
        f"/runs/{payload['run_id']}/select-package",
        json={"package_id": package_id},
    )

    assert select_response.status_code == 200
    selected = select_response.json()
    assert selected["status"] == "itinerary_ready"
    assert selected["selected_package_id"] == package_id
    assert len(selected["itinerary"]) == 4
    assert selected["itinerary"][0]["items"][0]["item_type"] == "flight"
    assert any(item["item_type"] == "hotel_checkin" for item in selected["itinerary"][0]["items"])
    assert any(item["item_type"] == "flight" for item in selected["itinerary"][-1]["items"])

    run_response = client.get(f"/runs/{payload['run_id']}")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["selected_package_id"] == package_id
    assert len(run_payload["itinerary"]) == 4
    assert run_payload["memory_after"]["last_selected_package_id"] == package_id


def test_unknown_package_returns_404(tmp_path):
    service = build_service(tmp_path)
    stub_success(service)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    plan_response = client.post(
        "/plan-trip",
        json={
            "user_query": "Plan a relaxed Goa trip under 35000 for 2 people",
            "user_id": "user_1",
            "start_date": "2026-11-12",
            "end_date": "2026-11-15",
        },
    )
    run_id = plan_response.json()["run_id"]

    select_response = client.post(
        f"/runs/{run_id}/select-package",
        json={"package_id": "missing-package"},
    )

    assert select_response.status_code == 404
    assert select_response.json()["error_type"] == "not_found"


def test_no_viable_package_maps_to_500(tmp_path):
    service = build_service(tmp_path)

    async def fake_interpret(user_query, memory, start_date=None, end_date=None):
        return TripBrief(
            origin="Kolkata",
            destination="Goa",
            start_date=start_date or "2026-11-12",
            end_date=end_date or "2026-11-15",
            duration_nights=3,
            traveler_count=2,
            total_budget=10000,
            trip_style="relaxed",
            interests=["beaches"],
            food_preferences=[],
            constraints=[],
            travel_month=11,
            assumptions=[],
            arrival_time_preference="afternoon",
            departure_time_preference="evening",
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
            "local_transport_search": {"options": [], "zone_travel_minutes": {}},
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
        json={
            "user_query": "Plan Goa trip under 10000",
            "user_id": "user_1",
            "start_date": "2026-11-12",
            "end_date": "2026-11-15",
        },
    )

    assert response.status_code == 500
    assert "No flight offers available" in response.json()["detail"]
    assert response.json()["error_type"] == "internal_error"
