"""Domain layer for Paridhi containing models, entities, and exceptions."""

from paridhi.domain.exceptions import (
    DomainError,
    InvalidCoordinateError,
    ParidhiError,
    POINotFoundError,
    ProviderConnectionError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    RadiusOutOfRangeError,
    ValidationError,
)
from paridhi.domain.models import (
    DEFAULT_RADIUS_METERS,
    MAX_RADIUS_METERS,
    MIN_RADIUS_METERS,
    CircularBound,
    Coordinates,
    DiscoverPOIsRequest,
    DiscoverPOIsResponse,
    HealthCheckResponse,
    PointOfInterest,
    clamp_radius,
)

__all__ = [
    "DEFAULT_RADIUS_METERS",
    "MAX_RADIUS_METERS",
    "MIN_RADIUS_METERS",
    "CircularBound",
    "Coordinates",
    "DiscoverPOIsRequest",
    "DiscoverPOIsResponse",
    "DomainError",
    "HealthCheckResponse",
    "InvalidCoordinateError",
    "POINotFoundError",
    "ParidhiError",
    "PointOfInterest",
    "ProviderConnectionError",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "RadiusOutOfRangeError",
    "ValidationError",
    "clamp_radius",
]
