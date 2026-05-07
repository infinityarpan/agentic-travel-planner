import os
from dataclasses import dataclass

from dotenv import load_dotenv

from orchestrator.errors import ConfigurationError

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    interpreter_model: str
    mcp_base_url: str
    database_path: str
    default_user_id: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            interpreter_model=(
                os.getenv("INTERPRETER_MODEL", "").strip()
                or os.getenv("PLANNER_MODEL", "gpt-4o-mini").strip()
            ),
            mcp_base_url=os.getenv("MCP_BASE_URL", "http://127.0.0.1:8001").rstrip("/"),
            database_path=os.getenv("TRAVEL_DB_PATH", "travel_planner.db").strip(),
            default_user_id=os.getenv("DEFAULT_USER_ID", "user_1").strip(),
        )

    def validate(self) -> None:
        if not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required to start the orchestrator service.")
        if not self.mcp_base_url:
            raise ConfigurationError("MCP_BASE_URL must be configured.")
        if not self.database_path:
            raise ConfigurationError("TRAVEL_DB_PATH must be configured.")
