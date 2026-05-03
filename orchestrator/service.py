from orchestrator.config import Settings
from orchestrator.graph import build_graph
from orchestrator.logger import get_logger
from orchestrator.mcp_client import MCPClient
from orchestrator.memory import Memory
from orchestrator.nodes import TravelPlannerNodes
from orchestrator.schemas import PlannerRunListResponse, PlannerRunRecord, TravelPlanRequest, TravelPlanResponse, UserMemoryResponse

logger = get_logger("travel_planner_service")


class TravelPlannerService:
    def __init__(self, settings: Settings):
        settings.validate()
        self.settings = settings
        self.memory_store = Memory(settings.database_path)
        self.mcp_client = MCPClient(settings)
        self.nodes = TravelPlannerNodes(settings, self.memory_store, self.mcp_client)
        self.graph = build_graph(self.nodes)

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

        try:
            logger.info(f"Starting trip planning run {run_id} for user {request.user_id}")
            result = await self.graph.ainvoke(initial_state)
        except Exception as exc:
            attempts = initial_state.get("attempts", 0)
            self.memory_store.fail_run(run_id, attempts=attempts, error_message=str(exc))
            raise

        self.memory_store.complete_run(
            run_id,
            status=result.get("status", result["feedback"]["status"]),
            attempts=result["attempts"],
            plan=result["plan"],
            results=result["results"],
            feedback=result["feedback"],
            memory_after=result.get("memory_after", memory_before),
        )
        logger.info(f"Completed trip planning run {run_id} with status {result.get('status', result['feedback']['status'])}")

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
