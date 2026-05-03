def build_route_after_critic(max_attempts: int):
    def route_after_critic(state):
        if state["feedback"]["status"] == "good":
            return "end"
        if state["attempts"] >= max_attempts:
            return "end"
        return "planner"

    return route_after_critic
