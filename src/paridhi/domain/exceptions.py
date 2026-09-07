"""Domain and infrastructure exception hierarchy for Paridhi."""

from typing import Any


class ParidhiError(Exception):
    """Base exception for all Paridhi domain and infrastructure errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(ParidhiError):
    """Raised when spatial inputs, query criteria, or filters fail validation."""


class InvalidCoordinateError(ValidationError):
    """Raised when geographic coordinates fall outside valid latitude/longitude bounds."""

    def __init__(self, latitude: float, longitude: float, reason: str | None = None) -> None:
        msg = f"Invalid geographic coordinates: (lat: {latitude}, lon: {longitude})"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg, details={"latitude": latitude, "longitude": longitude})


class RadiusOutOfRangeError(ValidationError):
    """Raised when a spatial radius value is non-positive or violates invariants."""

    def __init__(self, radius: float, min_radius: float, max_radius: float) -> None:
        msg = f"Radius {radius}m is out of permissible range [{min_radius}m, {max_radius}m]"
        super().__init__(
            msg,
            details={"radius": radius, "min_radius": min_radius, "max_radius": max_radius},
        )


class DomainError(ParidhiError):
    """Base exception for business logic and domain rule violations."""


class POINotFoundError(DomainError):
    """Raised when a specific Point of Interest is not found."""

    def __init__(self, poi_id: str) -> None:
        super().__init__(f"Point of Interest not found: {poi_id}", details={"poi_id": poi_id})


class ProviderError(ParidhiError):
    """Base exception for external POI data provider and enrichment failures."""


class ProviderConnectionError(ProviderError):
    """Raised when failing to connect to an external POI provider."""


class ProviderTimeoutError(ProviderError):
    """Raised when a request to an external POI provider times out."""


class ProviderRateLimitError(ProviderError):
    """Raised when external POI provider rate limits are exceeded."""
