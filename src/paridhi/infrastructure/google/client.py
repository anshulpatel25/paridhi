"""Google Maps Platform client alias."""

from paridhi.infrastructure.google.adapter import GoogleSpatialAdapter

# Alias for backwards-compatibility with naming conventions
GoogleSpatialClient = GoogleSpatialAdapter

__all__ = ["GoogleSpatialAdapter", "GoogleSpatialClient"]
