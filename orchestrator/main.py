# orchestrator/main.py

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.telemetry import configure_tracing, get_tracer
from graph import build_graph


async def run():
    configure_tracing("travel-orchestrator")
    tracer = get_tracer("travel-orchestrator.main")
    graph = build_graph()

    initial_state = {
        "user_query": "Plan Goa trip under 20000 in a nice weather",
        "user_id": "user_1",
        "plan": [],
        "results": [],
        "feedback": {},
        "attempts": 0,
        "memory": {},
    }

    with tracer.start_as_current_span("travel_planner.run") as span:
        span.set_attribute("user.id", initial_state["user_id"])
        span.set_attribute("travel.user_query", initial_state["user_query"])
        result = await graph.ainvoke(initial_state)
        span.set_attribute("travel.plan_step_count", len(result.get("plan", [])))
        span.set_attribute("travel.attempts", result.get("attempts", 0))

    print("\nFinal Output:\n", result)


if __name__ == "__main__":
    asyncio.run(run())
