import os

from fastapi.testclient import TestClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("APP_OTEL_METRICS_ENABLED", "false")

from orchestrator.api import create_app
from orchestrator.config import Settings
from orchestrator.errors import ServiceDependencyError, ToolExecutionError
from orchestrator.schemas import CriticFeedback, PlanStep
from orchestrator.service import TravelPlannerService


def build_service(tmp_path):
    settings = Settings(
        openai_api_key="test-key",
        planner_model="gpt-4o-mini",
        critic_model="gpt-4o-mini",
        mcp_base_url="http://127.0.0.1:8001",
        database_path=str(tmp_path / "travel_planner.db"),
        default_user_id="user_1",
        critic_max_attempts=3,
        openai_max_retries=1,
        openai_retry_delay_seconds=0.0,
        mcp_timeout_seconds=1.0,
        weather_timeout_seconds=1.0,
        weather_enabled=True,
    )
    return TravelPlannerService(settings)


def stub_success(service: TravelPlannerService):
    async def fake_plan(user_query, memory):
        return [
            PlanStep(tool="weather", input={"location": "Goa"}),
            PlanStep(tool="flights", input={"from": "Kolkata", "to": "Goa", "budget": 10000}),
            PlanStep(tool="hotels", input={"location": "Goa", "budget": 10000}),
        ]

    async def fake_execute(plan):
        return [
            {"weather": {"weather": "Clear, 29C"}},
            {"flights": {"flights": [{"airline": "IndiGo", "price": 5000}]}},
            {"hotels": {"hotels": [{"name": "Sea View Resort", "price": 3000}]}},
        ]

    async def fake_review(user_query, results):
        return CriticFeedback(status="good", reason="Stubbed success")

    service.nodes.planner.plan = fake_plan
    service.nodes.executor.execute = fake_execute
    service.nodes.critic.review = fake_review


def test_health_and_ready(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_plan_trip_validation_error(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post("/plan-trip", json={})

    assert response.status_code == 422


def test_plan_trip_persists_run_and_memory(tmp_path):
    service = build_service(tmp_path)
    stub_success(service)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "good"
    assert payload["memory_updated"]["preferred_airline"] == "IndiGo"

    run_response = client.get(f"/runs/{payload['run_id']}")
    assert run_response.status_code == 200
    assert run_response.json()["feedback"]["reason"] == "Stubbed success"

    runs_response = client.get("/runs", params={"user_id": "user_1"})
    assert runs_response.status_code == 200
    assert len(runs_response.json()["runs"]) == 1

    memory_response = client.get("/users/user_1/memory")
    assert memory_response.status_code == 200
    assert memory_response.json()["memory"]["preferred_airline"] == "IndiGo"


def test_missing_run_returns_404(tmp_path):
    service = build_service(tmp_path)
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.get("/runs/999")

    assert response.status_code == 404
    assert response.json()["error_type"] == "not_found"


def test_dependency_failure_maps_to_502(tmp_path):
    service = build_service(tmp_path)

    async def broken_plan_trip(request):
        raise ServiceDependencyError("Upstream planner failed")

    service.plan_trip = broken_plan_trip
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream planner failed"
    assert response.json()["error_type"] == "internal_error"
    assert response.json()["tool_name"] is None


def test_location_not_found_dependency_failure_maps_to_404(tmp_path):
    service = build_service(tmp_path)

    async def broken_plan_trip(request):
        raise ToolExecutionError(
            tool_name="weather",
            error_type="not_found",
            detail="Location 'Mondarmoni' not found.",
            status_code=404,
            retryable=False,
        )

    service.plan_trip = broken_plan_trip
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Mondarmoni trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Location 'Mondarmoni' not found."
    assert response.json()["error_type"] == "not_found"
    assert response.json()["tool_name"] == "weather"


def test_tool_timeout_maps_to_504(tmp_path):
    service = build_service(tmp_path)

    async def broken_plan_trip(request):
        raise ToolExecutionError(
            tool_name="weather",
            error_type="timeout",
            detail="MCP tool 'weather' timed out.",
            status_code=504,
            retryable=True,
        )

    service.plan_trip = broken_plan_trip
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 504
    assert response.json()["error_type"] == "timeout"
    assert response.json()["tool_name"] == "weather"


def test_tool_invalid_input_maps_to_422(tmp_path):
    service = build_service(tmp_path)

    async def broken_plan_trip(request):
        raise ToolExecutionError(
            tool_name="hotels",
            error_type="invalid_input",
            detail="Budget must be non-negative.",
            status_code=422,
            retryable=False,
        )

    service.plan_trip = broken_plan_trip
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 422
    assert response.json()["error_type"] == "invalid_input"
    assert response.json()["tool_name"] == "hotels"


def test_tool_bad_response_maps_to_502(tmp_path):
    service = build_service(tmp_path)

    async def broken_plan_trip(request):
        raise ToolExecutionError(
            tool_name="flights",
            error_type="bad_response",
            detail="MCP tool 'flights' returned an invalid response payload.",
            status_code=502,
            retryable=False,
        )

    service.plan_trip = broken_plan_trip
    app = create_app(service=service, settings=service.settings)
    client = TestClient(app)

    response = client.post(
        "/plan-trip",
        json={"user_query": "Plan Goa trip under 20000", "user_id": "user_1"},
    )

    assert response.status_code == 502
    assert response.json()["error_type"] == "bad_response"
    assert response.json()["tool_name"] == "flights"
