# orchestrator/nodes.py

import time
from common.telemetry import get_tracer
from agents import PlannerAgent, ExecutorAgent, CriticAgent
from mcp_client import MCPClient
from memory import Memory
from logger import get_logger

memory_store = Memory()
tracer = get_tracer("travel-orchestrator.nodes")

memory_load_logger = get_logger("memory_load")

def memory_load_node(state):
    with tracer.start_as_current_span("memory_load") as span:
        span.set_attribute("user.id", state["user_id"])
        memory_load_logger.info(f"Loading memory for user: {state['user_id']}")
        user_mem = memory_store.get_user_memory(state["user_id"])
        memory_load_logger.info(f"Loaded memory: {user_mem}")
        return {**state, "memory": user_mem}

memory_save_logger = get_logger("memory_save")

def memory_save_node(state):
    with tracer.start_as_current_span("memory_save") as span:
        span.set_attribute("user.id", state["user_id"])
        memory_save_logger.info("Saving user memory")
        preferences = {}

        for result in state.get("results", []):
            flights = result.get("flights", {}).get("flights")
            if flights:
                cheapest = min(flights, key=lambda x: x["price"])
                preferences["preferred_airline"] = cheapest["airline"]

        memory_store.update_user_memory(state["user_id"], preferences)
        memory_save_logger.info(f"Updated memory for user: {state['user_id']}")
        return state

mcp_client = MCPClient()

planner = PlannerAgent(mcp_client)
executor = ExecutorAgent(mcp_client)
critic = CriticAgent()

planner_logger = get_logger("planner")

async def planner_node(state):
    with tracer.start_as_current_span("planner") as span:
        span.set_attribute("user.id", state["user_id"])
        span.set_attribute("travel.user_query", state["user_query"])
        planner_logger.info(f"Planning for query: {state['user_query']}")
        plan = await planner.plan(state["user_query"], state["memory"])
        span.set_attribute("travel.plan_step_count", len(plan))
        planner_logger.info(f"Generated plan: {plan}")
        return {**state, "plan": plan}

executor_logger = get_logger("executor")

async def executor_node(state):
    with tracer.start_as_current_span("executor") as span:
        span.set_attribute("travel.plan_step_count", len(state["plan"]))
        executor_logger.info(f"Executing plan with {len(state['plan'])} steps")
        start = time.time()
        results = await executor.execute(state["plan"])
        duration = round(time.time() - start, 3)
        span.set_attribute("travel.execution_seconds", duration)
        executor_logger.info(f"Execution completed in {duration}s")
        executor_logger.info(f"Execution results: {results}")
        return {**state, "results": results}

critic_logger = get_logger("critic")

def critic_node(state):
    with tracer.start_as_current_span("critic") as span:
        span.set_attribute("travel.attempts", state["attempts"])
        critic_logger.info("Evaluating results")
        feedback = critic.review(state["user_query"], state["results"])
        critic_logger.info(f"Critic feedback: {feedback}")
        return {
            **state,
            "feedback": feedback,
            "attempts": state["attempts"] + 1
        }
