# Domain Package

## Overview
Contains the core business domain models, geospatial entities, data transfer schemas, abstract service ports, and the typed exception hierarchy. Strictly isolated from external infrastructure dependencies.

## Interface
- `[ports.py:SpatialProvider]`: Runtime-checkable abstract protocol defining geospatial operations:
  - `[ports.py:SpatialProvider.geocode]`: Resolves address string to `Coordinates`.
  - `[ports.py:SpatialProvider.search_places]`: Discovers places within a circular perimeter.
- `[models.py:Coordinates]`: Immutable WGS 84 geographic coordinate representation (`latitude`, `longitude`).
- `[models.py:CircularBound]`: Immutable circular spatial bounding perimeter (`center`, `radius_meters`).
- `[models.py:Place]`: Immutable point of interest entity with deep link formatting properties (`map_location_link`, `ratings_link`).
- `[models.py:clamp_radius]`: Clamping function enforcing `[100.0, 50,000.0]` meter bounds on search radii.
- `[models.py:format_places_table]`: Renders collections of `Place` instances into GitHub-flavored Markdown tables.
- `[models.py:DiscoverPOIsRequest]`: Validates inbound tool arguments, origin coordinates/address requirements, and clamped search bounds.
- `[models.py:HealthCheckResponse]`: Schema for server operational health payload.
- `[exceptions.py:ParidhiError]`: Base exception for all Paridhi domain, validation, and provider failures.
- `[exceptions.py:GeocodingFailedError]`: Raised when address resolution yields no matches.
- `[exceptions.py:ZeroPlacesFoundError]`: Raised when no places match search criteria within the spatial bounds.
- `[exceptions.py:ProviderError]`: Base exception for remote provider failures (`ProviderAuthenticationError`, `ProviderQuotaExceededError`, `ProviderUnavailableError`, `ProviderTimeoutError`, `ProviderConnectionError`).

## Invariants
- `[models.py:Coordinates]`: Latitude strictly constrained to `[-90.0, 90.0]`; longitude strictly constrained to `[-180.0, 180.0]`.
- `[models.py:DiscoverPOIsRequest.validate_spatial_origin]`: Either `location` (non-empty string) or both `latitude` and `longitude` must be provided; raises `ValueError` otherwise.
- `[models.py:DiscoverPOIsRequest.limit]`: Constrained to integer range `[1, 20]`.
- `[models.py:clamp_radius]`: Clamps radii less than 100m to 100m, and greater than 50,000m to 50,000m.

## Side Effects
- `["None"]`

## Verification
- Run: `uv run pytest tests/test_domain_models.py`
