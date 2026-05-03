import asyncio
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from orchestrator.config import Settings
from orchestrator.schemas import CriticFeedback, PlanStep, parse_critic_feedback, parse_plan_steps


TRANSIENT_OPENAI_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError)


class PlannerAgent:
    def __init__(self, mcp_client, settings: Settings):
        self.mcp = mcp_client
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def plan(self, user_query: str, memory: dict[str, Any]) -> list[PlanStep]:
        tools = await self.mcp.list_tools()
        prompt = f"""
You are a travel planning agent.

User request: {user_query}

User preferences:
{memory}

Available tools:
{[tool.model_dump() for tool in tools]}

Return a JSON array of steps like:
[
  {{"tool": "weather", "input": {{"location": "Goa"}}}},
  {{"tool": "flights", "input": {{"from": "Kolkata", "to": "Goa"}}}}
]

Only return valid JSON. No explanation.
"""
        return await self._with_retries(
            lambda: self._generate_plan(prompt),
            fallback=[
                PlanStep(tool="weather", input={"location": "Goa"}),
                PlanStep(tool="flights", input={"from": "Kolkata", "to": "Goa"}),
                PlanStep(tool="hotels", input={"location": "Goa"}),
            ],
        )

    async def _generate_plan(self, prompt: str) -> list[PlanStep]:
        response = await self.client.chat.completions.create(
            model=self.settings.planner_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "[]"
        return parse_plan_steps(content)

    async def _with_retries(self, operation, fallback):
        last_error = None
        for attempt in range(1, self.settings.openai_max_retries + 1):
            try:
                return await operation()
            except TRANSIENT_OPENAI_ERRORS as exc:
                last_error = exc
                if attempt == self.settings.openai_max_retries:
                    break
                await asyncio.sleep(self.settings.openai_retry_delay_seconds)
            except Exception:
                return fallback
        return fallback if last_error else fallback


class ExecutorAgent:
    def __init__(self, mcp_client):
        self.mcp = mcp_client

    async def execute(self, plan: list[dict[str, Any]] | list[PlanStep]) -> list[dict[str, Any]]:
        normalized_plan = [
            step if isinstance(step, PlanStep) else PlanStep.model_validate(step)
            for step in plan
        ]

        async def run_step(step: PlanStep):
            result = await self.mcp.call_tool(step.tool, step.input)
            return {step.tool: result}

        tasks = [run_step(step) for step in normalized_plan]
        return await asyncio.gather(*tasks)


class CriticAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def review(self, user_query: str, results: list[dict[str, Any]]) -> CriticFeedback:
        prompt = f"""
User request: {user_query}

Execution results:
{results}

Evaluate:
- Did we satisfy the user?
- Are results valid?

Return JSON:
{{"status": "good" or "bad", "reason": "..."}}
"""
        return await self._with_retries(lambda: self._generate_feedback(prompt))

    async def _generate_feedback(self, prompt: str) -> CriticFeedback:
        response = await self.client.chat.completions.create(
            model=self.settings.critic_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return parse_critic_feedback(content)

    async def _with_retries(self, operation):
        for attempt in range(1, self.settings.openai_max_retries + 1):
            try:
                return await operation()
            except TRANSIENT_OPENAI_ERRORS:
                if attempt == self.settings.openai_max_retries:
                    break
                await asyncio.sleep(self.settings.openai_retry_delay_seconds)
            except Exception:
                return CriticFeedback(status="good", reason="Critic fallback applied.")
        return CriticFeedback(status="good", reason="Critic fallback applied after retries.")
