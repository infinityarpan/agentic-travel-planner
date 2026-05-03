from typing import Any, NotRequired, TypedDict


class TravelState(TypedDict):
    run_id: int
    user_query: str
    user_id: str
    plan: list[dict[str, Any]]
    results: list[dict[str, Any]]
    feedback: dict[str, Any]
    attempts: int
    memory: dict[str, Any]
    memory_after: dict[str, Any]
    status: str
    error_message: NotRequired[str]
