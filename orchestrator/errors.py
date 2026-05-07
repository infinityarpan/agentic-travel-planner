class TravelPlannerError(Exception):
    """Base application error for orchestrator failures."""


class ConfigurationError(TravelPlannerError):
    """Raised when required application configuration is invalid."""


class PersistenceError(TravelPlannerError):
    """Raised when durable storage operations fail."""


class ResourceNotFoundError(TravelPlannerError):
    """Raised when a requested persistent resource does not exist."""
