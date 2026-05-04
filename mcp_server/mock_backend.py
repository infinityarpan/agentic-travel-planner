from __future__ import annotations

from datetime import datetime

from orchestrator.schemas import (
    ActivitySearchRequest,
    ActivitiesResponse,
    FlightSearchRequest,
    FlightsResponse,
    FoodResponse,
    FoodSearchRequest,
    HotelSearchRequest,
    HotelsResponse,
    LocalTransportResponse,
    LocalTransportSearchRequest,
    WeatherResponse,
    WeatherSearchRequest,
)


DESTINATIONS = {
    "goa": {
        "display": "Goa",
        "kind": "beach",
        "peak_months": {11, 12, 1, 2},
        "weather": {"peak": ("Sunny", 30), "regular": ("Humid", 29), "monsoon": ("Rainy", 27)},
        "hotels": [
            {"name": "Palm Cove Residency", "comfort_level": "economy", "nightly_rate": 2800, "star_rating": 3.4, "area": "Calangute", "max_occupancy": 2, "amenities": ["wifi", "breakfast"]},
            {"name": "Harbor Breeze Suites", "comfort_level": "comfort", "nightly_rate": 4200, "star_rating": 4.1, "area": "Candolim", "max_occupancy": 3, "amenities": ["pool", "breakfast", "beach shuttle"]},
            {"name": "Azure Dunes Retreat", "comfort_level": "premium", "nightly_rate": 6800, "star_rating": 4.6, "area": "Morjim", "max_occupancy": 4, "amenities": ["pool", "spa", "beach access"]},
        ],
        "activities": [
            {"name": "Sunset Cruise", "category": "leisure", "duration_hours": 2.5, "price_total": 2400, "indoor": False, "family_friendly": True, "recommended_for": ["relaxed", "romantic"]},
            {"name": "Water Sports Combo", "category": "adventure", "duration_hours": 4.0, "price_total": 4200, "indoor": False, "family_friendly": False, "recommended_for": ["adventure"]},
            {"name": "Old Goa Heritage Walk", "category": "culture", "duration_hours": 3.0, "price_total": 1800, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "family"]},
            {"name": "Beach Shack Evening", "category": "food", "duration_hours": 2.0, "price_total": 1500, "indoor": False, "family_friendly": True, "recommended_for": ["foodie", "relaxed"]},
        ],
        "transport": [
            {"mode": "rental scooter", "total_price": 1800, "convenience_score": 7.2, "coverage": "Best for beaches and casual town hopping"},
            {"mode": "private cab", "total_price": 3800, "convenience_score": 9.1, "coverage": "Door-to-door comfort with airport and sightseeing coverage"},
            {"mode": "self-drive car", "total_price": 4600, "convenience_score": 8.5, "coverage": "Ideal for groups exploring North and South Goa"},
        ],
        "food": [
            {"name": "Fisherman's Wharf Dinner", "cuisine": "Goan seafood", "meal_type": "dinner", "price_band": "premium", "estimated_cost_per_person": 1400, "neighborhood": "Cavelossim"},
            {"name": "Beach Shack Thali", "cuisine": "coastal Indian", "meal_type": "lunch", "price_band": "budget", "estimated_cost_per_person": 500, "neighborhood": "Baga"},
            {"name": "Cafe Brunch by the Sea", "cuisine": "continental", "meal_type": "brunch", "price_band": "mid", "estimated_cost_per_person": 850, "neighborhood": "Anjuna"},
        ],
        "flight_bases": {"Kolkata": 6400, "Delhi": 5900, "Mumbai": 4200, "Bengaluru": 5200},
        "flight_duration": {"Kolkata": 2.9, "Delhi": 2.7, "Mumbai": 1.3, "Bengaluru": 1.5},
    },
    "jaipur": {
        "display": "Jaipur",
        "kind": "heritage",
        "peak_months": {10, 11, 12, 1, 2, 3},
        "weather": {"peak": ("Pleasant", 24), "regular": ("Warm", 31), "monsoon": ("Cloudy", 29)},
        "hotels": [
            {"name": "Pink City Lodge", "comfort_level": "economy", "nightly_rate": 2300, "star_rating": 3.5, "area": "MI Road", "max_occupancy": 2, "amenities": ["wifi", "breakfast"]},
            {"name": "Amber Courtyard Hotel", "comfort_level": "comfort", "nightly_rate": 3900, "star_rating": 4.2, "area": "Bani Park", "max_occupancy": 3, "amenities": ["pool", "breakfast"]},
            {"name": "Royal Haveli Palace", "comfort_level": "premium", "nightly_rate": 6100, "star_rating": 4.7, "area": "Civil Lines", "max_occupancy": 4, "amenities": ["spa", "courtyard dining", "pool"]},
        ],
        "activities": [
            {"name": "Amber Fort Guided Tour", "category": "culture", "duration_hours": 3.5, "price_total": 2200, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "family"]},
            {"name": "City Palace and Bazaar Trail", "category": "shopping", "duration_hours": 4.0, "price_total": 1900, "indoor": False, "family_friendly": True, "recommended_for": ["foodie", "cultural"]},
            {"name": "Rajasthani Folk Evening", "category": "performance", "duration_hours": 2.5, "price_total": 2600, "indoor": True, "family_friendly": True, "recommended_for": ["relaxed", "family", "romantic"]},
            {"name": "Hot Air Balloon Sunrise", "category": "adventure", "duration_hours": 3.0, "price_total": 6200, "indoor": False, "family_friendly": False, "recommended_for": ["adventure", "romantic"]},
        ],
        "transport": [
            {"mode": "city cab pass", "total_price": 2600, "convenience_score": 8.8, "coverage": "Best for forts, markets, and hotel transfers"},
            {"mode": "self-drive car", "total_price": 4200, "convenience_score": 7.9, "coverage": "Useful for day trips around Jaipur"},
            {"mode": "private cab", "total_price": 3600, "convenience_score": 9.0, "coverage": "Comfort-focused city movement"},
        ],
        "food": [
            {"name": "Traditional Thali Dinner", "cuisine": "Rajasthani", "meal_type": "dinner", "price_band": "mid", "estimated_cost_per_person": 900, "neighborhood": "C Scheme"},
            {"name": "Street Chaat Crawl", "cuisine": "street food", "meal_type": "evening snacks", "price_band": "budget", "estimated_cost_per_person": 350, "neighborhood": "Johari Bazaar"},
            {"name": "Haveli Rooftop Lunch", "cuisine": "North Indian", "meal_type": "lunch", "price_band": "premium", "estimated_cost_per_person": 1200, "neighborhood": "Old City"},
        ],
        "flight_bases": {"Kolkata": 5200, "Delhi": 3200, "Mumbai": 4700, "Bengaluru": 6100},
        "flight_duration": {"Kolkata": 2.1, "Delhi": 1.0, "Mumbai": 1.8, "Bengaluru": 2.5},
    },
    "manali": {
        "display": "Manali",
        "kind": "mountain",
        "peak_months": {4, 5, 6, 10, 11, 12},
        "weather": {"peak": ("Cool", 16), "regular": ("Mild", 12), "monsoon": ("Wet", 10)},
        "hotels": [
            {"name": "Pine Trails Inn", "comfort_level": "economy", "nightly_rate": 2500, "star_rating": 3.6, "area": "Old Manali", "max_occupancy": 2, "amenities": ["wifi", "heater"]},
            {"name": "Valley View Chalet", "comfort_level": "comfort", "nightly_rate": 4100, "star_rating": 4.2, "area": "Log Huts", "max_occupancy": 3, "amenities": ["heater", "mountain view", "breakfast"]},
            {"name": "Snowcrest Spa Resort", "comfort_level": "premium", "nightly_rate": 6700, "star_rating": 4.7, "area": "Prini", "max_occupancy": 4, "amenities": ["spa", "heater", "mountain view"]},
        ],
        "activities": [
            {"name": "Solang Adventure Day", "category": "adventure", "duration_hours": 5.0, "price_total": 4800, "indoor": False, "family_friendly": False, "recommended_for": ["adventure"]},
            {"name": "Hadimba and Old Manali Walk", "category": "culture", "duration_hours": 3.0, "price_total": 1700, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "relaxed"]},
            {"name": "Riverside Cafe Trail", "category": "food", "duration_hours": 2.5, "price_total": 1400, "indoor": True, "family_friendly": True, "recommended_for": ["foodie", "romantic"]},
            {"name": "Snow View Couple Picnic", "category": "leisure", "duration_hours": 3.5, "price_total": 2600, "indoor": False, "family_friendly": False, "recommended_for": ["romantic", "relaxed"]},
        ],
        "transport": [
            {"mode": "private cab", "total_price": 3400, "convenience_score": 9.2, "coverage": "Reliable for hills and point-to-point sightseeing"},
            {"mode": "self-drive car", "total_price": 4100, "convenience_score": 7.8, "coverage": "Flexible but weather-sensitive"},
            {"mode": "rental bike", "total_price": 2000, "convenience_score": 6.8, "coverage": "Adventure-friendly short-distance travel"},
        ],
        "food": [
            {"name": "Tibetan Kitchen Dinner", "cuisine": "Tibetan", "meal_type": "dinner", "price_band": "mid", "estimated_cost_per_person": 700, "neighborhood": "Mall Road"},
            {"name": "Woodfire Cafe Brunch", "cuisine": "cafe", "meal_type": "brunch", "price_band": "budget", "estimated_cost_per_person": 450, "neighborhood": "Old Manali"},
            {"name": "Mountain View Grill", "cuisine": "continental", "meal_type": "dinner", "price_band": "premium", "estimated_cost_per_person": 1150, "neighborhood": "Prini"},
        ],
        "flight_bases": {"Kolkata": 7800, "Delhi": 5200, "Mumbai": 7400, "Bengaluru": 8600},
        "flight_duration": {"Kolkata": 3.3, "Delhi": 1.5, "Mumbai": 2.5, "Bengaluru": 3.7},
    },
    "darjeeling": {
        "display": "Darjeeling",
        "kind": "hill town",
        "peak_months": {3, 4, 5, 10, 11},
        "weather": {"peak": ("Crisp", 15), "regular": ("Cool", 13), "monsoon": ("Foggy", 11)},
        "hotels": [
            {"name": "Tea Garden Stay", "comfort_level": "economy", "nightly_rate": 2200, "star_rating": 3.4, "area": "Chowrasta", "max_occupancy": 2, "amenities": ["wifi", "tea service"]},
            {"name": "Cloudline Residency", "comfort_level": "comfort", "nightly_rate": 3600, "star_rating": 4.0, "area": "Gandhi Road", "max_occupancy": 3, "amenities": ["heater", "breakfast", "valley view"]},
            {"name": "Heritage Himalayan Manor", "comfort_level": "premium", "nightly_rate": 5600, "star_rating": 4.5, "area": "Observatory Hill", "max_occupancy": 4, "amenities": ["fireplace", "tea lounge", "valley view"]},
        ],
        "activities": [
            {"name": "Tiger Hill Sunrise", "category": "sightseeing", "duration_hours": 3.5, "price_total": 1800, "indoor": False, "family_friendly": True, "recommended_for": ["relaxed", "family", "romantic"]},
            {"name": "Toy Train Heritage Ride", "category": "culture", "duration_hours": 2.0, "price_total": 2100, "indoor": True, "family_friendly": True, "recommended_for": ["cultural", "family"]},
            {"name": "Tea Estate Tasting", "category": "food", "duration_hours": 2.5, "price_total": 1600, "indoor": False, "family_friendly": True, "recommended_for": ["foodie", "relaxed"]},
            {"name": "Monastery and Market Walk", "category": "culture", "duration_hours": 3.0, "price_total": 1500, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "foodie"]},
        ],
        "transport": [
            {"mode": "private cab", "total_price": 3200, "convenience_score": 8.9, "coverage": "Best for steep roads and early morning departures"},
            {"mode": "city cab pass", "total_price": 2400, "convenience_score": 7.7, "coverage": "Suitable for local town transfers and viewpoints"},
            {"mode": "rental bike", "total_price": 1900, "convenience_score": 6.1, "coverage": "Short scenic hops for confident riders"},
        ],
        "food": [
            {"name": "Tea Lounge High Tea", "cuisine": "tea and bakery", "meal_type": "afternoon tea", "price_band": "mid", "estimated_cost_per_person": 650, "neighborhood": "Chowrasta"},
            {"name": "Momo House Dinner", "cuisine": "Tibetan", "meal_type": "dinner", "price_band": "budget", "estimated_cost_per_person": 320, "neighborhood": "Nehru Road"},
            {"name": "Colonial Dining Room", "cuisine": "continental", "meal_type": "dinner", "price_band": "premium", "estimated_cost_per_person": 1100, "neighborhood": "Observatory Hill"},
        ],
        "flight_bases": {"Kolkata": 2800, "Delhi": 5400, "Mumbai": 6600, "Bengaluru": 6900},
        "flight_duration": {"Kolkata": 1.1, "Delhi": 2.0, "Mumbai": 2.7, "Bengaluru": 3.0},
    },
}


AIRLINES = [
    ("SkyJet", "saver", 1.0, 15),
    ("Vista Air", "flex", 1.18, 20),
    ("AeroLux", "premium", 1.42, 30),
]


def _current_month(month: int | None) -> int:
    return month or datetime.utcnow().month


def _normalize_destination(destination: str) -> tuple[str, dict]:
    key = destination.strip().lower()
    if key not in DESTINATIONS:
        raise ValueError(f"Destination '{destination}' is not supported by the travel platform mock.")
    return key, DESTINATIONS[key]


def _season_bucket(destination: dict, month: int) -> str:
    if month in destination["peak_months"]:
        return "peak"
    if month in {6, 7, 8, 9}:
        return "monsoon"
    return "regular"


def _price_multiplier(destination: dict, month: int) -> float:
    bucket = _season_bucket(destination, month)
    if bucket == "peak":
        return 1.2
    if bucket == "monsoon":
        return 0.88
    return 1.0


def search_flights(request: FlightSearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    month = _current_month(request.travel_month)
    multiplier = _price_multiplier(destination, month)
    base_price = destination["flight_bases"].get(request.origin, 7200)
    base_duration = destination["flight_duration"].get(request.origin, 2.4)
    offers = []
    for index, (airline, tier, tier_multiplier, baggage_kg) in enumerate(AIRLINES, start=1):
        total_price = int(base_price * tier_multiplier * multiplier * request.traveler_count)
        offers.append(
            {
                "id": f"{request.origin[:3].upper()}-{request.destination[:3].upper()}-F{index}",
                "airline": airline,
                "tier": tier,
                "origin": request.origin,
                "destination": destination["display"],
                "total_price": total_price,
                "duration_hours": round(base_duration + (index * 0.2), 1),
                "baggage_kg": baggage_kg,
                "seats_left": max(3, 9 - index),
                "availability_status": "limited" if index == 3 else "available",
                "explanation": f"{tier.title()} fare tuned for {destination['display']} demand in month {month}.",
            }
        )
    return FlightsResponse(offers=offers).model_dump()


def search_hotels(request: HotelSearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    month = _current_month(request.travel_month)
    multiplier = _price_multiplier(destination, month)
    offers = []
    for index, hotel in enumerate(destination["hotels"], start=1):
        nightly_rate = int(hotel["nightly_rate"] * multiplier)
        total_price = nightly_rate * request.duration_nights
        offers.append(
            {
                "id": f"{request.destination[:3].upper()}-H{index}",
                "name": hotel["name"],
                "comfort_level": hotel["comfort_level"],
                "nightly_rate": nightly_rate,
                "total_price": total_price,
                "star_rating": hotel["star_rating"],
                "area": hotel["area"],
                "max_occupancy": hotel["max_occupancy"],
                "amenities": hotel["amenities"],
                "availability_status": "limited" if hotel["comfort_level"] == "premium" else "available",
                "explanation": f"{hotel['comfort_level'].title()} stay priced for {request.duration_nights} nights in {destination['display']}.",
            }
        )
    return HotelsResponse(offers=offers).model_dump()


def search_activities(request: ActivitySearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    items = []
    for index, activity in enumerate(destination["activities"], start=1):
        items.append(
            {
                "id": f"{request.destination[:3].upper()}-A{index}",
                "name": activity["name"],
                "category": activity["category"],
                "duration_hours": activity["duration_hours"],
                "price_total": activity["price_total"],
                "indoor": activity["indoor"],
                "family_friendly": activity["family_friendly"],
                "recommended_for": activity["recommended_for"],
                "explanation": f"Good fit for {', '.join(activity['recommended_for'])} trips in {destination['display']}.",
            }
        )
    return ActivitiesResponse(items=items).model_dump()


def search_local_transport(request: LocalTransportSearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    options = []
    for index, option in enumerate(destination["transport"], start=1):
        options.append(
            {
                "id": f"{request.destination[:3].upper()}-T{index}",
                "mode": option["mode"],
                "total_price": option["total_price"],
                "convenience_score": option["convenience_score"],
                "coverage": option["coverage"],
                "explanation": f"{option['mode'].title()} is commonly chosen for {destination['display']} itineraries.",
            }
        )
    return LocalTransportResponse(options=options).model_dump()


def search_food(request: FoodSearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    items = []
    for index, item in enumerate(destination["food"], start=1):
        items.append(
            {
                "id": f"{request.destination[:3].upper()}-FD{index}",
                "name": item["name"],
                "cuisine": item["cuisine"],
                "meal_type": item["meal_type"],
                "price_band": item["price_band"],
                "estimated_cost_per_person": item["estimated_cost_per_person"],
                "neighborhood": item["neighborhood"],
                "explanation": f"{item['cuisine'].title()} option aligned to {destination['display']} demand.",
            }
        )
    return FoodResponse(items=items).model_dump()


def search_weather(request: WeatherSearchRequest) -> dict:
    _, destination = _normalize_destination(request.destination)
    month = _current_month(request.travel_month)
    bucket = _season_bucket(destination, month)
    condition, avg_temp = destination["weather"][bucket]
    advisories = {
        "peak": "Popular season with stronger demand and higher prices.",
        "regular": "Balanced season with steady availability.",
        "monsoon": "Expect weather-related variability and slower outdoor plans.",
    }
    return WeatherResponse(
        summary={
            "destination": destination["display"],
            "expected_condition": condition,
            "avg_temp_c": avg_temp,
            "season_tag": bucket,
            "trip_advisory": advisories[bucket],
        }
    ).model_dump()
