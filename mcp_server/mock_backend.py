from __future__ import annotations

from datetime import datetime

from orchestrator.schemas import (
    ActivitiesResponse,
    ActivitySearchRequest,
    FlightsResponse,
    FlightSearchRequest,
    FoodResponse,
    FoodSearchRequest,
    HotelsResponse,
    HotelSearchRequest,
    LocalTransportResponse,
    LocalTransportSearchRequest,
    WeatherResponse,
    WeatherSearchRequest,
)


DESTINATIONS = {
    "goa": {
        "display": "Goa",
        "peak_months": {11, 12, 1, 2},
        "weather": {"peak": ("Sunny", 30), "regular": ("Humid", 29), "monsoon": ("Rainy", 27)},
        "hotel_zone": "beach_strip",
        "day_structure": {"lunch": ("13:00", "14:15"), "dinner": ("19:00", "21:00")},
        "zones": {
            "airport": {"beach_strip": 55, "heritage_quarter": 70, "watersports_bay": 65},
            "beach_strip": {"airport": 55, "heritage_quarter": 30, "watersports_bay": 25},
            "heritage_quarter": {"airport": 70, "beach_strip": 30, "watersports_bay": 35},
            "watersports_bay": {"airport": 65, "beach_strip": 25, "heritage_quarter": 35},
        },
        "hotels": [
            {
                "name": "Palm Cove Residency",
                "comfort_level": "economy",
                "nightly_rate": 2800,
                "star_rating": 3.4,
                "area": "Calangute",
                "zone": "beach_strip",
                "max_occupancy": 2,
                "amenities": ["wifi", "breakfast"],
            },
            {
                "name": "Harbor Breeze Suites",
                "comfort_level": "comfort",
                "nightly_rate": 4200,
                "star_rating": 4.1,
                "area": "Candolim",
                "zone": "beach_strip",
                "max_occupancy": 3,
                "amenities": ["pool", "breakfast", "beach shuttle"],
            },
            {
                "name": "Azure Dunes Retreat",
                "comfort_level": "premium",
                "nightly_rate": 6800,
                "star_rating": 4.6,
                "area": "Morjim",
                "zone": "beach_strip",
                "max_occupancy": 4,
                "amenities": ["pool", "spa", "beach access"],
            },
        ],
        "activities": [
            {
                "name": "Sunrise Beach Walk",
                "category": "leisure",
                "zone": "beach_strip",
                "duration_hours": 1.5,
                "price_total": 1200,
                "indoor": False,
                "family_friendly": True,
                "recommended_for": ["relaxed", "romantic"],
                "slots": [("sunrise", "06:15", "07:45")],
            },
            {
                "name": "Water Sports Combo",
                "category": "adventure",
                "zone": "watersports_bay",
                "duration_hours": 4.0,
                "price_total": 4200,
                "indoor": False,
                "family_friendly": False,
                "recommended_for": ["adventure"],
                "slots": [("morning", "09:30", "13:30"), ("afternoon", "14:30", "18:30")],
            },
            {
                "name": "Old Goa Heritage Walk",
                "category": "culture",
                "zone": "heritage_quarter",
                "duration_hours": 3.0,
                "price_total": 1800,
                "indoor": False,
                "family_friendly": True,
                "recommended_for": ["cultural", "family"],
                "slots": [("morning", "10:00", "13:00"), ("evening", "16:00", "19:00")],
            },
            {
                "name": "Sunset Cruise",
                "category": "leisure",
                "zone": "beach_strip",
                "duration_hours": 2.5,
                "price_total": 2400,
                "indoor": False,
                "family_friendly": True,
                "recommended_for": ["relaxed", "romantic"],
                "slots": [("sunset", "17:15", "19:45")],
            },
        ],
        "transport": [
            {"mode": "rental scooter", "total_price": 1800, "convenience_score": 7.2, "coverage": "Best for beaches and casual town hopping", "transfer_buffer_minutes": 10},
            {"mode": "private cab", "total_price": 3800, "convenience_score": 9.1, "coverage": "Door-to-door comfort with airport and sightseeing coverage", "transfer_buffer_minutes": 12},
            {"mode": "self-drive car", "total_price": 4600, "convenience_score": 8.5, "coverage": "Ideal for groups exploring North and South Goa", "transfer_buffer_minutes": 15},
        ],
        "food": [
            {"name": "Cafe Brunch by the Sea", "cuisine": "continental", "meal_type": "lunch", "zone": "beach_strip", "price_band": "mid", "estimated_cost_per_person": 850, "neighborhood": "Anjuna", "meal_slots": [("lunch", "12:30", "14:00")]},
            {"name": "Beach Shack Thali", "cuisine": "coastal Indian", "meal_type": "lunch", "zone": "beach_strip", "price_band": "budget", "estimated_cost_per_person": 500, "neighborhood": "Baga", "meal_slots": [("lunch", "13:00", "14:30")]},
            {"name": "Fisherman's Wharf Dinner", "cuisine": "Goan seafood", "meal_type": "dinner", "zone": "beach_strip", "price_band": "premium", "estimated_cost_per_person": 1400, "neighborhood": "Cavelossim", "meal_slots": [("dinner", "19:30", "21:00")]},
        ],
        "flight_bases": {"Kolkata": 6400, "Delhi": 5900, "Mumbai": 4200, "Bengaluru": 5200},
        "flight_duration": {"Kolkata": 2.9, "Delhi": 2.7, "Mumbai": 1.3, "Bengaluru": 1.5},
    },
    "jaipur": {
        "display": "Jaipur",
        "peak_months": {10, 11, 12, 1, 2, 3},
        "weather": {"peak": ("Pleasant", 24), "regular": ("Warm", 31), "monsoon": ("Cloudy", 29)},
        "hotel_zone": "city_center",
        "day_structure": {"lunch": ("13:00", "14:15"), "dinner": ("19:30", "21:15")},
        "zones": {
            "airport": {"city_center": 35, "fort_belt": 50, "old_city": 40},
            "city_center": {"airport": 35, "fort_belt": 30, "old_city": 20},
            "fort_belt": {"airport": 50, "city_center": 30, "old_city": 25},
            "old_city": {"airport": 40, "city_center": 20, "fort_belt": 25},
        },
        "hotels": [
            {"name": "Pink City Lodge", "comfort_level": "economy", "nightly_rate": 2300, "star_rating": 3.5, "area": "MI Road", "zone": "city_center", "max_occupancy": 2, "amenities": ["wifi", "breakfast"]},
            {"name": "Amber Courtyard Hotel", "comfort_level": "comfort", "nightly_rate": 3900, "star_rating": 4.2, "area": "Bani Park", "zone": "city_center", "max_occupancy": 3, "amenities": ["pool", "breakfast"]},
            {"name": "Royal Haveli Palace", "comfort_level": "premium", "nightly_rate": 6100, "star_rating": 4.7, "area": "Civil Lines", "zone": "city_center", "max_occupancy": 4, "amenities": ["spa", "courtyard dining", "pool"]},
        ],
        "activities": [
            {"name": "Amber Fort Guided Tour", "category": "culture", "zone": "fort_belt", "duration_hours": 3.5, "price_total": 2200, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "family"], "slots": [("morning", "09:00", "12:30")]},
            {"name": "City Palace and Bazaar Trail", "category": "shopping", "zone": "old_city", "duration_hours": 4.0, "price_total": 1900, "indoor": False, "family_friendly": True, "recommended_for": ["foodie", "cultural"], "slots": [("afternoon", "14:30", "18:30")]},
            {"name": "Rajasthani Folk Evening", "category": "performance", "zone": "city_center", "duration_hours": 2.5, "price_total": 2600, "indoor": True, "family_friendly": True, "recommended_for": ["relaxed", "family", "romantic"], "slots": [("evening", "19:00", "21:30")]},
        ],
        "transport": [
            {"mode": "city cab pass", "total_price": 2600, "convenience_score": 8.8, "coverage": "Best for forts, markets, and hotel transfers", "transfer_buffer_minutes": 12},
            {"mode": "self-drive car", "total_price": 4200, "convenience_score": 7.9, "coverage": "Useful for day trips around Jaipur", "transfer_buffer_minutes": 15},
            {"mode": "private cab", "total_price": 3600, "convenience_score": 9.0, "coverage": "Comfort-focused city movement", "transfer_buffer_minutes": 12},
        ],
        "food": [
            {"name": "Street Chaat Crawl", "cuisine": "street food", "meal_type": "lunch", "zone": "old_city", "price_band": "budget", "estimated_cost_per_person": 350, "neighborhood": "Johari Bazaar", "meal_slots": [("lunch", "12:45", "14:00")]},
            {"name": "Traditional Thali Dinner", "cuisine": "Rajasthani", "meal_type": "dinner", "zone": "city_center", "price_band": "mid", "estimated_cost_per_person": 900, "neighborhood": "C Scheme", "meal_slots": [("dinner", "19:30", "21:00")]},
            {"name": "Haveli Rooftop Dinner", "cuisine": "North Indian", "meal_type": "dinner", "zone": "old_city", "price_band": "premium", "estimated_cost_per_person": 1200, "neighborhood": "Old City", "meal_slots": [("dinner", "20:00", "21:30")]},
        ],
        "flight_bases": {"Kolkata": 5200, "Delhi": 3200, "Mumbai": 4700, "Bengaluru": 6100},
        "flight_duration": {"Kolkata": 2.1, "Delhi": 1.0, "Mumbai": 1.8, "Bengaluru": 2.5},
    },
    "manali": {
        "display": "Manali",
        "peak_months": {4, 5, 6, 10, 11, 12},
        "weather": {"peak": ("Cool", 16), "regular": ("Mild", 12), "monsoon": ("Wet", 10)},
        "hotel_zone": "town_center",
        "day_structure": {"lunch": ("13:00", "14:00"), "dinner": ("19:00", "20:45")},
        "zones": {
            "airport": {"town_center": 110, "adventure_belt": 130, "old_manali": 120},
            "town_center": {"airport": 110, "adventure_belt": 35, "old_manali": 20},
            "adventure_belt": {"airport": 130, "town_center": 35, "old_manali": 40},
            "old_manali": {"airport": 120, "town_center": 20, "adventure_belt": 40},
        },
        "hotels": [
            {"name": "Pine Trails Inn", "comfort_level": "economy", "nightly_rate": 2500, "star_rating": 3.6, "area": "Old Manali", "zone": "old_manali", "max_occupancy": 2, "amenities": ["wifi", "heater"]},
            {"name": "Valley View Chalet", "comfort_level": "comfort", "nightly_rate": 4100, "star_rating": 4.2, "area": "Log Huts", "zone": "town_center", "max_occupancy": 3, "amenities": ["heater", "mountain view", "breakfast"]},
            {"name": "Snowcrest Spa Resort", "comfort_level": "premium", "nightly_rate": 6700, "star_rating": 4.7, "area": "Prini", "zone": "town_center", "max_occupancy": 4, "amenities": ["spa", "heater", "mountain view"]},
        ],
        "activities": [
            {"name": "Solang Adventure Day", "category": "adventure", "zone": "adventure_belt", "duration_hours": 5.0, "price_total": 4800, "indoor": False, "family_friendly": False, "recommended_for": ["adventure"], "slots": [("morning", "09:30", "14:30")]},
            {"name": "Hadimba and Old Manali Walk", "category": "culture", "zone": "old_manali", "duration_hours": 3.0, "price_total": 1700, "indoor": False, "family_friendly": True, "recommended_for": ["cultural", "relaxed"], "slots": [("morning", "10:00", "13:00"), ("afternoon", "15:00", "18:00")]},
            {"name": "Snow View Couple Picnic", "category": "leisure", "zone": "town_center", "duration_hours": 3.5, "price_total": 2600, "indoor": False, "family_friendly": False, "recommended_for": ["romantic", "relaxed"], "slots": [("afternoon", "14:00", "17:30")]},
        ],
        "transport": [
            {"mode": "private cab", "total_price": 3400, "convenience_score": 9.2, "coverage": "Reliable for hills and point-to-point sightseeing", "transfer_buffer_minutes": 15},
            {"mode": "self-drive car", "total_price": 4100, "convenience_score": 7.8, "coverage": "Flexible but weather-sensitive", "transfer_buffer_minutes": 18},
            {"mode": "rental bike", "total_price": 2000, "convenience_score": 6.8, "coverage": "Adventure-friendly short-distance travel", "transfer_buffer_minutes": 12},
        ],
        "food": [
            {"name": "Woodfire Cafe Brunch", "cuisine": "cafe", "meal_type": "lunch", "zone": "old_manali", "price_band": "budget", "estimated_cost_per_person": 450, "neighborhood": "Old Manali", "meal_slots": [("lunch", "12:00", "13:30")]},
            {"name": "Tibetan Kitchen Dinner", "cuisine": "Tibetan", "meal_type": "dinner", "zone": "town_center", "price_band": "mid", "estimated_cost_per_person": 700, "neighborhood": "Mall Road", "meal_slots": [("dinner", "19:00", "20:30")]},
            {"name": "Mountain View Grill", "cuisine": "continental", "meal_type": "dinner", "zone": "town_center", "price_band": "premium", "estimated_cost_per_person": 1150, "neighborhood": "Prini", "meal_slots": [("dinner", "19:30", "21:00")]},
        ],
        "flight_bases": {"Kolkata": 7800, "Delhi": 5200, "Mumbai": 7400, "Bengaluru": 8600},
        "flight_duration": {"Kolkata": 3.3, "Delhi": 1.5, "Mumbai": 2.5, "Bengaluru": 3.7},
    },
    "darjeeling": {
        "display": "Darjeeling",
        "peak_months": {3, 4, 5, 10, 11},
        "weather": {"peak": ("Crisp", 15), "regular": ("Cool", 13), "monsoon": ("Foggy", 11)},
        "hotel_zone": "town_center",
        "day_structure": {"lunch": ("13:00", "14:00"), "dinner": ("19:00", "20:45")},
        "zones": {
            "airport": {"town_center": 95, "viewpoint": 110, "tea_estate": 105},
            "town_center": {"airport": 95, "viewpoint": 25, "tea_estate": 30},
            "viewpoint": {"airport": 110, "town_center": 25, "tea_estate": 35},
            "tea_estate": {"airport": 105, "town_center": 30, "viewpoint": 35},
        },
        "hotels": [
            {"name": "Tea Garden Stay", "comfort_level": "economy", "nightly_rate": 2200, "star_rating": 3.4, "area": "Chowrasta", "zone": "town_center", "max_occupancy": 2, "amenities": ["wifi", "tea service"]},
            {"name": "Cloudline Residency", "comfort_level": "comfort", "nightly_rate": 3600, "star_rating": 4.0, "area": "Gandhi Road", "zone": "town_center", "max_occupancy": 3, "amenities": ["heater", "breakfast", "valley view"]},
            {"name": "Heritage Himalayan Manor", "comfort_level": "premium", "nightly_rate": 5600, "star_rating": 4.5, "area": "Observatory Hill", "zone": "town_center", "max_occupancy": 4, "amenities": ["fireplace", "tea lounge", "valley view"]},
        ],
        "activities": [
            {"name": "Tiger Hill Sunrise", "category": "sightseeing", "zone": "viewpoint", "duration_hours": 3.5, "price_total": 1800, "indoor": False, "family_friendly": True, "recommended_for": ["relaxed", "family", "romantic"], "slots": [("sunrise", "05:15", "08:45")]},
            {"name": "Toy Train Heritage Ride", "category": "culture", "zone": "town_center", "duration_hours": 2.0, "price_total": 2100, "indoor": True, "family_friendly": True, "recommended_for": ["cultural", "family"], "slots": [("morning", "10:30", "12:30"), ("afternoon", "14:30", "16:30")]},
            {"name": "Tea Estate Tasting", "category": "food", "zone": "tea_estate", "duration_hours": 2.5, "price_total": 1600, "indoor": False, "family_friendly": True, "recommended_for": ["foodie", "relaxed"], "slots": [("afternoon", "15:00", "17:30")]},
        ],
        "transport": [
            {"mode": "private cab", "total_price": 3200, "convenience_score": 8.9, "coverage": "Best for steep roads and early morning departures", "transfer_buffer_minutes": 15},
            {"mode": "city cab pass", "total_price": 2400, "convenience_score": 7.7, "coverage": "Suitable for local town transfers and viewpoints", "transfer_buffer_minutes": 12},
            {"mode": "rental bike", "total_price": 1900, "convenience_score": 6.1, "coverage": "Short scenic hops for confident riders", "transfer_buffer_minutes": 10},
        ],
        "food": [
            {"name": "Tea Lounge High Tea", "cuisine": "tea and bakery", "meal_type": "lunch", "zone": "town_center", "price_band": "mid", "estimated_cost_per_person": 650, "neighborhood": "Chowrasta", "meal_slots": [("lunch", "12:30", "14:00")]},
            {"name": "Momo House Dinner", "cuisine": "Tibetan", "meal_type": "dinner", "zone": "town_center", "price_band": "budget", "estimated_cost_per_person": 320, "neighborhood": "Nehru Road", "meal_slots": [("dinner", "19:00", "20:15")]},
            {"name": "Colonial Dining Room", "cuisine": "continental", "meal_type": "dinner", "zone": "town_center", "price_band": "premium", "estimated_cost_per_person": 1100, "neighborhood": "Observatory Hill", "meal_slots": [("dinner", "19:30", "21:00")]},
        ],
        "flight_bases": {"Kolkata": 2800, "Delhi": 5400, "Mumbai": 6600, "Bengaluru": 6900},
        "flight_duration": {"Kolkata": 1.1, "Delhi": 2.0, "Mumbai": 2.7, "Bengaluru": 3.0},
    },
}

AIRLINES = [
    ("SkyJet", "saver", 1.0, 15, "07:10", "10:05", "18:20", "21:15"),
    ("Vista Air", "flex", 1.18, 20, "09:00", "11:55", "16:40", "19:35"),
    ("AeroLux", "premium", 1.42, 30, "11:00", "13:55", "14:20", "17:15"),
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
    for index, (airline, tier, tier_multiplier, baggage_kg, out_dep, out_arr, in_dep, in_arr) in enumerate(AIRLINES, start=1):
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
                "outbound_departure_time": out_dep,
                "outbound_arrival_time": out_arr,
                "inbound_departure_time": in_dep,
                "inbound_arrival_time": in_arr,
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
                "zone": hotel["zone"],
                "max_occupancy": hotel["max_occupancy"],
                "amenities": hotel["amenities"],
                "availability_status": "limited" if hotel["comfort_level"] == "premium" else "available",
                "check_in_window": {"label": "hotel check-in", "start_time": "14:00", "end_time": "22:00"},
                "check_out_window": {"label": "hotel check-out", "start_time": "06:00", "end_time": "11:00"},
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
                "zone": activity["zone"],
                "duration_hours": activity["duration_hours"],
                "price_total": activity["price_total"],
                "indoor": activity["indoor"],
                "family_friendly": activity["family_friendly"],
                "recommended_for": activity["recommended_for"],
                "slots": [
                    {"label": label, "start_time": start_time, "end_time": end_time}
                    for label, start_time, end_time in activity["slots"]
                ],
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
                "transfer_buffer_minutes": option["transfer_buffer_minutes"],
                "explanation": f"{option['mode'].title()} is commonly chosen for {destination['display']} itineraries.",
            }
        )
    return LocalTransportResponse(options=options, zone_travel_minutes=destination["zones"]).model_dump()


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
                "zone": item["zone"],
                "price_band": item["price_band"],
                "estimated_cost_per_person": item["estimated_cost_per_person"],
                "neighborhood": item["neighborhood"],
                "meal_slots": [
                    {"meal_type": meal_type, "start_time": start_time, "end_time": end_time}
                    for meal_type, start_time, end_time in item["meal_slots"]
                ],
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
