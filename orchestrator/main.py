# orchestrator/main.py

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from orchestrator.config import Settings
from orchestrator.logger import configure_logging
from orchestrator.schemas import TravelPlanRequest
from orchestrator.service import TravelPlannerService


async def run():
    configure_logging()
    settings = Settings.from_env()
    service = TravelPlannerService(settings)
    result = await service.plan_trip(
        TravelPlanRequest(
            user_query="Plan a relaxed 3-night Goa trip for 2 people under 35000 with good food",
            user_id=settings.default_user_id,
        )
    )
    print("\nFinal Output:\n", json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(run())
