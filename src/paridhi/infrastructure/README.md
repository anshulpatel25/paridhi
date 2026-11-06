# Infrastructure Package

## Overview
Houses external integrations, provider adapters, and dependency injection factories conforming to the `SpatialProvider` domain port. Contains both production adapters and deterministic offline mock providers.

## Interface
- `[factory.py:get_spatial_provider]`: Factory function resolving and instantiating a `SpatialProvider` implementation (`mock` or `google`) based on application settings.
- `[mock.py:MockSpatialProvider]`: Offline mock provider implementing `SpatialProvider` for local testing without external API credentials.
- `[mock.py:SAMPLE_PLACES]`: Static fixture dataset of verified sample `Place` entities in Ahmedabad.
- [Google Maps Platform Adapter](./google/README.md): Production adapter package integrating Google Geocoding and Places API (New).

## Invariants
- `[factory.py:get_spatial_provider]`: Instantiates `MockSpatialProvider` when `settings.spatial_provider == "mock"`, otherwise returns `GoogleSpatialAdapter` (default fallback for unrecognized provider names).
- `[mock.py:MockSpatialProvider.geocode]`: Empty location string or string containing `"invalid"` / `"unknown"` raises `GeocodingFailedError`.
- `[mock.py:MockSpatialProvider.search_places]`: Query containing `"empty"` or `"nonexistent"` raises `ZeroPlacesFoundError`.

## Side Effects
- `[factory.py:get_spatial_provider]`: Emits log messages to logger `paridhi.infrastructure.factory`.
- `[mock.py:MockSpatialProvider]`: None (in-memory fixture responses without network calls).

## Verification
- Run: `uv run pytest tests/test_google_adapter.py tests/test_server.py`
