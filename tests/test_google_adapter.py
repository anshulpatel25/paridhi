"""Unit tests for GoogleSpatialAdapter using mock HTTP transport."""

import json

import httpx
import pytest

from paridhi.core.config import Settings
from paridhi.domain.exceptions import (
    GeocodingFailedError,
    ProviderAuthenticationError,
    ProviderQuotaExceededError,
    ProviderTimeoutError,
    ZeroPlacesFoundError,
)
from paridhi.domain.models import Coordinates
from paridhi.infrastructure.google.adapter import GoogleSpatialAdapter


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        google_maps_api_key="mock-api-key-12345",
        _env_file=None,  # type: ignore[call-arg]
    )


@pytest.mark.asyncio
async def test_missing_api_key_raises_auth_error() -> None:
    """Verify adapter raises ProviderAuthenticationError if key is missing."""
    settings = Settings(google_maps_api_key=None, _env_file=None)  # type: ignore[call-arg]
    adapter = GoogleSpatialAdapter(api_key=None, settings=settings)

    with pytest.raises(ProviderAuthenticationError):
        await adapter.geocode("Bhatta, Paldi")


@pytest.mark.asyncio
async def test_geocode_success(mock_settings: Settings) -> None:
    """Verify successful geocoding resolves coordinates."""
    mock_payload = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "Bhatta, Paldi, Ahmedabad, Gujarat 380007, India",
                "geometry": {
                    "location": {"lat": 23.0128, "lng": 72.5629},
                },
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "address=Bhatta%2C+Paldi" in str(request.url) or "address=Bhatta" in str(request.url)
        assert "key=mock-api-key-12345" in str(request.url)
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        coords = await adapter.geocode("Bhatta, Paldi")
        assert coords.latitude == 23.0128
        assert coords.longitude == 72.5629


@pytest.mark.asyncio
async def test_geocode_zero_results(mock_settings: Settings) -> None:
    """Verify ZERO_RESULTS status raises GeocodingFailedError."""
    mock_payload = {"status": "ZERO_RESULTS", "results": []}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        with pytest.raises(GeocodingFailedError):
            await adapter.geocode("NonExistentUnknownLocation999")


@pytest.mark.asyncio
async def test_geocode_quota_exceeded(mock_settings: Settings) -> None:
    """Verify OVER_QUERY_LIMIT status raises ProviderQuotaExceededError."""
    mock_payload = {"status": "OVER_QUERY_LIMIT", "error_message": "Quota exceeded"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        with pytest.raises(ProviderQuotaExceededError):
            await adapter.geocode("Bhatta, Paldi")


@pytest.mark.asyncio
async def test_search_places_success(mock_settings: Settings) -> None:
    """Verify Places API (New) parsing and field masking."""
    mock_payload = {
        "places": [
            {
                "displayName": {"text": "Jay Bhavani Vadapav", "languageCode": "en"},
                "formattedAddress": "Paldi Cross Road, Ahmedabad",
                "googleMapsUri": "https://maps.google.com/?cid=123456789012345",
                "rating": 4.3,
                "userRatingCount": 2450,
                "location": {"latitude": 23.0125, "longitude": 72.5635},
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-Api-Key"] == "mock-api-key-12345"
        assert "places.displayName" in request.headers["X-Goog-FieldMask"]
        body = json.loads(request.content.decode("utf-8"))
        assert "locationBias" in body
        assert "circle" in body["locationBias"]
        assert body["locationBias"]["circle"]["radius"] == 3000.0
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        places = await adapter.search_places(
            query="vadapav shops",
            center=Coordinates(latitude=23.0128, longitude=72.5629),
            radius_meters=3000,
        )
        assert len(places) == 1
        place = places[0]
        assert place.name == "Jay Bhavani Vadapav"
        assert place.rating == 4.3
        assert place.user_rating_count == 2450
        assert place.map_location_link == "[Pin](https://maps.google.com/?cid=123456789012345)"
        assert place.ratings_link == "[4.3 ★ (2,450)](https://maps.google.com/?cid=123456789012345)"


@pytest.mark.asyncio
async def test_search_places_zero_results(mock_settings: Settings) -> None:
    """Verify empty places list raises ZeroPlacesFoundError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"places": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        with pytest.raises(ZeroPlacesFoundError):
            await adapter.search_places(
                query="astronaut food",
                center=Coordinates(latitude=23.0128, longitude=72.5629),
                radius_meters=1000,
            )


@pytest.mark.asyncio
async def test_timeout_maps_to_provider_timeout_error(mock_settings: Settings) -> None:
    """Verify httpx.TimeoutException maps to ProviderTimeoutError."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = GoogleSpatialAdapter(client=client, settings=mock_settings)
        with pytest.raises(ProviderTimeoutError):
            await adapter.geocode("Bhatta, Paldi")
