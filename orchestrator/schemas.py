from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


class ToolDescriptor(BaseModel):
    name: str
    endpoint: str


class PlanStep(BaseModel):
    tool: str
    input: dict[str, Any] = Field(default_factory=dict)


class CriticFeedback(BaseModel):
    status: Literal["good", "bad"]
    reason: str = ""


class TravelPlanRequest(BaseModel):
    user_query: str = Field(min_length=3)
    user_id: str = Field(default="user_1", min_length=1)

    @field_validator("user_query", "user_id")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class TravelPlanResponse(BaseModel):
    run_id: int
    user_query: str
    user_id: str
    plan: list[PlanStep]
    results: list[dict[str, Any]]
    feedback: CriticFeedback
    attempts: int
    memory_used: dict[str, Any] = Field(default_factory=dict)
    memory_updated: dict[str, Any] = Field(default_factory=dict)
    status: str


class PlannerRunRecord(BaseModel):
    run_id: int
    user_id: str
    user_query: str
    status: str
    attempts: int
    plan: list[PlanStep] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    feedback: dict[str, Any] = Field(default_factory=dict)
    memory_before: dict[str, Any] = Field(default_factory=dict)
    memory_after: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: str
    updated_at: str


class PlannerRunListResponse(BaseModel):
    runs: list[PlannerRunRecord]


class UserMemoryResponse(BaseModel):
    user_id: str
    memory: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str | None = None
    tool_name: str | None = None


class FlightSearchRequest(BaseModel):
    from_: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    airline: str | None = None
    budget: int | None = Field(default=None, ge=0)


class HotelSearchRequest(BaseModel):
    location: str = Field(min_length=1)
    budget: int | None = Field(default=None, ge=0)
    check_in: str | None = None
    check_out: str | None = None


class WeatherRequest(BaseModel):
    location: str = Field(min_length=1)


class FlightOption(BaseModel):
    airline: str
    price: int = Field(ge=0)


class FlightsResponse(BaseModel):
    flights: list[FlightOption]


class HotelOption(BaseModel):
    name: str
    price: int = Field(ge=0)


class HotelsResponse(BaseModel):
    hotels: list[HotelOption]


class WeatherResponse(BaseModel):
    weather: str


class ToolRegistryResponse(BaseModel):
    tools: list[ToolDescriptor]


def extract_json(text: str) -> str:
    payload = text.strip()
    if payload.startswith("```"):
        lines = payload.splitlines()
        if len(lines) >= 3:
            payload = "\n".join(lines[1:-1]).strip()
    return payload


def parse_plan_steps(text: str) -> list[PlanStep]:
    payload = json.loads(extract_json(text))
    if not isinstance(payload, list):
        raise ValueError("Planner response must be a JSON array.")
    return [PlanStep.model_validate(item) for item in payload]


def parse_critic_feedback(text: str) -> CriticFeedback:
    payload = json.loads(extract_json(text))
    return CriticFeedback.model_validate(payload)


def validation_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return exc.json()
    return str(exc)
