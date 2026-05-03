import asyncio
from typing import Any

from openai import AsyncOpenAI

from orchestrator.config import Settings
from orchestrator.schemas import CriticFeedback, PlanStep, parse_critic_feedback, parse_plan_steps


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
        response = await self.client.chat.completions.create(
            model=self.settings.planner_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "[]"
        return parse_plan_steps(content)


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
        response = await self.client.chat.completions.create(
            model=self.settings.critic_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return parse_critic_feedback(content)
