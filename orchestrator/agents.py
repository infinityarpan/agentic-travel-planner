from datetime import date, timedelta
from typing import Any

from openai import AsyncOpenAI

from orchestrator.config import Settings
from orchestrator.schemas import TripBrief, parse_trip_brief


class TripBriefAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def interpret(
        self,
        user_query: str,
        memory: dict[str, Any],
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TripBrief:
        suggested_start = start_date or (date.today() + timedelta(days=30))
        suggested_end = end_date or (suggested_start + timedelta(days=3))
        prompt = f"""
You are an internal travel-platform query interpreter.

Convert the user request into JSON that matches this shape exactly:
{{
  "origin": "string",
  "destination": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "duration_nights": 3,
  "traveler_count": 2,
  "total_budget": 35000,
  "trip_style": "relaxed|adventure|cultural|family|foodie|romantic",
  "interests": ["string"],
  "food_preferences": ["string"],
  "constraints": ["string"],
  "travel_month": 11,
  "assumptions": ["string"],
  "arrival_time_preference": "morning|afternoon|evening|null",
  "departure_time_preference": "morning|afternoon|evening|null"
}}

Rules:
- Prefer explicit user details over defaults.
- If origin is missing, use "{memory.get('home_city', 'Kolkata')}" and record that assumption.
- If traveler count is missing, assume 2 and record that assumption.
- If dates are missing, use start_date "{suggested_start.isoformat()}" and end_date "{suggested_end.isoformat()}" and record that assumption.
- If budget is missing, assume 30000 and record that assumption.
- Keep interests and food_preferences concise and relevant.
- Only return valid JSON with no explanation.

Date hints from API:
- start_date hint: {start_date.isoformat() if start_date else "null"}
- end_date hint: {end_date.isoformat() if end_date else "null"}

User memory:
{memory}

User request:
{user_query}
"""
        response = await self.client.chat.completions.create(
            model=self.settings.interpreter_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return parse_trip_brief(content)
