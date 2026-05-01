# orchestrator/state.py

from typing import TypedDict, List, Dict

class TravelState(TypedDict):
    user_query: str
    user_id: str
    trace_id: str
    plan: List[Dict]
    results: List[Dict]
    feedback: Dict
    attempts: int
    memory: Dict
