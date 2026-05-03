import time
from typing import Any

from common.telemetry import get_meter, get_tracer, metric_attributes
from orchestrator.agents import CriticAgent, ExecutorAgent, PlannerAgent
from orchestrator.config import Settings
from orchestrator.logger import get_logger
from orchestrator.mcp_client import MCPClient
from orchestrator.memory import Memory

tracer = get_tracer("travel-orchestrator.nodes")
meter = get_meter("travel-orchestrator.nodes")
node_run_counter = meter.create_counter(
    "travel.graph.node.runs",
    description="Number of node executions.",
)
node_run_duration = meter.create_histogram(
    "travel.graph.node.duration",
    unit="s",
    description="Duration of graph node executions in seconds.",
)


class TravelPlannerNodes:
    def __init__(self, settings: Settings, memory_store: Memory, mcp_client: MCPClient):
        self.settings = settings
        self.memory_store = memory_store
        self.planner = PlannerAgent(mcp_client, settings)
        self.executor = ExecutorAgent(mcp_client)
        self.critic = CriticAgent(settings)

        self.memory_load_logger = get_logger("memory_load")
        self.memory_save_logger = get_logger("memory_save")
        self.planner_logger = get_logger("planner")
        self.executor_logger = get_logger("executor")
        self.critic_logger = get_logger("critic")

    def memory_load_node(self, state):
        start = time.time()
        with tracer.start_as_current_span("memory_load") as span:
            span.set_attribute("user.id", state["user_id"])
            self.memory_load_logger.info(f"Loading memory for user: {state['user_id']}")
            user_mem = self.memory_store.get_user_memory(state["user_id"])
            self.memory_load_logger.info(f"Loaded memory: {user_mem}")
            attributes = metric_attributes(node_name="memory_load")
            node_run_counter.add(1, attributes)
            node_run_duration.record(time.time() - start, attributes)
            return {**state, "memory": user_mem}

    def memory_save_node(self, state):
        start = time.time()
        with tracer.start_as_current_span("memory_save") as span:
            span.set_attribute("user.id", state["user_id"])
            self.memory_save_logger.info("Saving user memory")
            preferences: dict[str, Any] = {}

            for result in state.get("results", []):
                flights = result.get("flights", {}).get("flights")
                if flights:
                    cheapest = min(flights, key=lambda x: x["price"])
                    preferences["preferred_airline"] = cheapest["airline"]

            updated_memory = self.memory_store.update_user_memory(state["user_id"], preferences)
            self.memory_save_logger.info(f"Updated memory for user: {state['user_id']}")
            attributes = metric_attributes(node_name="memory_save")
            node_run_counter.add(1, attributes)
            node_run_duration.record(time.time() - start, attributes)
            return {**state, "memory_after": updated_memory}

    async def planner_node(self, state):
        start = time.time()
        with tracer.start_as_current_span("planner") as span:
            span.set_attribute("user.id", state["user_id"])
            span.set_attribute("travel.user_query", state["user_query"])
            self.planner_logger.info(f"Planning for query: {state['user_query']}")
            plan = await self.planner.plan(state["user_query"], state["memory"])
            plan_payload = [step.model_dump() for step in plan]
            span.set_attribute("travel.plan_step_count", len(plan_payload))
            self.planner_logger.info(f"Generated plan: {plan_payload}")
            attributes = metric_attributes(node_name="planner")
            node_run_counter.add(1, attributes)
            node_run_duration.record(time.time() - start, attributes)
            return {**state, "plan": plan_payload}

    async def executor_node(self, state):
        start = time.time()
        with tracer.start_as_current_span("executor") as span:
            span.set_attribute("travel.plan_step_count", len(state["plan"]))
            self.executor_logger.info(f"Executing plan with {len(state['plan'])} steps")
            results = await self.executor.execute(state["plan"])
            duration = round(time.time() - start, 3)
            span.set_attribute("travel.execution_seconds", duration)
            self.executor_logger.info(f"Execution completed in {duration}s")
            self.executor_logger.info(f"Execution results: {results}")
            attributes = metric_attributes(node_name="executor")
            node_run_counter.add(1, attributes)
            node_run_duration.record(time.time() - start, attributes)
            return {**state, "results": results}

    async def critic_node(self, state):
        start = time.time()
        with tracer.start_as_current_span("critic") as span:
            span.set_attribute("travel.attempts", state["attempts"])
            self.critic_logger.info("Evaluating results")
            feedback = await self.critic.review(state["user_query"], state["results"])
            self.critic_logger.info(f"Critic feedback: {feedback.model_dump()}")
            attributes = metric_attributes(node_name="critic")
            node_run_counter.add(1, attributes)
            node_run_duration.record(time.time() - start, attributes)
            return {
                **state,
                "feedback": feedback.model_dump(),
                "attempts": state["attempts"] + 1,
                "status": feedback.status,
            }
