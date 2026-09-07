"""Core configuration for Paridhi."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PARIDHI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_name: str = Field(
        default="Paridhi",
        description="Name of the MCP server instance",
    )
    server_version: str = Field(
        default="0.1.0",
        description="Paridhi application version",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode and verbose logging",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Spatial radius constraints (in meters)
    min_radius_meters: float = Field(
        default=100.0,
        description="Minimum allowed search radius in meters",
    )
    max_radius_meters: float = Field(
        default=50_000.0,
        description="Maximum allowed search radius in meters",
    )
    default_radius_meters: float = Field(
        default=1_000.0,
        description="Default search radius in meters when unspecified",
    )

    # Query result limits
    default_results_limit: int = Field(
        default=20,
        description="Default limit for returned POI results",
    )
    max_results_limit: int = Field(
        default=100,
        description="Maximum permissible limit for returned POI results",
    )

    # Geospatial Provider Configuration
    spatial_provider: str = Field(
        default="google",
        description="Active spatial provider implementation ('google', 'mock')",
    )
    google_maps_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GOOGLE_MAPS_API_KEY",
            "GOOGLE_API_KEY",
            "PARIDHI_GOOGLE_MAPS_API_KEY",
            "PARIDHI_GOOGLE_API_KEY",
        ),
        description="Google Maps Platform API Key for Geocoding and Places API",
    )
    geocoding_base_url: str = Field(
        default="https://maps.googleapis.com/maps/api/geocode/json",
        description="Google Maps Geocoding API endpoint",
    )
    places_search_base_url: str = Field(
        default="https://places.googleapis.com/v1/places:searchText",
        description="Google Places API (New) Text Search endpoint",
    )
    http_timeout_seconds: float = Field(
        default=10.0,
        description="HTTP client timeout in seconds for upstream provider requests",
    )

    # Server transport configuration
    transport: Literal["stdio", "http", "streamable-http", "sse"] = Field(
        default="stdio",
        description="FastMCP transport mechanism",
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host interface to bind for network transports",
    )
    port: int = Field(
        default=8000,
        description="Port to listen on for network transports",
    )
    path: str | None = Field(
        default=None,
        description="Custom endpoint path (e.g. /mcp or /sse) for network transports",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
