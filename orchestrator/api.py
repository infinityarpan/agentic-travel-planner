from pathlib import Path
import sys

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.telemetry import configure_tracing, instrument_fastapi
from orchestrator.config import Settings
from orchestrator.errors import (
    ConfigurationError,
    PersistenceError,
    ResourceNotFoundError,
    ServiceDependencyError,
    ToolExecutionError,
)
from orchestrator.schemas import (
    ErrorResponse,
    PlannerRunListResponse,
    PlannerRunRecord,
    TravelPlanRequest,
    TravelPlanResponse,
    UserMemoryResponse,
)
from orchestrator.service import TravelPlannerService


def create_app(
    service: TravelPlannerService | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    configure_tracing("travel-orchestrator")

    app = FastAPI(title="Agentic Travel Planner", version="1.1.0")
    instrument_fastapi(app)

    resolved_settings = settings or Settings.from_env()
    resolved_service = service or TravelPlannerService(resolved_settings)
    app.state.settings = resolved_settings
    app.state.service = resolved_service

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(_: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(detail=str(exc), error_type="not_found").model_dump(),
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(_: Request, exc: ConfigurationError):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(detail=str(exc), error_type="internal_error").model_dump(),
        )

    @app.exception_handler(PersistenceError)
    async def persistence_error_handler(_: Request, exc: PersistenceError):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(detail=str(exc), error_type="internal_error").model_dump(),
        )

    @app.exception_handler(ToolExecutionError)
    async def tool_execution_error_handler(_: Request, exc: ToolExecutionError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                error_type=exc.error_type,
                tool_name=exc.tool_name,
            ).model_dump(),
        )

    @app.exception_handler(ServiceDependencyError)
    async def service_dependency_error_handler(_: Request, exc: ServiceDependencyError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=exc.detail, error_type=exc.error_type).model_dump(),
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready", response_model=dict)
    def ready(request: Request):
        request.app.state.service.readiness_check()
        return {"status": "ready"}

    @app.post(
        "/plan-trip",
        response_model=TravelPlanResponse,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            504: {"model": ErrorResponse},
        },
    )
    async def plan_trip(payload: TravelPlanRequest, request: Request):
        return await request.app.state.service.plan_trip(payload)

    @app.get(
        "/runs/{run_id}",
        response_model=PlannerRunRecord,
        responses={404: {"model": ErrorResponse}},
    )
    def get_run(run_id: int, request: Request):
        return request.app.state.service.get_run(run_id)

    @app.get("/runs", response_model=PlannerRunListResponse)
    def list_runs(
        request: Request,
        user_id: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ):
        return request.app.state.service.list_runs(user_id=user_id, limit=limit)

    @app.get("/users/{user_id}/memory", response_model=UserMemoryResponse)
    def get_user_memory(user_id: str, request: Request):
        return request.app.state.service.get_user_memory(user_id)

    return app


app = create_app()
