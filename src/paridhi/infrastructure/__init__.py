"""Infrastructure layer for external geospatial services and adapters."""

from paridhi.infrastructure.factory import get_spatial_provider
from paridhi.infrastructure.google.adapter import GoogleSpatialAdapter

__all__ = ["GoogleSpatialAdapter", "get_spatial_provider"]
