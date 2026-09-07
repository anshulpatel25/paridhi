"""Provider factory for instantiating SpatialProvider implementations."""

import logging

from paridhi.core.config import Settings, get_settings
from paridhi.domain.ports import SpatialProvider
from paridhi.infrastructure.google.adapter import GoogleSpatialAdapter
from paridhi.infrastructure.mock import MockSpatialProvider

logger = logging.getLogger("paridhi.infrastructure.factory")


def get_spatial_provider(settings: Settings | None = None) -> SpatialProvider:
    """Instantiate and return the configured SpatialProvider.

    Swappable via configuration (e.g. PARIDHI_SPATIAL_PROVIDER="google" or "mock").
    """
    app_settings = settings or get_settings()
    provider_name = app_settings.spatial_provider.lower().strip()

    if provider_name == "mock":
        logger.info("Initializing MockSpatialProvider")
        return MockSpatialProvider()

    if provider_name == "google":
        logger.info("Initializing GoogleSpatialAdapter")
        return GoogleSpatialAdapter(settings=app_settings)

    # Fallback to Google adapter or raise
    logger.warning(
        "Unrecognized spatial provider '%s', defaulting to Google adapter", provider_name
    )
    return GoogleSpatialAdapter(settings=app_settings)
