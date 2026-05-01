# orchestrator/nodes.py

import time
from agents import PlannerAgent, ExecutorAgent, CriticAgent
from mcp_client import MCPClient
from memory import Memory
from logger import get_logger

memory_store = Memory()

memory_load_logger = get_logger("memory_load")

def memory_load_node(state):
    memory_load_logger.info(f"[{state['trace_id']}] Loading memory for user: {state['user_id']}")
    user_mem = memory_store.get_user_memory(state["user_id"])
    memory_load_logger.info(f"[{state['trace_id']}] Loaded memory: {user_mem}")
    return {**state, "memory": user_mem}

memory_save_logger = get_logger("memory_save")

def memory_save_node(state):

    # Example: store preference
    memory_save_logger.info(f"[{state['trace_id']}] Saving user memory")
    preferences = {}

    for result in state.get("results", []):
        flights = result.get("flights", {}).get("flights")
        if flights:
            cheapest = min(flights, key=lambda x: x["price"])
            preferences["preferred_airline"] = cheapest["airline"]

    memory_store.update_user_memory(state["user_id"], preferences)
    memory_save_logger.info(f"[{state['trace_id']}] Updated memory for user: {state['user_id']}")
    
    return state

mcp_client = MCPClient()

planner = PlannerAgent(mcp_client)
executor = ExecutorAgent(mcp_client)
critic = CriticAgent()

planner_logger = get_logger("planner")

async def planner_node(state):
    planner_logger.info(f"[{state['trace_id']}] Planning for query: {state['user_query']}")
    plan = await planner.plan(state["user_query"], state["memory"], trace_id=state["trace_id"])
    planner_logger.info(f"[{state['trace_id']}] Generated plan: {plan}")
    return {**state, "plan": plan}

executor_logger = get_logger("executor")

async def executor_node(state):
    executor_logger.info(f"[{state['trace_id']}] Executing plan with {len(state['plan'])} steps")
    start = time.time()
    results = await executor.execute(state["plan"], trace_id=state["trace_id"])
    duration = round(time.time() - start, 3)
    executor_logger.info(f"[{state['trace_id']}] Execution completed in {duration}s")
    executor_logger.info(f"[{state['trace_id']}] Execution results: {results}")
    return {**state, "results": results}

critic_logger = get_logger("critic")

def critic_node(state):
    critic_logger.info(f"[{state['trace_id']}] Evaluating results")
    feedback = critic.review(state["user_query"], state["results"])
    critic_logger.info(f"[{state['trace_id']}] Critic feedback: {feedback}")
    return {
        **state,
        "feedback": feedback,
        "attempts": state["attempts"] + 1
    }
