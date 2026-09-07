"""Domain models and Pydantic validation schemas for Paridhi."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_RADIUS_METERS: float = 100.0
MAX_RADIUS_METERS: float = 50_000.0
DEFAULT_RADIUS_METERS: float = 1_000.0


def clamp_radius(
    radius: float,
    min_radius: float = MIN_RADIUS_METERS,
    max_radius: float = MAX_RADIUS_METERS,
) -> float:
    """Clamp a search radius to strictly fall within [min_radius, max_radius] meters."""
    return max(min_radius, min(max_radius, radius))


class Coordinates(BaseModel):
    """Geographic coordinate representation (WGS 84)."""

    model_config = ConfigDict(frozen=True)

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees [-90.0, 90.0]",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees [-180.0, 180.0]",
    )


class CircularBound(BaseModel):
    """Circular geographic boundary defined by a center point and search radius."""

    model_config = ConfigDict(frozen=True)

    center: Coordinates = Field(..., description="Center coordinate of the circular perimeter")
    radius_meters: float = Field(
        default=DEFAULT_RADIUS_METERS,
        description="Radius in meters, automatically clamped to [100m, 50,000m]",
    )

    @field_validator("radius_meters", mode="before")
    @classmethod
    def validate_and_clamp_radius(cls, value: Any) -> float:
        """Clamp radius to the allowed geographic limits [100m, 50000m]."""
        if value is None:
            return DEFAULT_RADIUS_METERS
        try:
            val = float(value)
        except (ValueError, TypeError) as err:
            msg = f"radius_meters must be a valid numeric value, got: {value!r}"
            raise ValueError(msg) from err
        return clamp_radius(val)


class PointOfInterest(BaseModel):
    """Point of Interest (POI) within spatial perimeter."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Unique POI identifier")
    name: str = Field(..., description="Display name of the place/point of interest")
    location: Coordinates = Field(..., description="Geographic location of the POI")
    category: str = Field(default="general", description="Primary category/classification")
    address: str | None = Field(default=None, description="Physical address descriptor")
    distance_meters: float | None = Field(
        default=None,
        description="Calculated distance in meters from the query center",
    )
    tags: dict[str, Any] = Field(
        default_factory=dict,
        description="Descriptive tags (e.g. amenities, cuisine, opening hours)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Upstream provider metadata and enrichment payloads",
    )


class DiscoverPOIsRequest(BaseModel):
    """Request parameters for discovering POIs within circular spatial bounds."""

    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude of search center [-90.0, 90.0]",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude of search center [-180.0, 180.0]",
    )
    radius_meters: float = Field(
        default=DEFAULT_RADIUS_METERS,
        description="Search radius in meters. Automatically clamped between 100m and 50,000m.",
    )
    categories: list[str] | None = Field(
        default=None,
        description="Optional list of category filters (e.g. ['restaurant', 'park', 'museum'])",
    )
    query: str | None = Field(
        default=None,
        description="Optional free-text search term or keyword to match against POI names/tags",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of POIs to return (1-100)",
    )

    @field_validator("radius_meters", mode="before")
    @classmethod
    def enforce_clamped_radius(cls, value: Any) -> float:
        """Enforce geographic radius constraints by clamping between 100m and 50,000m."""
        if value is None:
            return DEFAULT_RADIUS_METERS
        try:
            val = float(value)
        except (ValueError, TypeError) as err:
            msg = f"radius_meters must be a valid numeric value, got: {value!r}"
            raise ValueError(msg) from err
        return clamp_radius(val)

    def to_circular_bound(self) -> CircularBound:
        """Convert validated request into a domain CircularBound object."""
        return CircularBound(
            center=Coordinates(latitude=self.latitude, longitude=self.longitude),
            radius_meters=self.radius_meters,
        )


class DiscoverPOIsResponse(BaseModel):
    """Response containing discovered POIs within the circular perimeter."""

    center: Coordinates = Field(..., description="Center of the circular search area")
    radius_meters: float = Field(..., description="Effective radius applied in meters (clamped)")
    total_found: int = Field(..., description="Number of POIs returned in this response")
    pois: list[PointOfInterest] = Field(
        default_factory=list,
        description="Collection of discovered points of interest",
    )
    message: str | None = Field(
        default=None,
        description="Status or enrichment summary message",
    )


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Operational status of the server")
    service: str = Field(default="Paridhi", description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the health check",
    )
