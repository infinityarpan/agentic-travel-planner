# orchestrator/main.py

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import time

from common.telemetry import configure_tracing, get_meter, get_tracer, metric_attributes
from graph import build_graph

meter = get_meter("travel-orchestrator.main")
graph_run_counter = meter.create_counter(
    "travel.graph.runs",
    description="Number of graph runs.",
)
graph_run_duration = meter.create_histogram(
    "travel.graph.run.duration",
    unit="s",
    description="Duration of graph runs in seconds.",
)


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

    start = time.time()
    with tracer.start_as_current_span("travel_planner.run") as span:
        span.set_attribute("user.id", initial_state["user_id"])
        span.set_attribute("travel.user_query", initial_state["user_query"])
        result = await graph.ainvoke(initial_state)
        span.set_attribute("travel.plan_step_count", len(result.get("plan", [])))
        span.set_attribute("travel.attempts", result.get("attempts", 0))
        attributes = metric_attributes(run_type="travel_planner")
        graph_run_counter.add(1, attributes)
        graph_run_duration.record(time.time() - start, attributes)

    print("\nFinal Output:\n", result)


if __name__ == "__main__":
    asyncio.run(run())
