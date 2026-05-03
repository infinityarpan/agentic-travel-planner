import os
from dataclasses import dataclass

from dotenv import load_dotenv

from orchestrator.errors import ConfigurationError

load_dotenv()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    planner_model: str
    critic_model: str
    mcp_base_url: str
    database_path: str
    default_user_id: str
    critic_max_attempts: int
    openai_max_retries: int
    openai_retry_delay_seconds: float
    mcp_timeout_seconds: float
    weather_timeout_seconds: float
    weather_enabled: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            planner_model=os.getenv("PLANNER_MODEL", "gpt-4o-mini").strip(),
            critic_model=os.getenv("CRITIC_MODEL", "gpt-4o-mini").strip(),
            mcp_base_url=os.getenv("MCP_BASE_URL", "http://127.0.0.1:8001").rstrip("/"),
            database_path=os.getenv("TRAVEL_DB_PATH", "travel_planner.db").strip(),
            default_user_id=os.getenv("DEFAULT_USER_ID", "user_1").strip(),
            critic_max_attempts=max(1, int(os.getenv("CRITIC_MAX_ATTEMPTS", "3"))),
            openai_max_retries=max(1, int(os.getenv("OPENAI_MAX_RETRIES", "3"))),
            openai_retry_delay_seconds=float(os.getenv("OPENAI_RETRY_DELAY_SECONDS", "1.0")),
            mcp_timeout_seconds=float(os.getenv("MCP_TIMEOUT_SECONDS", "10.0")),
            weather_timeout_seconds=float(os.getenv("WEATHER_TIMEOUT_SECONDS", "10.0")),
            weather_enabled=_as_bool(os.getenv("WEATHER_ENABLED"), True),
        )

    def validate(self) -> None:
        if not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required to start the orchestrator service.")
        if not self.mcp_base_url:
            raise ConfigurationError("MCP_BASE_URL must be configured.")
        if not self.database_path:
            raise ConfigurationError("TRAVEL_DB_PATH must be configured.")
