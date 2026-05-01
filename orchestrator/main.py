# orchestrator/main.py

import uuid
import asyncio
from graph import build_graph

async def run():

    graph = build_graph()

    initial_state = {
        "user_query": "Plan Goa trip under 20000 in a nice weather",
        "user_id": "user_1",
        "plan": [],
        "results": [],
        "feedback": {},
        "attempts": 0,
        "memory": {},
        "trace_id": str(uuid.uuid4())
    }

    result = await graph.ainvoke(initial_state)

    print("\n✅ Final Output:\n", result)


if __name__ == "__main__":
    asyncio.run(run())