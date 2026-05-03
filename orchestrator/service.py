import time

from common.telemetry import get_meter, get_tracer, metric_attributes
from orchestrator.config import Settings
from orchestrator.errors import ServiceDependencyError, ToolExecutionError
from orchestrator.graph import build_graph
from orchestrator.mcp_client import MCPClient
from orchestrator.memory import Memory
from orchestrator.nodes import TravelPlannerNodes
from orchestrator.schemas import PlannerRunListResponse, PlannerRunRecord, TravelPlanRequest, TravelPlanResponse, UserMemoryResponse

tracer = get_tracer("travel-orchestrator.service")
meter = get_meter("travel-orchestrator.service")
graph_run_counter = meter.create_counter(
    "travel.graph.runs",
    description="Number of graph runs.",
)
graph_run_duration = meter.create_histogram(
    "travel.graph.run.duration",
    unit="s",
    description="Duration of graph runs in seconds.",
)


class TravelPlannerService:
    def __init__(self, settings: Settings):
        settings.validate()
        self.settings = settings
        self.memory_store = Memory(settings.database_path)
        self.mcp_client = MCPClient(settings)
        self.nodes = TravelPlannerNodes(settings, self.memory_store, self.mcp_client)
        self.graph = build_graph(self.nodes, settings.critic_max_attempts)

    def readiness_check(self) -> None:
        self.memory_store.healthcheck()

    def get_run(self, run_id: int) -> PlannerRunRecord:
        return PlannerRunRecord.model_validate(self.memory_store.get_run(run_id))

    def list_runs(self, *, user_id: str | None = None, limit: int = 20) -> PlannerRunListResponse:
        limit = max(1, min(limit, 100))
        runs = [PlannerRunRecord.model_validate(run) for run in self.memory_store.list_runs(user_id=user_id, limit=limit)]
        return PlannerRunListResponse(runs=runs)

    def get_user_memory(self, user_id: str) -> UserMemoryResponse:
        return UserMemoryResponse(user_id=user_id, memory=self.memory_store.get_user_memory(user_id))

    async def plan_trip(self, request: TravelPlanRequest) -> TravelPlanResponse:
        memory_before = self.memory_store.get_user_memory(request.user_id)
        run_id = self.memory_store.create_run(request.user_id, request.user_query, memory_before)
        initial_state = {
            "run_id": run_id,
            "user_query": request.user_query,
            "user_id": request.user_id,
            "plan": [],
            "results": [],
            "feedback": {},
            "attempts": 0,
            "memory": memory_before,
            "memory_after": memory_before,
            "status": "running",
        }

        start = time.time()
        try:
            with tracer.start_as_current_span("travel_planner.run") as span:
                span.set_attribute("user.id", request.user_id)
                span.set_attribute("travel.user_query", request.user_query)
                result = await self.graph.ainvoke(initial_state)
                span.set_attribute("travel.plan_step_count", len(result.get("plan", [])))
                span.set_attribute("travel.attempts", result.get("attempts", 0))
                attributes = metric_attributes(run_type="travel_planner")
                graph_run_counter.add(1, attributes)
                graph_run_duration.record(time.time() - start, attributes)
        except ToolExecutionError as exc:
            attempts = initial_state.get("attempts", 0)
            self.memory_store.fail_run(run_id, attempts=attempts, error_message=str(exc))
            raise
        except ServiceDependencyError as exc:
            attempts = initial_state.get("attempts", 0)
            self.memory_store.fail_run(run_id, attempts=attempts, error_message=exc.detail)
            raise
        except Exception as exc:
            attempts = initial_state.get("attempts", 0)
            self.memory_store.fail_run(run_id, attempts=attempts, error_message=str(exc))
            raise ServiceDependencyError(f"Trip planning failed: {exc}") from exc

        self.memory_store.complete_run(
            run_id,
            status=result.get("status", result["feedback"]["status"]),
            attempts=result["attempts"],
            plan=result["plan"],
            results=result["results"],
            feedback=result["feedback"],
            memory_after=result.get("memory_after", memory_before),
        )

        return TravelPlanResponse(
            run_id=run_id,
            user_query=request.user_query,
            user_id=request.user_id,
            plan=result["plan"],
            results=result["results"],
            feedback=result["feedback"],
            attempts=result["attempts"],
            memory_used=memory_before,
            memory_updated=result.get("memory_after", memory_before),
            status=result.get("status", result["feedback"]["status"]),
        )
