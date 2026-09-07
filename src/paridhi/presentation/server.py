"""FastMCP presentation layer: server instantiation and tool handlers."""

import logging

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import ValidationError as PydanticValidationError

from paridhi.core.config import Settings, get_settings
from paridhi.domain.models import (
    DiscoverPOIsRequest,
    DiscoverPOIsResponse,
    HealthCheckResponse,
    PointOfInterest,
)

logger = logging.getLogger("paridhi.server")


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the Paridhi FastMCP server instance."""
    app_settings = settings or get_settings()

    server = FastMCP(
        name=app_settings.server_name,
        instructions=(
            "Paridhi is an MCP server for discovering and enriching local points of interest "
            "(POIs) within circular spatial bounds."
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
            "Discover and search points of interest (POIs) within a circular spatial boundary. "
            "Input radius is enforced and clamped between 100 meters and 50,000 meters."
        ),
    )
    def discover_pois(
        latitude: float,
        longitude: float,
        radius_meters: float = app_settings.default_radius_meters,
        categories: list[str] | None = None,
        query: str | None = None,
        limit: int = app_settings.default_results_limit,
    ) -> DiscoverPOIsResponse:
        """Discover points of interest within circular spatial bounds.

        Args:
            latitude: Center latitude in decimal degrees [-90.0, 90.0].
            longitude: Center longitude in decimal degrees [-180.0, 180.0].
            radius_meters: Search radius in meters (automatically clamped to [100m, 50,000m]).
            categories: Optional list of category filters.
            query: Optional free-text keyword search query.
            limit: Maximum number of POIs to return (1-100).
        """
        # Validate inputs and enforce radius clamping via domain schema
        try:
            request = DiscoverPOIsRequest(
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                categories=categories,
                query=query,
                limit=limit,
            )
        except PydanticValidationError as err:
            err_details = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in err.errors())
            logger.warning("Validation failed for discover_pois: %s", err_details)
            raise ToolError(f"Invalid input parameters: {err_details}") from err

        bound = request.to_circular_bound()

        logger.info(
            "POI discovery at (%.4f, %.4f), radius %.1fm (raw: %.1fm)",
            bound.center.latitude,
            bound.center.longitude,
            bound.radius_meters,
            radius_meters,
        )

        clamping_note = ""
        min_r = app_settings.min_radius_meters
        max_r = app_settings.max_radius_meters
        if radius_meters < min_r:
            clamping_note = f" (clamped from requested {radius_meters}m to minimum {min_r}m)"
        elif radius_meters > max_r:
            clamping_note = f" (clamped from requested {radius_meters}m to maximum {max_r}m)"

        # Baseline skeleton response: ready for provider/enricher integration
        discovered: list[PointOfInterest] = []

        return DiscoverPOIsResponse(
            center=bound.center,
            radius_meters=bound.radius_meters,
            total_found=len(discovered),
            pois=discovered,
            message=(
                f"Spatial search perimeter established at radius {bound.radius_meters:.1f}m"
                f"{clamping_note}."
            ),
        )

    return server


# Default server instance
mcp = create_server()
