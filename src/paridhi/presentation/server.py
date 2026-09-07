"""FastMCP presentation layer: server instantiation and tool handlers."""

import logging

from fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from paridhi.core.config import Settings, get_settings
from paridhi.domain.exceptions import (
    GeocodingFailedError,
    ParidhiError,
    ProviderAuthenticationError,
    ProviderQuotaExceededError,
    ProviderUnavailableError,
    ZeroPlacesFoundError,
)
from paridhi.domain.models import (
    Coordinates,
    DiscoverPOIsRequest,
    HealthCheckResponse,
    format_places_table,
)
from paridhi.domain.ports import SpatialProvider
from paridhi.infrastructure.factory import get_spatial_provider

logger = logging.getLogger("paridhi.server")


def create_server(
    settings: Settings | None = None,
    provider: SpatialProvider | None = None,
) -> FastMCP:
    """Create and configure the Paridhi FastMCP server instance.

    Injects the SpatialProvider interface (Ports & Adapters pattern) to ensure
    presentation logic remains fully decoupled from concrete geospatial backends.
    """
    app_settings = settings or get_settings()
    spatial_provider = provider or get_spatial_provider(app_settings)

    server = FastMCP(
        name=app_settings.server_name,
        instructions=(
            "Paridhi is a geospatial MCP server for discovering and enriching local points "
            "of interest (POIs) within circular spatial bounds using Google Maps Platform."
        ),
    )

    @server.tool(
        name="ping",
        description="Health-check endpoint verifying the Paridhi MCP server is operational.",
    )
    def ping() -> HealthCheckResponse:
        """Return server health status, version, and current timestamp."""
        logger.debug("Health-check ping invoked")
        return HealthCheckResponse(
            status="healthy",
            service=app_settings.server_name,
            version=app_settings.server_version,
        )

    @server.tool(
        name="discover_pois",
        description=(
            "Discover points of interest (POIs) within circular spatial bounds using real-world "
            "geospatial data (Google Maps Geocoding & Places API New). "
            "Accepts a query, origin location name (e.g. 'Bhatta, Paldi') or coordinates, "
            "and a radius in meters (clamped [100m, 50,000m]). Returns Markdown table."
        ),
    )
    async def discover_pois(
        query: str = "points of interest",
        location: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_meters: float = app_settings.default_radius_meters,
        limit: int = app_settings.default_results_limit,
    ) -> str:
        """Discover points of interest within circular spatial bounds.

        Args:
            query: Search query, cuisine, or place category (e.g. 'vadapav shops').
            location: Informal address, landmark, or neighborhood (e.g. 'Bhatta, Paldi').
            latitude: Optional direct center latitude in decimal degrees [-90.0, 90.0].
            longitude: Optional direct center longitude in decimal degrees [-180.0, 180.0].
            radius_meters: Search radius in meters (automatically clamped [100m, 50,000m]).
            limit: Maximum results to retrieve (1-20).

        Returns:
            Formatted Markdown table containing discovered places with deep links.
        """
        # 1. Validate input parameters and spatial constraints
        try:
            request = DiscoverPOIsRequest(
                query=query,
                location=location,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                limit=limit,
            )
        except PydanticValidationError as err:
            err_details = "; ".join(
                f"{e['loc'][0]}: {e['msg']}"
                if e.get("loc")
                else str(e.get("msg", "Validation error"))
                for e in err.errors()
            )
            logger.warning("Input validation failed for discover_pois: %s", err_details)
            return f"⚠️ **Invalid Input**: {err_details}"

        # 2. Resolve origin coordinates (Geocoding pipeline)
        origin_desc: str
        center: Coordinates
        try:
            if request.latitude is not None and request.longitude is not None:
                center = Coordinates(latitude=request.latitude, longitude=request.longitude)
                origin_desc = f"coordinates ({center.latitude:.4f}, {center.longitude:.4f})"
            elif request.location:
                origin_desc = f"'{request.location.strip()}'"
                center = await spatial_provider.geocode(request.location.strip())
            else:
                return (
                    "⚠️ **Missing Origin**: Please provide either a location string or coordinates."
                )
        except GeocodingFailedError as exc:
            logger.warning("Geocoding failed for '%s': %s", request.location, exc.message)
            return (
                f"⚠️ **Geocoding Error**: {exc.message}. "
                "Please check the location spelling or try nearby landmarks."
            )
        except ProviderAuthenticationError as exc:
            logger.error("Authentication error during geocoding: %s", exc.message)
            return f"⚠️ **Authentication Failed**: {exc.message}"
        except ProviderQuotaExceededError as exc:
            logger.error("Quota exceeded during geocoding: %s", exc.message)
            return f"⚠️ **Quota Exceeded**: Geospatial provider quota exceeded. {exc.message}"
        except ProviderUnavailableError as exc:
            logger.error("Provider unavailable during geocoding: %s", exc.message)
            return f"⚠️ **Provider Unavailable**: Could not reach geospatial provider. {exc.message}"
        except ParidhiError as exc:
            logger.error("Domain error during geocoding: %s", exc.message)
            return f"⚠️ **Geocoding Error**: {exc.message}"

        # 3. Discover places within circular boundary
        effective_radius = int(request.radius_meters)
        logger.info(
            "Searching for '%s' near %s (coords: %s) within %dm",
            request.query,
            origin_desc,
            center,
            effective_radius,
        )

        try:
            places = await spatial_provider.search_places(
                query=request.query,
                center=center,
                radius_meters=effective_radius,
            )
        except ZeroPlacesFoundError as exc:
            logger.info("Zero places found: %s", exc.message)
            return (
                f"ℹ️ **No Places Found**: No results matching '{request.query}' within "
                f"{effective_radius}m of {origin_desc}."
            )
        except ProviderAuthenticationError as exc:
            logger.error("Authentication error during places search: %s", exc.message)
            return f"⚠️ **Authentication Failed**: {exc.message}"
        except ProviderQuotaExceededError as exc:
            logger.error("Quota exceeded during places search: %s", exc.message)
            return f"⚠️ **Quota Exceeded**: Provider quota exceeded. {exc.message}"
        except ProviderUnavailableError as exc:
            logger.error("Provider unavailable during places search: %s", exc.message)
            return f"⚠️ **Provider Unavailable**: Could not reach Places API. {exc.message}"
        except ParidhiError as exc:
            logger.error("Domain error during places search: %s", exc.message)
            return f"⚠️ **Discovery Error**: {exc.message}"

        # 4. Generate clean Markdown table with deep links
        clamping_note = ""
        min_r = int(app_settings.min_radius_meters)
        max_r = int(app_settings.max_radius_meters)
        if radius_meters < min_r:
            clamping_note = (
                f"\n\n_Note: Radius was adjusted from {radius_meters:.0f}m to minimum {min_r}m._"
            )
        elif radius_meters > max_r:
            clamping_note = (
                f"\n\n_Note: Radius was adjusted from {radius_meters:.0f}m to maximum {max_r}m._"
            )

        table = format_places_table(places)
        return (
            f"### Discovered '{request.query}' within {effective_radius}m of {origin_desc}\n\n"
            f"{table}"
            f"{clamping_note}"
        )

    return server


# Default server instance
mcp = create_server()
