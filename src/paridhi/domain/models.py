"""Domain models and Pydantic validation schemas for Paridhi."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude}"


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


class Place(BaseModel):
    """Geographic Place entity representing a discovered Point of Interest."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Display name of the place")
    formatted_address: str = Field(default="N/A", description="Formatted street address")
    maps_url: str | None = Field(default=None, description="Direct URL to view the place on maps")
    rating: float | None = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Average star rating (0.0 to 5.0)",
    )
    user_rating_count: int | None = Field(
        default=None,
        ge=0,
        description="Total number of user reviews/ratings",
    )
    location: Coordinates | None = Field(
        default=None,
        description="Geographic coordinates of the place",
    )

    @property
    def map_location_link(self) -> str:
        """Markdown formatted pin link: [Pin](<url>)."""
        url = self.maps_url
        if not url and self.location:
            url = f"https://maps.google.com/?q={self.location.latitude},{self.location.longitude}"
        return f"[Pin]({url})" if url else "[Pin](#)"

    @property
    def ratings_link(self) -> str:
        """Markdown formatted ratings link: [<rating> ★ (<count>)](<url>) or N/A."""
        if self.rating is None:
            return "N/A"
        count_str = f"{self.user_rating_count:,}" if self.user_rating_count is not None else "0"
        label = f"{self.rating:.1f} ★ ({count_str})"
        url = self.maps_url
        if not url and self.location:
            url = f"https://maps.google.com/?q={self.location.latitude},{self.location.longitude}"
        return f"[{label}]({url})" if url else label


def format_places_table(places: list[Place]) -> str:
    """Format a collection of Place objects into a clean Markdown table with deep links.

    Header format:
    | Place Name | Address | Google Map location | Google Ratings |
    | :--- | :--- | :--- | :--- |
    """
    if not places:
        return "No places found matching the search criteria."

    lines = [
        "| Place Name | Address | Google Map location | Google Ratings |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for p in places:
        lines.append(
            f"| **{p.name}** | {p.formatted_address} | {p.map_location_link} | {p.ratings_link} |"
        )
    return "\n".join(lines)


class PlaceSearchRequest(BaseModel):
    """Domain request parameters for place searching."""

    query: str = Field(
        ..., min_length=1, description="Search term or POI keyword (e.g. 'vadapav shops')"
    )
    center: Coordinates = Field(..., description="Geographic coordinates of circular search origin")
    radius_meters: int = Field(
        default=int(DEFAULT_RADIUS_METERS),
        description="Search radius in meters clamped [100m, 50,000m]",
    )

    @field_validator("radius_meters", mode="before")
    @classmethod
    def clamp_int_radius(cls, value: Any) -> int:
        if value is None:
            return int(DEFAULT_RADIUS_METERS)
        try:
            val = int(float(value))
        except (ValueError, TypeError) as err:
            msg = f"radius_meters must be a valid numeric value, got: {value!r}"
            raise ValueError(msg) from err
        return int(clamp_radius(val))


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

    model_config = ConfigDict(extra="ignore")

    query: str = Field(
        default="points of interest",
        description="Search term, cuisine, or category keyword (e.g. 'vadapav shops')",
    )
    location: str | None = Field(
        default=None,
        description="Origin address or neighborhood string to geocode (e.g. 'Bhatta, Paldi')",
    )
    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Latitude of search center [-90.0, 90.0]",
    )
    longitude: float | None = Field(
        default=None,
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
        description="Optional list of category filters",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=20,
        description="Maximum number of POIs to return (1-20)",
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

    @model_validator(mode="after")
    def validate_spatial_origin(self) -> "DiscoverPOIsRequest":
        """Ensure either an address/neighborhood string or valid coordinates are provided."""
        has_coords = self.latitude is not None and self.longitude is not None
        has_location = bool(self.location and self.location.strip())
        if not has_coords and not has_location:
            raise ValueError(
                "Either 'location' (e.g. 'Bhatta, Paldi') or both 'latitude' and 'longitude' "
                "must be specified as search origin."
            )
        return self

    def to_circular_bound(self) -> CircularBound:
        """Convert validated request into a domain CircularBound object."""
        if self.latitude is None or self.longitude is None:
            raise ValueError("Coordinates must be resolved before converting to CircularBound")
        return CircularBound(
            center=Coordinates(latitude=self.latitude, longitude=self.longitude),
            radius_meters=self.radius_meters,
        )


class DiscoverPOIsResponse(BaseModel):
    """Response containing discovered POIs within the circular perimeter."""

    center: Coordinates = Field(..., description="Center of the circular search area")
    radius_meters: float = Field(..., description="Effective radius applied in meters (clamped)")
    total_found: int = Field(..., description="Number of POIs returned in this response")
    places: list[Place] = Field(
        default_factory=list,
        description="Collection of discovered place entities",
    )
    markdown_table: str = Field(
        default="",
        description="Formatted Markdown table with deep links",
    )
    pois: list[PointOfInterest] = Field(
        default_factory=list,
        description="Backward-compatible POI collection",
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
