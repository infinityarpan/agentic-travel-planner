from langgraph.graph import END, StateGraph

from orchestrator.router import build_route_after_critic
from orchestrator.state import TravelState


def build_graph(nodes, max_attempts: int):
    builder = StateGraph(TravelState)

    builder.add_node("memory_load", nodes.memory_load_node)
    builder.add_node("planner", nodes.planner_node)
    builder.add_node("executor", nodes.executor_node)
    builder.add_node("critic", nodes.critic_node)
    builder.add_node("memory_save", nodes.memory_save_node)

    builder.set_entry_point("memory_load")
    builder.add_edge("memory_load", "planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", "critic")
    builder.add_conditional_edges(
        "critic",
        build_route_after_critic(max_attempts),
        {
            "planner": "planner",
            "end": "memory_save",
        },
    )
    builder.add_edge("memory_save", END)

    return builder.compile()
