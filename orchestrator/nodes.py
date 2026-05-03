from typing import Any

from orchestrator.agents import CriticAgent, ExecutorAgent, PlannerAgent
from orchestrator.config import Settings
from orchestrator.logger import get_logger
from orchestrator.mcp_client import MCPClient
from orchestrator.memory import Memory


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
        self.memory_load_logger.info(f"Loading memory for user: {state['user_id']}")
        user_mem = self.memory_store.get_user_memory(state["user_id"])
        self.memory_load_logger.info(f"Loaded memory: {user_mem}")
        return {**state, "memory": user_mem}

    def memory_save_node(self, state):
        self.memory_save_logger.info("Saving user memory")
        preferences: dict[str, Any] = {}

        for result in state.get("results", []):
            flights = result.get("flights", {}).get("flights")
            if flights:
                cheapest = min(flights, key=lambda x: x["price"])
                preferences["preferred_airline"] = cheapest["airline"]

        updated_memory = self.memory_store.update_user_memory(state["user_id"], preferences)
        self.memory_save_logger.info(f"Updated memory for user: {state['user_id']}")
        return {**state, "memory_after": updated_memory}

    async def planner_node(self, state):
        self.planner_logger.info(f"Planning for query: {state['user_query']}")
        plan = await self.planner.plan(state["user_query"], state["memory"])
        plan_payload = [step.model_dump() for step in plan]
        self.planner_logger.info(f"Generated plan: {plan_payload}")
        return {**state, "plan": plan_payload}

    async def executor_node(self, state):
        self.executor_logger.info(f"Executing plan with {len(state['plan'])} steps")
        results = await self.executor.execute(state["plan"])
        self.executor_logger.info("Execution completed")
        self.executor_logger.info(f"Execution results: {results}")
        return {**state, "results": results}

    async def critic_node(self, state):
        self.critic_logger.info("Evaluating results")
        feedback = await self.critic.review(state["user_query"], state["results"])
        self.critic_logger.info(f"Critic feedback: {feedback.model_dump()}")
        return {
            **state,
            "feedback": feedback.model_dump(),
            "attempts": state["attempts"] + 1,
            "status": feedback.status,
        }
