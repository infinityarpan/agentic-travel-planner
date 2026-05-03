class TravelPlannerError(Exception):
    """Base application error for orchestrator failures."""


class ConfigurationError(TravelPlannerError):
    """Raised when required application configuration is invalid."""


class ToolExecutionError(TravelPlannerError):
    """Raised when an MCP tool call fails or returns invalid data."""

    def __init__(
        self,
        *,
        tool_name: str,
        error_type: str,
        detail: str,
        status_code: int,
        retryable: bool,
    ):
        super().__init__(detail)
        self.tool_name = tool_name
        self.error_type = error_type
        self.detail = detail
        self.status_code = status_code
        self.retryable = retryable


class ServiceDependencyError(TravelPlannerError):
    """Raised when a non-tool dependency fails inside orchestration."""

    def __init__(self, detail: str, *, error_type: str = "internal_error", status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.error_type = error_type
        self.status_code = status_code


class PersistenceError(TravelPlannerError):
    """Raised when durable storage operations fail."""


class ResourceNotFoundError(TravelPlannerError):
    """Raised when a requested persistent resource does not exist."""
