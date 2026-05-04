from typing import Any

from openai import AsyncOpenAI

from orchestrator.config import Settings
from orchestrator.schemas import TripBrief, parse_trip_brief

from orchestrator.logger import get_logger

logger = get_logger("agents")


class TripBriefAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def interpret(self, user_query: str, memory: dict[str, Any]) -> TripBrief:
        prompt = f"""
You are an internal travel-platform query interpreter.

Convert the user request into JSON that matches this shape exactly:
{{
  "origin": "string",
  "destination": "string",
  "duration_nights": 3,
  "traveler_count": 2,
  "total_budget": 35000,
  "trip_style": "relaxed|adventure|cultural|family|foodie|romantic",
  "interests": ["string"],
  "food_preferences": ["string"],
  "constraints": ["string"],
  "travel_month": 11,
  "assumptions": ["string"]
}}

Rules:
- Properly understand user's query and prefer explicit user details over defaults.
- If origin is missing, use "{memory.get('home_city', 'Kolkata')}" and record that in assumptions.
- If traveler count is missing, assume 2 and record that in assumptions.
- If duration is missing, assume 3 nights and record that in assumptions.
- If budget is missing, assume 30000 and record that in assumptions.
- If month/season is missing, use null for travel_month and record a seasonal in assumptions.
- Keep interests and food_preferences concise and relevant.
- Only return valid JSON with no explanation.

User memory:
{memory}

User request:
{user_query}
"""
        logger.info(f"Interpreting user query with prompt:\n{prompt}")
        response = await self.client.chat.completions.create(
            model=self.settings.interpreter_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return parse_trip_brief(content)
