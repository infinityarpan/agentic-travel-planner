# orchestrator/graph.py

from langgraph.graph import StateGraph, END
from state import TravelState
from nodes import memory_load_node, memory_save_node, planner_node, executor_node, critic_node
from router import route_after_critic

# orchestrator/graph.py

def build_graph():

    builder = StateGraph(TravelState)

    # Nodes
    builder.add_node("memory_load", memory_load_node)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("critic", critic_node)
    builder.add_node("memory_save", memory_save_node)

    # Flow
    builder.set_entry_point("memory_load")

    builder.add_edge("memory_load", "planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", "critic")

    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "planner": "planner",
            "end": "memory_save"
        }
    )

    builder.add_edge("memory_save", END)

    return builder.compile()