import asyncio
from typing import Any

from orchestrator.agents import TripBriefAgent
from orchestrator.config import Settings
from orchestrator.errors import ResourceNotFoundError
from orchestrator.itinerary_builder import ItineraryBuilder
from orchestrator.logger import get_logger
from orchestrator.mcp_client import MCPClient
from orchestrator.memory import Memory
from orchestrator.package_builder import TripPackageBuilder
from orchestrator.schemas import (
    ActivitySearchRequest,
    FlightSearchRequest,
    FoodSearchRequest,
    HotelSearchRequest,
    PackageSelectionRequest,
    SelectedPackageResponse,
    ServiceTraceEntry,
    TravelPlanRequest,
    TravelPlanResponse,
    TravelRunListResponse,
    TravelRunRecord,
    TripBrief,
    TripPackage,
    UserMemoryResponse,
    WeatherSearchRequest,
    LocalTransportSearchRequest,
)

logger = get_logger("travel_planner_service")


class TravelPlannerService:
    def __init__(self, settings: Settings):
        settings.validate()
        self.settings = settings
        self.memory_store = Memory(settings.database_path)
        self.mcp_client = MCPClient(settings)
        self.interpreter = TripBriefAgent(settings)
        self.package_builder = TripPackageBuilder()
        self.itinerary_builder = ItineraryBuilder()

    def get_run(self, run_id: int) -> TravelRunRecord:
        return TravelRunRecord.model_validate(self.memory_store.get_run(run_id))

    def list_runs(self, *, user_id: str | None = None, limit: int = 20) -> TravelRunListResponse:
        limit = max(1, min(limit, 100))
        runs = [TravelRunRecord.model_validate(run) for run in self.memory_store.list_runs(user_id=user_id, limit=limit)]
        return TravelRunListResponse(runs=runs)

    def get_user_memory(self, user_id: str) -> UserMemoryResponse:
        return UserMemoryResponse(user_id=user_id, memory=self.memory_store.get_user_memory(user_id))

    async def plan_trip(self, request: TravelPlanRequest) -> TravelPlanResponse:
        memory_before = self.memory_store.get_user_memory(request.user_id)
        run_id = self.memory_store.create_run(request.user_id, request.user_query, memory_before)
        try:
            logger.info(f"Starting travel planning run {run_id} for user {request.user_id}")
            trip_brief = await self.interpreter.interpret(
                request.user_query,
                memory_before,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            trip_brief = self._normalize_trip_brief(trip_brief, request)
            service_requests = self._build_service_requests(trip_brief)
            service_results = await self._execute_services(service_requests)
            assembly = self.package_builder.build(trip_brief, service_results)
            memory_after = self.memory_store.update_user_memory(
                request.user_id,
                self._learn_preferences(trip_brief, assembly.recommended_package),
            )
            service_trace = [
                ServiceTraceEntry(service=name, request=payload, response=service_results[name])
                for name, payload in service_requests.items()
            ]
            self.memory_store.complete_run(
                run_id,
                status="ready",
                trip_brief=trip_brief.model_dump(mode="json"),
                trip_packages=[package.model_dump(mode="json") for package in assembly.packages],
                recommended_package=assembly.recommended_package.model_dump(mode="json"),
                cost_breakdown=assembly.recommended_package.cost_breakdown.model_dump(mode="json"),
                assumptions=assembly.assumptions,
                service_trace=[entry.model_dump(mode="json") for entry in service_trace],
                memory_after=memory_after,
            )
            logger.info(f"Completed travel planning run {run_id} for destination {trip_brief.destination}")
            return TravelPlanResponse(
                run_id=run_id,
                user_query=request.user_query,
                user_id=request.user_id,
                status="ready",
                trip_brief=trip_brief,
                trip_packages=assembly.packages,
                recommended_package=assembly.recommended_package,
                cost_breakdown=assembly.recommended_package.cost_breakdown,
                assumptions=assembly.assumptions,
                service_trace=service_trace,
                selected_package_id=None,
                itinerary=[],
                schedule_assumptions=[],
                schedule_warnings=[],
                memory_used=memory_before,
                memory_updated=memory_after,
            )
        except Exception as exc:
            self.memory_store.fail_run(run_id, error_message=str(exc))
            raise

    async def select_package(self, run_id: int, request: PackageSelectionRequest) -> SelectedPackageResponse:
        run = self.get_run(run_id)
        if not run.trip_brief:
            raise ValueError(f"Travel run '{run_id}' is missing trip brief data.")
        selected_package = next((pkg for pkg in run.trip_packages if pkg.package_id == request.package_id), None)
        if selected_package is None:
            raise ResourceNotFoundError(f"Package '{request.package_id}' was not found for run '{run_id}'.")

        itinerary_result = self.itinerary_builder.build(run.trip_brief, selected_package, run.service_trace)
        memory_after = self.memory_store.update_user_memory(
            run.user_id,
            {
                "last_selected_destination": run.trip_brief.destination,
                "last_selected_package_id": request.package_id,
            },
        )
        self.memory_store.select_package(
            run_id,
            status="itinerary_ready",
            selected_package_id=request.package_id,
            itinerary=[day.model_dump(mode="json") for day in itinerary_result.itinerary],
            schedule_assumptions=itinerary_result.schedule_assumptions,
            schedule_warnings=itinerary_result.schedule_warnings,
            memory_after=memory_after,
        )
        return SelectedPackageResponse(
            run_id=run_id,
            user_id=run.user_id,
            status="itinerary_ready",
            selected_package_id=request.package_id,
            trip_brief=run.trip_brief,
            selected_package=selected_package,
            itinerary=itinerary_result.itinerary,
            schedule_assumptions=itinerary_result.schedule_assumptions,
            schedule_warnings=itinerary_result.schedule_warnings,
            memory_updated=memory_after,
        )

    def _normalize_trip_brief(self, trip_brief: TripBrief, request: TravelPlanRequest) -> TripBrief:
        if request.start_date and request.end_date:
            assumptions = list(trip_brief.assumptions)
            if trip_brief.start_date != request.start_date or trip_brief.end_date != request.end_date:
                assumptions.append("Applied explicit API dates over interpreted timing.")
            return trip_brief.model_copy(
                update={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "duration_nights": (request.end_date - request.start_date).days,
                    "travel_month": request.start_date.month,
                    "assumptions": assumptions,
                }
            )
        return trip_brief

    def _build_service_requests(self, trip_brief: TripBrief) -> dict[str, dict[str, Any]]:
        return {
            "flight_search": FlightSearchRequest(
                origin=trip_brief.origin,
                destination=trip_brief.destination,
                duration_nights=trip_brief.duration_nights,
                traveler_count=trip_brief.traveler_count,
                total_budget=trip_brief.total_budget,
                trip_style=trip_brief.trip_style,
                travel_month=trip_brief.travel_month,
                constraints=trip_brief.constraints,
                arrival_time_preference=trip_brief.arrival_time_preference,
                departure_time_preference=trip_brief.departure_time_preference,
            ).model_dump(mode="json"),
            "hotel_search": HotelSearchRequest(
                destination=trip_brief.destination,
                duration_nights=trip_brief.duration_nights,
                traveler_count=trip_brief.traveler_count,
                total_budget=trip_brief.total_budget,
                trip_style=trip_brief.trip_style,
                travel_month=trip_brief.travel_month,
            ).model_dump(mode="json"),
            "activity_search": ActivitySearchRequest(
                destination=trip_brief.destination,
                duration_nights=trip_brief.duration_nights,
                traveler_count=trip_brief.traveler_count,
                trip_style=trip_brief.trip_style,
                interests=trip_brief.interests,
                travel_month=trip_brief.travel_month,
            ).model_dump(mode="json"),
            "local_transport_search": LocalTransportSearchRequest(
                destination=trip_brief.destination,
                duration_nights=trip_brief.duration_nights,
                traveler_count=trip_brief.traveler_count,
                trip_style=trip_brief.trip_style,
            ).model_dump(mode="json"),
            "food_search": FoodSearchRequest(
                destination=trip_brief.destination,
                traveler_count=trip_brief.traveler_count,
                total_budget=trip_brief.total_budget,
                trip_style=trip_brief.trip_style,
                food_preferences=trip_brief.food_preferences,
            ).model_dump(mode="json"),
            "weather_search": WeatherSearchRequest(
                destination=trip_brief.destination,
                travel_month=trip_brief.travel_month,
            ).model_dump(mode="json"),
        }

    async def _execute_services(self, service_requests: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        available_tools = {tool.name for tool in await self.mcp_client.list_tools()}
        missing = [service for service in service_requests if service not in available_tools]
        if missing:
            raise ValueError(f"Missing required services: {', '.join(sorted(missing))}.")

        async def invoke(service_name: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
            result = await self.mcp_client.call_tool(service_name, payload)
            return service_name, result

        pairs = await asyncio.gather(
            *(invoke(service_name, payload) for service_name, payload in service_requests.items())
        )
        return dict(pairs)

    def _learn_preferences(self, trip_brief: TripBrief, recommended_package: TripPackage) -> dict[str, Any]:
        hotel = recommended_package.hotel
        flight = recommended_package.flight
        food = recommended_package.food_recommendations[0] if recommended_package.food_recommendations else None
        return {
            "home_city": trip_brief.origin,
            "preferred_airline_tier": flight.tier,
            "hotel_comfort_level": hotel.comfort_level,
            "activity_style": trip_brief.trip_style,
            "food_style": food.cuisine if food else trip_brief.trip_style,
            "budget_band": self._budget_band(trip_brief.total_budget),
            "trip_pace": "slow" if trip_brief.duration_nights >= 5 else "compact",
        }

    def _budget_band(self, total_budget: int) -> str:
        if total_budget < 25000:
            return "value"
        if total_budget < 50000:
            return "mid"
        return "premium"
