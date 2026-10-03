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


class GeocodingFailedError(DomainError):
    """Raised when an address or location string cannot be resolved into coordinates."""

    def __init__(self, location: str, reason: str | None = None) -> None:
        msg = f"Could not geocode location '{location}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, details={"location": location, "reason": reason})


class ZeroPlacesFoundError(DomainError):
    """Raised when no places or POIs are found for the search criteria."""

    def __init__(
        self, query: str, location: str | None = None, radius_meters: int | None = None
    ) -> None:
        loc_str = f" near '{location}'" if location else ""
        rad_str = f" within {radius_meters}m" if radius_meters else ""
        msg = f"No places found matching '{query}'{loc_str}{rad_str}."
        super().__init__(
            msg,
            details={"query": query, "location": location, "radius_meters": radius_meters},
        )


class ProviderError(ParidhiError):
    """Base exception for external POI data provider and enrichment failures."""


class ProviderUnavailableError(ProviderError):
    """Raised when failing to connect to or communicate with an external provider."""


class ProviderConnectionError(ProviderUnavailableError):
    """Raised when failing to establish a network connection to the provider."""


class ProviderTimeoutError(ProviderUnavailableError):
    """Raised when a request to an external POI provider times out."""


class ProviderQuotaExceededError(ProviderError):
    """Raised when external POI provider rate limits or quotas are exceeded."""


class ProviderRateLimitError(ProviderQuotaExceededError):
    """Alias for quota exceeded / rate limited conditions."""


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with the external provider fails (invalid/missing API key)."""
