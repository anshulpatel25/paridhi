# Google Maps Infrastructure Adapter

## Overview
Provides concrete geospatial adapter implementations interfacing with Google Maps Platform services (Geocoding API and Google Places API New Text Search). Enforces perimeter validation via Haversine filtering and billing optimization via explicit field masking.

## Interface
- `[adapter.py:GoogleSpatialAdapter]`: Primary adapter class conforming to `SpatialProvider` protocol.
  - `[adapter.py:GoogleSpatialAdapter.geocode]`: Resolves text location strings to `Coordinates` using Google Maps Geocoding API.
  - `[adapter.py:GoogleSpatialAdapter.search_places]`: Searches POIs within circular spatial bounds using Google Places API (New).
- `[client.py:GoogleSpatialClient]`: Backward-compatibility type alias for `GoogleSpatialAdapter`.
- `[adapter.py:haversine_distance_meters]`: Utility function calculating great-circle distance between coordinates.
- `[adapter.py:PLACES_FIELD_MASK]`: Explicit field mask limiting Places API payloads to essential fields (`displayName`, `formattedAddress`, `googleMapsUri`, `rating`, `userRatingCount`, `location`).

## Invariants
- `[adapter.py:GoogleSpatialAdapter._ensure_api_key]`: API key must be provided via constructor or settings; raises `ProviderAuthenticationError` if missing or whitespace.
- `[adapter.py:GoogleSpatialAdapter.geocode]`: `location_name` must be non-empty after whitespace stripping; raises `GeocodingFailedError` on empty strings.
- `[adapter.py:GoogleSpatialAdapter.search_places]`: Outlying candidate places with distance exceeding `radius_meters * 1.15` are discarded by Haversine perimeter filtering.
- `[adapter.py:GoogleSpatialAdapter.search_places]`: Maximum upstream candidate fetch size is fixed to 20 (`maxResultCount=20`).

## Side Effects
- `[adapter.py:GoogleSpatialAdapter.geocode]`: Outbound asynchronous HTTP GET request to `settings.geocoding_base_url` (`https://maps.googleapis.com/maps/api/geocode/json`) via `httpx.AsyncClient`.
- `[adapter.py:GoogleSpatialAdapter.search_places]`: Outbound asynchronous HTTP POST request to `settings.places_search_base_url` (`https://places.googleapis.com/v1/places:searchText`) via `httpx.AsyncClient`.

## Verification
- Run: `uv run pytest tests/test_google_adapter.py`
