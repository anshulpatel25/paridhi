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

    # Authentication & OAuth 2.1 Provider Configuration
    auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("PARIDHI_AUTH_ENABLED", "AUTH_ENABLED"),
        description="Enable OAuth 2.1 authentication on FastMCP server",
    )
    auth_provider: str = Field(
        default="google",
        validation_alias=AliasChoices("PARIDHI_AUTH_PROVIDER", "AUTH_PROVIDER"),
        description="Active OAuth identity provider ('google', 'github', 'oidc', 'none')",
    )
    auth_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PARIDHI_AUTH_BASE_URL", "AUTH_BASE_URL"),
        description="Public base URL for OAuth endpoints (e.g. http://localhost:8000 or https://mcp.domain.com)",
    )
    auth_jwt_signing_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "JWT_SIGNING_KEY",
            "PARIDHI_JWT_SIGNING_KEY",
            "PARIDHI_AUTH_JWT_SIGNING_KEY",
        ),
        description="Secret key for signing internal FastMCP JWT access tokens",
    )
    auth_require_consent: bool = Field(
        default=True,
        validation_alias=AliasChoices("PARIDHI_AUTH_REQUIRE_CONSENT", "AUTH_REQUIRE_CONSENT"),
        description="Whether to show user authorization consent screen before redirecting to IdP",
    )
    auth_allowed_redirect_uris: list[str] | None = Field(
        default=None,
        description="Allowed client redirect URI patterns for MCP clients (None allows all)",
    )

    # Google OAuth 2.0 IdP Settings
    google_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GOOGLE_CLIENT_ID",
            "PARIDHI_GOOGLE_CLIENT_ID",
            "PARIDHI_OAUTH_GOOGLE_CLIENT_ID",
        ),
        description="Google OAuth 2.0 Web Client ID",
    )
    google_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GOOGLE_CLIENT_SECRET",
            "PARIDHI_GOOGLE_CLIENT_SECRET",
            "PARIDHI_OAUTH_GOOGLE_CLIENT_SECRET",
        ),
        description="Google OAuth 2.0 Client Secret",
    )
    google_oauth_scopes: list[str] = Field(
        default_factory=lambda: [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        description="Scopes requested from Google during OAuth flow",
    )

    # Alternative IdP Settings (for future flexibility: GitHub, Keycloak, Auth0, Okta, etc.)
    github_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GITHUB_CLIENT_ID", "PARIDHI_GITHUB_CLIENT_ID"),
        description="GitHub OAuth App Client ID",
    )
    github_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GITHUB_CLIENT_SECRET", "PARIDHI_GITHUB_CLIENT_SECRET"),
        description="GitHub OAuth App Client Secret",
    )
    oidc_config_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OIDC_CONFIG_URL", "PARIDHI_OIDC_CONFIG_URL"),
        description="OpenID Connect discovery URL (e.g. https://idp.example.com/.well-known/openid-configuration)",
    )
    oidc_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OIDC_CLIENT_ID", "PARIDHI_OIDC_CLIENT_ID"),
        description="Generic OIDC Client ID",
    )
    oidc_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OIDC_CLIENT_SECRET", "PARIDHI_OIDC_CLIENT_SECRET"),
        description="Generic OIDC Client Secret",
    )

    @property
    def effective_auth_base_url(self) -> str:
        """Derive effective public base URL for OAuth endpoints if not explicitly configured."""
        if self.auth_base_url and self.auth_base_url.strip():
            return self.auth_base_url.strip()
        host = "localhost" if self.host in ("0.0.0.0", "127.0.0.1") else self.host
        return f"http://{host}:{self.port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
