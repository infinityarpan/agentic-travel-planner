from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


TripStyle = Literal["relaxed", "adventure", "cultural", "family", "foodie", "romantic"]
ComfortLevel = Literal["economy", "comfort", "premium"]
AvailabilityStatus = Literal["available", "limited"]


class ToolDescriptor(BaseModel):
    name: str
    endpoint: str


class TripBrief(BaseModel):
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    duration_nights: int = Field(ge=1, le=14)
    traveler_count: int = Field(ge=1, le=8)
    total_budget: int = Field(ge=5000)
    trip_style: TripStyle
    interests: list[str] = Field(default_factory=list)
    food_preferences: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    travel_month: int | None = Field(default=None, ge=1, le=12)
    assumptions: list[str] = Field(default_factory=list)


class PackageCostBreakdown(BaseModel):
    flight_total: int = Field(ge=0)
    stay_total: int = Field(ge=0)
    activities_total: int = Field(ge=0)
    local_transport_total: int = Field(ge=0)
    food_total: int = Field(ge=0)
    contingency_total: int = Field(ge=0)
    grand_total: int = Field(ge=0)


class FlightOffer(BaseModel):
    id: str
    airline: str
    tier: Literal["saver", "flex", "premium"]
    origin: str
    destination: str
    total_price: int = Field(ge=0)
    duration_hours: float = Field(gt=0)
    baggage_kg: int = Field(ge=0)
    seats_left: int = Field(ge=0)
    availability_status: AvailabilityStatus
    explanation: str


class HotelOffer(BaseModel):
    id: str
    name: str
    comfort_level: ComfortLevel
    nightly_rate: int = Field(ge=0)
    total_price: int = Field(ge=0)
    star_rating: float = Field(ge=0, le=5)
    area: str
    max_occupancy: int = Field(ge=1)
    amenities: list[str] = Field(default_factory=list)
    availability_status: AvailabilityStatus
    explanation: str


class ActivityOption(BaseModel):
    id: str
    name: str
    category: str
    duration_hours: float = Field(gt=0)
    price_total: int = Field(ge=0)
    indoor: bool
    family_friendly: bool
    recommended_for: list[str] = Field(default_factory=list)
    explanation: str


class LocalTransportOption(BaseModel):
    id: str
    mode: str
    total_price: int = Field(ge=0)
    convenience_score: float = Field(ge=0, le=10)
    coverage: str
    explanation: str


class FoodRecommendation(BaseModel):
    id: str
    name: str
    cuisine: str
    meal_type: str
    price_band: Literal["budget", "mid", "premium"]
    estimated_cost_per_person: int = Field(ge=0)
    neighborhood: str
    explanation: str


class WeatherSummary(BaseModel):
    destination: str
    expected_condition: str
    avg_temp_c: int
    season_tag: str
    trip_advisory: str


class TripPackage(BaseModel):
    package_id: str
    title: str
    summary: str
    flight: FlightOffer
    hotel: HotelOffer
    activities: list[ActivityOption] = Field(default_factory=list)
    local_transport: LocalTransportOption
    food_recommendations: list[FoodRecommendation] = Field(default_factory=list)
    weather: WeatherSummary
    cost_breakdown: PackageCostBreakdown
    score: float
    package_tags: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ServiceTraceEntry(BaseModel):
    service: str
    request: dict[str, Any]
    response: dict[str, Any]


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
    status: str
    trip_brief: TripBrief
    trip_packages: list[TripPackage] = Field(default_factory=list)
    recommended_package: TripPackage
    cost_breakdown: PackageCostBreakdown
    assumptions: list[str] = Field(default_factory=list)
    service_trace: list[ServiceTraceEntry] = Field(default_factory=list)
    memory_used: dict[str, Any] = Field(default_factory=dict)
    memory_updated: dict[str, Any] = Field(default_factory=dict)


class TravelRunRecord(BaseModel):
    run_id: int
    user_id: str
    user_query: str
    status: str
    trip_brief: TripBrief | None = None
    trip_packages: list[TripPackage] = Field(default_factory=list)
    recommended_package: TripPackage | None = None
    cost_breakdown: PackageCostBreakdown | None = None
    assumptions: list[str] = Field(default_factory=list)
    service_trace: list[ServiceTraceEntry] = Field(default_factory=list)
    memory_before: dict[str, Any] = Field(default_factory=dict)
    memory_after: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: str
    updated_at: str


class TravelRunListResponse(BaseModel):
    runs: list[TravelRunRecord]


class UserMemoryResponse(BaseModel):
    user_id: str
    memory: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str | None = None


class FlightSearchRequest(BaseModel):
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    duration_nights: int = Field(ge=1, le=14)
    traveler_count: int = Field(ge=1, le=8)
    total_budget: int = Field(ge=5000)
    trip_style: TripStyle
    travel_month: int | None = Field(default=None, ge=1, le=12)
    constraints: list[str] = Field(default_factory=list)


class FlightsResponse(BaseModel):
    offers: list[FlightOffer]


class HotelSearchRequest(BaseModel):
    destination: str = Field(min_length=2)
    duration_nights: int = Field(ge=1, le=14)
    traveler_count: int = Field(ge=1, le=8)
    total_budget: int = Field(ge=5000)
    trip_style: TripStyle
    travel_month: int | None = Field(default=None, ge=1, le=12)


class HotelsResponse(BaseModel):
    offers: list[HotelOffer]


class ActivitySearchRequest(BaseModel):
    destination: str = Field(min_length=2)
    duration_nights: int = Field(ge=1, le=14)
    traveler_count: int = Field(ge=1, le=8)
    trip_style: TripStyle
    interests: list[str] = Field(default_factory=list)
    travel_month: int | None = Field(default=None, ge=1, le=12)


class ActivitiesResponse(BaseModel):
    items: list[ActivityOption]


class LocalTransportSearchRequest(BaseModel):
    destination: str = Field(min_length=2)
    duration_nights: int = Field(ge=1, le=14)
    traveler_count: int = Field(ge=1, le=8)
    trip_style: TripStyle


class LocalTransportResponse(BaseModel):
    options: list[LocalTransportOption]


class FoodSearchRequest(BaseModel):
    destination: str = Field(min_length=2)
    traveler_count: int = Field(ge=1, le=8)
    total_budget: int = Field(ge=5000)
    trip_style: TripStyle
    food_preferences: list[str] = Field(default_factory=list)


class FoodResponse(BaseModel):
    items: list[FoodRecommendation]


class WeatherSearchRequest(BaseModel):
    destination: str = Field(min_length=2)
    travel_month: int | None = Field(default=None, ge=1, le=12)


class WeatherResponse(BaseModel):
    summary: WeatherSummary


class ToolRegistryResponse(BaseModel):
    tools: list[ToolDescriptor]


def extract_json(text: str) -> str:
    payload = text.strip()
    if payload.startswith("```"):
        lines = payload.splitlines()
        if len(lines) >= 3:
            payload = "\n".join(lines[1:-1]).strip()
    return payload


def parse_trip_brief(text: str) -> TripBrief:
    payload = json.loads(extract_json(text))
    return TripBrief.model_validate(payload)


def validation_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return exc.json()
    return str(exc)
