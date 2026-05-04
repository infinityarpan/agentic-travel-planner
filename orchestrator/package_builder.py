from __future__ import annotations

from dataclasses import dataclass

from orchestrator.schemas import (
    ActivitiesResponse,
    FlightOffer,
    FlightsResponse,
    FoodRecommendation,
    FoodResponse,
    HotelOffer,
    HotelsResponse,
    LocalTransportOption,
    LocalTransportResponse,
    PackageCostBreakdown,
    TripBrief,
    TripPackage,
    WeatherResponse,
)


@dataclass
class PackageAssemblyResult:
    packages: list[TripPackage]
    recommended_package: TripPackage
    assumptions: list[str]


class TripPackageBuilder:
    def build(self, trip_brief: TripBrief, service_results: dict[str, dict]) -> PackageAssemblyResult:
        flights = FlightsResponse.model_validate(service_results["flight_search"]).offers
        hotels = HotelsResponse.model_validate(service_results["hotel_search"]).offers
        activities = ActivitiesResponse.model_validate(service_results["activity_search"]).items
        local_transport = LocalTransportResponse.model_validate(service_results["local_transport_search"]).options
        food = FoodResponse.model_validate(service_results["food_search"]).items
        weather = WeatherResponse.model_validate(service_results["weather_search"]).summary

        available_flights = [offer for offer in flights if offer.seats_left >= trip_brief.traveler_count]
        available_hotels = [offer for offer in hotels if offer.max_occupancy >= trip_brief.traveler_count]
        if not available_flights:
            raise ValueError(f"No flight offers available for {trip_brief.destination}.")
        if not available_hotels:
            raise ValueError(f"No hotel offers available for {trip_brief.destination}.")
        if not local_transport:
            raise ValueError(f"No local transport options available for {trip_brief.destination}.")

        candidate_flights = sorted(available_flights, key=lambda offer: offer.total_price)[:3]
        candidate_hotels = sorted(
            available_hotels,
            key=lambda offer: (self._hotel_preference_penalty(trip_brief, offer), offer.total_price),
        )[:3]
        ranked_transport = sorted(
            local_transport,
            key=lambda option: (-option.convenience_score, option.total_price),
        )

        packages: list[TripPackage] = []
        softened_budget_found = False
        for flight in candidate_flights:
            for hotel in candidate_hotels:
                chosen_transport = self._choose_transport(ranked_transport, trip_brief, hotel)
                chosen_activities = self._choose_activities(activities, trip_brief)
                chosen_food = self._choose_food(food, trip_brief)
                cost_breakdown = self._build_cost_breakdown(
                    trip_brief=trip_brief,
                    flight=flight,
                    hotel=hotel,
                    activities=chosen_activities,
                    local_transport=chosen_transport,
                    food=chosen_food,
                )
                within_budget = cost_breakdown.grand_total <= trip_brief.total_budget
                near_budget = cost_breakdown.grand_total <= int(trip_brief.total_budget * 1.15)
                if not within_budget and not near_budget:
                    continue
                if not within_budget and near_budget:
                    softened_budget_found = True
                score = self._score_package(trip_brief, flight, hotel, chosen_activities, chosen_transport, cost_breakdown)
                assumptions = []
                if not within_budget:
                    assumptions.append("Package is slightly above the stated budget but still the closest realistic fit.")
                packages.append(
                    TripPackage(
                        package_id=f"{trip_brief.destination.lower().replace(' ', '-')}-{flight.id}-{hotel.id}",
                        title=self._package_title(trip_brief, hotel),
                        summary=self._package_summary(trip_brief, flight, hotel, weather),
                        flight=flight,
                        hotel=hotel,
                        activities=chosen_activities,
                        local_transport=chosen_transport,
                        food_recommendations=chosen_food,
                        weather=weather,
                        cost_breakdown=cost_breakdown,
                        score=round(score, 2),
                        package_tags=[trip_brief.trip_style, weather.season_tag, hotel.comfort_level],
                        assumptions=assumptions,
                    )
                )

        if not packages:
            raise ValueError(
                f"No viable trip packages found for {trip_brief.destination} within a realistic budget range."
            )

        packages.sort(key=lambda package: (-package.score, package.cost_breakdown.grand_total))
        top_packages = packages[:3]
        assumptions = list(trip_brief.assumptions)
        if softened_budget_found and all(package.cost_breakdown.grand_total > trip_brief.total_budget for package in top_packages):
            assumptions.append("No package fit fully within budget, so near-budget options are shown.")
        return PackageAssemblyResult(
            packages=top_packages,
            recommended_package=top_packages[0],
            assumptions=assumptions + top_packages[0].assumptions,
        )

    def _choose_transport(
        self,
        options: list[LocalTransportOption],
        trip_brief: TripBrief,
        hotel: HotelOffer,
    ) -> LocalTransportOption:
        preferred = sorted(
            options,
            key=lambda option: (
                not self._matches_trip_style(option, trip_brief.trip_style),
                -option.convenience_score,
                option.total_price,
            ),
        )
        return preferred[0]

    def _choose_activities(self, options, trip_brief: TripBrief):
        ranked = sorted(
            options,
            key=lambda option: (
                -self._activity_match_score(option, trip_brief),
                option.price_total,
            ),
        )
        activity_budget = max(2500, int(trip_brief.total_budget * 0.12))
        chosen = []
        running_total = 0
        for option in ranked:
            if len(chosen) >= min(3, trip_brief.duration_nights):
                break
            if running_total + option.price_total > activity_budget and chosen:
                continue
            chosen.append(option)
            running_total += option.price_total
        return chosen

    def _choose_food(self, options: list[FoodRecommendation], trip_brief: TripBrief) -> list[FoodRecommendation]:
        ranked = sorted(
            options,
            key=lambda option: (
                not any(pref.lower() in option.cuisine.lower() for pref in trip_brief.food_preferences),
                option.estimated_cost_per_person,
            ),
        )
        return ranked[:2]

    def _build_cost_breakdown(
        self,
        *,
        trip_brief: TripBrief,
        flight: FlightOffer,
        hotel: HotelOffer,
        activities,
        local_transport: LocalTransportOption,
        food: list[FoodRecommendation],
    ) -> PackageCostBreakdown:
        flight_total = flight.total_price
        stay_total = hotel.total_price
        activities_total = sum(activity.price_total for activity in activities)
        local_transport_total = local_transport.total_price
        meal_count = min(2, max(1, trip_brief.duration_nights))
        food_total = sum(item.estimated_cost_per_person for item in food) * trip_brief.traveler_count * meal_count
        subtotal = flight_total + stay_total + activities_total + local_transport_total + food_total
        contingency_total = max(1500, int(subtotal * 0.08))
        grand_total = subtotal + contingency_total
        return PackageCostBreakdown(
            flight_total=flight_total,
            stay_total=stay_total,
            activities_total=activities_total,
            local_transport_total=local_transport_total,
            food_total=food_total,
            contingency_total=contingency_total,
            grand_total=grand_total,
        )

    def _score_package(
        self,
        trip_brief: TripBrief,
        flight: FlightOffer,
        hotel: HotelOffer,
        activities,
        local_transport: LocalTransportOption,
        cost_breakdown: PackageCostBreakdown,
    ) -> float:
        budget_fit = max(0.0, 40.0 - abs(trip_brief.total_budget - cost_breakdown.grand_total) / 1000)
        hotel_score = hotel.star_rating * 6
        activity_score = sum(self._activity_match_score(activity, trip_brief) for activity in activities)
        transport_score = local_transport.convenience_score * 2
        comfort_bonus = 4 if hotel.comfort_level == "comfort" else 2 if hotel.comfort_level == "premium" else 1
        flight_bonus = 4 if flight.tier == "flex" else 2 if flight.tier == "premium" else 1
        return budget_fit + hotel_score + activity_score + transport_score + comfort_bonus + flight_bonus

    def _activity_match_score(self, activity, trip_brief: TripBrief) -> int:
        score = 1
        if trip_brief.trip_style in activity.recommended_for:
            score += 4
        if any(interest.lower() in activity.category.lower() or interest.lower() in activity.name.lower() for interest in trip_brief.interests):
            score += 3
        if trip_brief.trip_style == "family" and activity.family_friendly:
            score += 2
        return score

    def _matches_trip_style(self, option: LocalTransportOption, trip_style: str) -> bool:
        style_map = {
            "relaxed": {"private cab", "rental scooter"},
            "adventure": {"rental bike", "self-drive car"},
            "family": {"private cab", "self-drive car"},
            "cultural": {"city cab pass", "metro and cab mix"},
            "foodie": {"city cab pass", "private cab"},
            "romantic": {"private cab", "self-drive car"},
        }
        return option.mode.lower() in style_map.get(trip_style, set())

    def _hotel_preference_penalty(self, trip_brief: TripBrief, hotel: HotelOffer) -> int:
        preferred = str(trip_brief.trip_style)
        if preferred in {"romantic", "foodie"} and hotel.comfort_level == "premium":
            return 0
        if preferred == "family" and hotel.comfort_level == "comfort":
            return 0
        if preferred == "adventure" and hotel.comfort_level == "economy":
            return 0
        return 1

    def _package_title(self, trip_brief: TripBrief, hotel: HotelOffer) -> str:
        return f"{trip_brief.destination} {trip_brief.trip_style.title()} Package - {hotel.comfort_level.title()} Stay"

    def _package_summary(self, trip_brief: TripBrief, flight: FlightOffer, hotel: HotelOffer, weather) -> str:
        return (
            f"{trip_brief.duration_nights}-night {trip_brief.trip_style} trip to {trip_brief.destination} "
            f"with {flight.airline} {flight.tier} airfare, a {hotel.star_rating}-star stay in {hotel.area}, "
            f"and {weather.expected_condition.lower()} weather."
        )
