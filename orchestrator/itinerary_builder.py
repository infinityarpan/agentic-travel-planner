from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from orchestrator.schemas import (
    ActivityOption,
    FoodRecommendation,
    ItineraryItem,
    LocalTransportResponse,
    MealSlot,
    ServiceTraceEntry,
    TransferLeg,
    TripBrief,
    TripDay,
    TripPackage,
)


@dataclass
class ItineraryBuildResult:
    itinerary: list[TripDay]
    schedule_assumptions: list[str]
    schedule_warnings: list[str]


class ItineraryBuilder:
    def build(
        self,
        trip_brief: TripBrief,
        trip_package: TripPackage,
        service_trace: list[ServiceTraceEntry],
    ) -> ItineraryBuildResult:
        trace_map = {entry.service: entry.response for entry in service_trace}
        transport_context = LocalTransportResponse.model_validate(trace_map["local_transport_search"])
        itinerary: list[TripDay] = []
        warnings: list[str] = []
        assumptions = [
            "Transfer times come from internal zone travel estimates.",
            "Hotel breakfast is assumed to be covered by the stay when available.",
        ]
        unscheduled_activities = list(trip_package.activities)
        lunch_option = self._choose_food(trip_package.food_recommendations, "lunch")
        dinner_option = self._choose_food(trip_package.food_recommendations, "dinner")

        current_date = trip_brief.start_date
        day_index = 0
        while current_date <= trip_brief.end_date:
            title = self._day_title(current_date, trip_brief)
            items: list[ItineraryItem] = []
            if day_index == 0:
                self._schedule_arrival_day(
                    day=current_date,
                    trip_brief=trip_brief,
                    trip_package=trip_package,
                    transport_context=transport_context,
                    unscheduled_activities=unscheduled_activities,
                    dinner_option=dinner_option,
                    items=items,
                    warnings=warnings,
                )
            elif current_date == trip_brief.end_date:
                self._schedule_departure_day(
                    day=current_date,
                    trip_brief=trip_brief,
                    trip_package=trip_package,
                    transport_context=transport_context,
                    unscheduled_activities=unscheduled_activities,
                    lunch_option=lunch_option,
                    items=items,
                    warnings=warnings,
                )
            else:
                self._schedule_full_day(
                    day=current_date,
                    trip_brief=trip_brief,
                    trip_package=trip_package,
                    transport_context=transport_context,
                    unscheduled_activities=unscheduled_activities,
                    lunch_option=lunch_option,
                    dinner_option=dinner_option,
                    items=items,
                )
            itinerary.append(TripDay(date=current_date, title=title, items=sorted(items, key=lambda item: item.start_at)))
            current_date += timedelta(days=1)
            day_index += 1

        if unscheduled_activities:
            warnings.append(
                "Some activities could not be scheduled without causing time conflicts: "
                + ", ".join(activity.name for activity in unscheduled_activities)
            )
        return ItineraryBuildResult(
            itinerary=itinerary,
            schedule_assumptions=assumptions,
            schedule_warnings=warnings,
        )

    def _schedule_arrival_day(
        self,
        *,
        day: date,
        trip_brief: TripBrief,
        trip_package: TripPackage,
        transport_context: LocalTransportResponse,
        unscheduled_activities: list[ActivityOption],
        dinner_option: FoodRecommendation | None,
        items: list[ItineraryItem],
        warnings: list[str],
    ) -> None:
        flight = trip_package.flight
        hotel = trip_package.hotel
        departure_dt = self._combine(day, flight.outbound_departure_time)
        arrival_dt = self._combine(day, flight.outbound_arrival_time)
        items.append(
            ItineraryItem(
                item_id=f"{flight.id}-outbound",
                item_type="flight",
                title=f"Fly from {flight.origin} to {flight.destination}",
                start_at=departure_dt,
                end_at=arrival_dt,
                zone="airport",
                details=f"{flight.airline} {flight.tier} outbound journey",
            )
        )

        transfer = self._transfer_leg(
            from_zone="airport",
            to_zone=hotel.zone,
            mode=trip_package.local_transport.mode,
            transport_context=transport_context,
        )
        transfer_start = arrival_dt + timedelta(minutes=trip_package.local_transport.transfer_buffer_minutes)
        transfer_end = transfer_start + timedelta(minutes=transfer.duration_minutes)
        items.append(self._transfer_item("arrival-transfer", "Airport transfer to hotel", transfer, transfer_start, transfer_end))

        earliest_checkin = self._combine(day, hotel.check_in_window.start_time)
        if transfer_end < earliest_checkin:
            items.append(
                ItineraryItem(
                    item_id=f"{hotel.id}-wait-checkin",
                    item_type="free_time",
                    title="Free time before hotel check-in",
                    start_at=transfer_end,
                    end_at=earliest_checkin,
                    zone=hotel.zone,
                    details="Use this time for a quick refresh or nearby walk.",
                )
            )
        checkin_start = max(transfer_end, earliest_checkin)
        checkin_end = checkin_start + timedelta(minutes=30)
        items.append(
            ItineraryItem(
                item_id=f"{hotel.id}-checkin",
                item_type="hotel_checkin",
                title=f"Check in at {hotel.name}",
                start_at=checkin_start,
                end_at=checkin_end,
                zone=hotel.zone,
                details=f"Check-in window starts at {hotel.check_in_window.start_time}.",
            )
        )

        activity = self._pick_activity_for_window(
            day=day,
            activities=unscheduled_activities,
            earliest_start=checkin_end + timedelta(minutes=30),
            latest_end=self._combine(day, "18:30"),
            from_zone=hotel.zone,
            transport_context=transport_context,
            transport_mode=trip_package.local_transport.mode,
            transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
        )
        if activity is not None:
            unscheduled_activities.remove(activity["activity"])
            items.extend(activity["items"])
        else:
            warnings.append("Arrival day is too compressed for a major activity; keeping the evening light.")

        if dinner_option:
            meal_item = self._schedule_meal(
                day=day,
                food=dinner_option,
                earliest_start=(items[-1].end_at if items else checkin_end) + timedelta(minutes=30),
                from_zone=(items[-1].zone or hotel.zone) if items else hotel.zone,
                transport_context=transport_context,
                transport_mode=trip_package.local_transport.mode,
                transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
            )
            if meal_item:
                items.extend(meal_item)

    def _schedule_full_day(
        self,
        *,
        day: date,
        trip_brief: TripBrief,
        trip_package: TripPackage,
        transport_context: LocalTransportResponse,
        unscheduled_activities: list[ActivityOption],
        lunch_option: FoodRecommendation | None,
        dinner_option: FoodRecommendation | None,
        items: list[ItineraryItem],
    ) -> None:
        hotel_zone = trip_package.hotel.zone
        start_cursor = self._combine(day, "08:30")
        current_zone = hotel_zone

        morning_pick = self._pick_activity_for_window(
            day=day,
            activities=unscheduled_activities,
            earliest_start=start_cursor,
            latest_end=self._combine(day, "12:45"),
            from_zone=current_zone,
            transport_context=transport_context,
            transport_mode=trip_package.local_transport.mode,
            transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
        )
        if morning_pick:
            unscheduled_activities.remove(morning_pick["activity"])
            items.extend(morning_pick["items"])
            current_zone = morning_pick["zone"]
            start_cursor = morning_pick["end_at"] + timedelta(minutes=30)

        if lunch_option:
            meal = self._schedule_meal(
                day=day,
                food=lunch_option,
                earliest_start=start_cursor,
                from_zone=current_zone,
                transport_context=transport_context,
                transport_mode=trip_package.local_transport.mode,
                transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
            )
            if meal:
                items.extend(meal)
                current_zone = meal[-1].zone or current_zone
                start_cursor = meal[-1].end_at + timedelta(minutes=30)

        afternoon_pick = self._pick_activity_for_window(
            day=day,
            activities=unscheduled_activities,
            earliest_start=start_cursor,
            latest_end=self._combine(day, "18:15"),
            from_zone=current_zone,
            transport_context=transport_context,
            transport_mode=trip_package.local_transport.mode,
            transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
        )
        if afternoon_pick:
            unscheduled_activities.remove(afternoon_pick["activity"])
            items.extend(afternoon_pick["items"])
            current_zone = afternoon_pick["zone"]
            start_cursor = afternoon_pick["end_at"] + timedelta(minutes=45)

        if dinner_option:
            meal = self._schedule_meal(
                day=day,
                food=dinner_option,
                earliest_start=start_cursor,
                from_zone=current_zone,
                transport_context=transport_context,
                transport_mode=trip_package.local_transport.mode,
                transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
            )
            if meal:
                items.extend(meal)

    def _schedule_departure_day(
        self,
        *,
        day: date,
        trip_brief: TripBrief,
        trip_package: TripPackage,
        transport_context: LocalTransportResponse,
        unscheduled_activities: list[ActivityOption],
        lunch_option: FoodRecommendation | None,
        items: list[ItineraryItem],
        warnings: list[str],
    ) -> None:
        flight = trip_package.flight
        hotel = trip_package.hotel
        departure_dt = self._combine(day, flight.inbound_departure_time)
        transfer = self._transfer_leg(
            from_zone=hotel.zone,
            to_zone="airport",
            mode=trip_package.local_transport.mode,
            transport_context=transport_context,
        )
        hotel_checkout_deadline = self._combine(day, hotel.check_out_window.end_time)
        transfer_departure = departure_dt - timedelta(minutes=90 + transfer.duration_minutes)

        short_activity = self._pick_activity_for_window(
            day=day,
            activities=unscheduled_activities,
            earliest_start=self._combine(day, "08:00"),
            latest_end=transfer_departure - timedelta(minutes=45),
            from_zone=hotel.zone,
            transport_context=transport_context,
            transport_mode=trip_package.local_transport.mode,
            transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
            max_duration_hours=2.5,
        )
        if short_activity:
            unscheduled_activities.remove(short_activity["activity"])
            items.extend(short_activity["items"])

        checkout_start = min(
            hotel_checkout_deadline - timedelta(minutes=20),
            transfer_departure - timedelta(minutes=20),
        )
        if items and checkout_start < items[-1].end_at:
            checkout_start = items[-1].end_at + timedelta(minutes=10)
        checkout_end = checkout_start + timedelta(minutes=20)
        if checkout_end > transfer_departure:
            warnings.append("Departure day is tight; hotel checkout is scheduled close to airport transfer.")
            checkout_end = transfer_departure
        items.append(
            ItineraryItem(
                item_id=f"{hotel.id}-checkout",
                item_type="hotel_checkout",
                title=f"Check out from {hotel.name}",
                start_at=checkout_start,
                end_at=checkout_end,
                zone=hotel.zone,
                details=f"Complete checkout before {hotel.check_out_window.end_time}.",
            )
        )

        if lunch_option and checkout_end < self._combine(day, "12:30") and self._combine(day, "12:30") < transfer_departure:
            meal = self._schedule_meal(
                day=day,
                food=lunch_option,
                earliest_start=checkout_end + timedelta(minutes=20),
                from_zone=hotel.zone,
                transport_context=transport_context,
                transport_mode=trip_package.local_transport.mode,
                transfer_buffer=trip_package.local_transport.transfer_buffer_minutes,
                latest_end=transfer_departure - timedelta(minutes=15),
            )
            if meal:
                items.extend(meal)

        transfer_start = departure_dt - timedelta(minutes=90 + transfer.duration_minutes)
        transfer_end = transfer_start + timedelta(minutes=transfer.duration_minutes)
        items.append(self._transfer_item("departure-transfer", "Transfer to airport", transfer, transfer_start, transfer_end))

        items.append(
            ItineraryItem(
                item_id=f"{flight.id}-inbound",
                item_type="flight",
                title=f"Return flight from {flight.destination} to {flight.origin}",
                start_at=departure_dt,
                end_at=self._combine(day, flight.inbound_arrival_time),
                zone="airport",
                details=f"{flight.airline} {flight.tier} return journey",
            )
        )

    def _pick_activity_for_window(
        self,
        *,
        day: date,
        activities: list[ActivityOption],
        earliest_start: datetime,
        latest_end: datetime,
        from_zone: str,
        transport_context: LocalTransportResponse,
        transport_mode: str,
        transfer_buffer: int,
        max_duration_hours: float | None = None,
    ) -> dict | None:
        ranked = sorted(
            activities,
            key=lambda activity: (activity.price_total, -len(activity.recommended_for)),
        )
        for activity in ranked:
            if max_duration_hours is not None and activity.duration_hours > max_duration_hours:
                continue
            transfer = self._transfer_leg(
                from_zone=from_zone,
                to_zone=activity.zone,
                mode=transport_mode,
                transport_context=transport_context,
            )
            for slot in activity.slots:
                slot_start = self._combine(day, slot.start_time)
                slot_end = self._combine(day, slot.end_time)
                if slot_end > latest_end:
                    continue
                travel_start = max(earliest_start, slot_start - timedelta(minutes=transfer.duration_minutes + transfer_buffer))
                activity_start = max(slot_start, travel_start + timedelta(minutes=transfer.duration_minutes + transfer_buffer))
                activity_end = activity_start + timedelta(minutes=int(activity.duration_hours * 60))
                if activity_end > slot_end or activity_end > latest_end:
                    continue
                transfer_item = self._transfer_item(
                    activity.id,
                    f"Travel to {activity.name}",
                    transfer,
                    activity_start - timedelta(minutes=transfer.duration_minutes + transfer_buffer),
                    activity_start,
                )
                activity_item = ItineraryItem(
                    item_id=activity.id,
                    item_type="activity",
                    title=activity.name,
                    start_at=activity_start,
                    end_at=activity_end,
                    zone=activity.zone,
                    details=f"{activity.category.title()} activity scheduled in the {slot.label} slot.",
                )
                return {
                    "activity": activity,
                    "items": [transfer_item, activity_item],
                    "zone": activity.zone,
                    "end_at": activity_end,
                }
        return None

    def _schedule_meal(
        self,
        *,
        day: date,
        food: FoodRecommendation,
        earliest_start: datetime,
        from_zone: str,
        transport_context: LocalTransportResponse,
        transport_mode: str,
        transfer_buffer: int,
        latest_end: datetime | None = None,
    ) -> list[ItineraryItem] | None:
        transfer = self._transfer_leg(
            from_zone=from_zone,
            to_zone=food.zone,
            mode=transport_mode,
            transport_context=transport_context,
        )
        for slot in food.meal_slots:
            slot_start = self._combine(day, slot.start_time)
            slot_end = self._combine(day, slot.end_time)
            meal_start = max(earliest_start + timedelta(minutes=transfer.duration_minutes + transfer_buffer), slot_start)
            meal_end = meal_start + timedelta(minutes=75)
            if meal_end > slot_end:
                continue
            if latest_end and meal_end > latest_end:
                continue
            transfer_item = self._transfer_item(
                food.id,
                f"Travel to {food.name}",
                transfer,
                meal_start - timedelta(minutes=transfer.duration_minutes + transfer_buffer),
                meal_start,
            )
            meal_item = ItineraryItem(
                item_id=food.id,
                item_type="meal",
                title=f"{food.meal_type.title()} at {food.name}",
                start_at=meal_start,
                end_at=meal_end,
                zone=food.zone,
                details=f"{food.cuisine.title()} recommendation in {food.neighborhood}.",
            )
            return [transfer_item, meal_item]
        return None

    def _transfer_leg(
        self,
        *,
        from_zone: str,
        to_zone: str,
        mode: str,
        transport_context: LocalTransportResponse,
    ) -> TransferLeg:
        duration = transport_context.zone_travel_minutes.get(from_zone, {}).get(to_zone, 25)
        return TransferLeg(from_zone=from_zone, to_zone=to_zone, mode=mode, duration_minutes=duration)

    def _transfer_item(
        self,
        item_prefix: str,
        title: str,
        transfer: TransferLeg,
        start_at: datetime,
        end_at: datetime,
    ) -> ItineraryItem:
        return ItineraryItem(
            item_id=f"{item_prefix}-{transfer.from_zone}-{transfer.to_zone}",
            item_type="transfer",
            title=title,
            start_at=start_at,
            end_at=end_at,
            zone=transfer.to_zone,
            details=f"{transfer.mode.title()} transfer from {transfer.from_zone} to {transfer.to_zone}.",
        )

    def _choose_food(self, foods, meal_type: str) -> FoodRecommendation | None:
        for food in foods:
            if food.meal_type == meal_type:
                return food
        return foods[0] if foods else None

    def _day_title(self, day: date, trip_brief: TripBrief) -> str:
        if day == trip_brief.start_date:
            return "Arrival day"
        if day == trip_brief.end_date:
            return "Departure day"
        return f"Day {(day - trip_brief.start_date).days + 1}"

    def _combine(self, day: date, raw_time: str) -> datetime:
        hour, minute = (int(part) for part in raw_time.split(":"))
        return datetime.combine(day, time(hour=hour, minute=minute))
