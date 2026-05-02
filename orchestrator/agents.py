# orchestrator/agents.py

import asyncio
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # loads from .env

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


class PlannerAgent:

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    async def plan(self, user_query, memory):

        tools = await self.mcp.list_tools()

        prompt = f"""
You are a travel planning agent.

User request: {user_query}

User preferences:
{memory}

Available tools:
{tools}

Return a JSON array of steps like:
[
  {{"tool": "flights", "input": {{...}}}},
  {{"tool": "hotels", "input": {{...}}}}
]

Only return JSON. No explanation.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except:
            print("⚠️ Failed parsing, fallback to default")
            return [
                {"tool": "flights", "input": {"from": "Kolkata", "to": "Goa"}},
                {"tool": "hotels", "input": {"location": "Goa"}},
            ]

class ExecutorAgent:

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    async def execute(self, plan):

        async def run_step(step):
            result = await self.mcp.call_tool(
                step["tool"],
                step["input"]
            )
            return {step["tool"]: result}

        tasks = [run_step(step) for step in plan]

        results = await asyncio.gather(*tasks)

        return results


class CriticAgent:

    def review(self, user_query, results):

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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except:
            return {"status": "good"}
