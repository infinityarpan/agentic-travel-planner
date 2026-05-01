# orchestrator/router.py

def route_after_critic(state):
    if state["feedback"]["status"] == "good":
        return "end"
    if state["attempts"] >= 3:
        return "end"
    return "planner"