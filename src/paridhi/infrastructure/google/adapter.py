"""Google Maps Platform adapter implementing SpatialProvider protocol.

Integrates:
1. Google Geocoding API: Resolves text location strings to coordinates.
2. Google Places API (New) Text Search: Discovers POIs within circular spatial perimeters
   using explicit field masks to minimize API consumption.
"""

import logging
import math
from typing import Any

import httpx

from paridhi.core.config import Settings, get_settings
from paridhi.domain.exceptions import (
    GeocodingFailedError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderQuotaExceededError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ZeroPlacesFoundError,
)
from paridhi.domain.models import Coordinates, Place
from paridhi.domain.ports import SpatialProvider

logger = logging.getLogger("paridhi.infrastructure.google")

# Explicit field mask to fetch only required fields and minimize billing consumption
PLACES_FIELD_MASK = (
    "places.displayName,"
    "places.formattedAddress,"
    "places.googleMapsUri,"
    "places.rating,"
    "places.userRatingCount,"
    "places.location"
)


def haversine_distance_meters(c1: Coordinates, c2: Coordinates) -> float:
    """Calculate great-circle distance between two coordinates in meters."""
    r = 6_371_000.0
    phi1 = math.radians(c1.latitude)
    phi2 = math.radians(c2.latitude)
    delta_phi = math.radians(c2.latitude - c1.latitude)
    delta_lambda = math.radians(c2.longitude - c1.longitude)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class GoogleSpatialAdapter(SpatialProvider):
    """Google Maps Platform client conforming to the SpatialProvider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._api_key = api_key or self._settings.google_maps_api_key
        self._external_client = client
        self._timeout = self._settings.http_timeout_seconds

    def _ensure_api_key(self) -> str:
        """Validate presence of Google Maps API key."""
        if not self._api_key or not self._api_key.strip():
            raise ProviderAuthenticationError(
                "Google Maps API key is missing. Please set GOOGLE_MAPS_API_KEY or GOOGLE_API_KEY "
                "in your environment or .env file."
            )
        return self._api_key.strip()

    async def _get_client(self) -> httpx.AsyncClient:
        """Return the injected HTTP client or create a new transient one."""
        if self._external_client is not None:
            return self._external_client
        return httpx.AsyncClient(timeout=self._timeout)

    async def geocode(self, location_name: str) -> Coordinates:
        """Resolve an address or neighborhood string into geographic coordinates."""
        key = self._ensure_api_key()
        cleaned_location = location_name.strip()
        if not cleaned_location:
            raise GeocodingFailedError(location_name, "Empty location name provided")

        url = self._settings.geocoding_base_url
        params = {"address": cleaned_location, "key": key}

        logger.info("Geocoding location '%s' via Google Geocoding API", cleaned_location)

        try:
            if self._external_client is not None:
                response = await self._external_client.get(url, params=params)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, params=params)
        except httpx.TimeoutException as exc:
            logger.error("Timeout connecting to Google Geocoding API: %s", exc)
            raise ProviderTimeoutError(
                f"Geocoding request timed out for '{cleaned_location}'"
            ) from exc
        except httpx.NetworkError as exc:
            logger.error("Network error connecting to Google Geocoding API: %s", exc)
            raise ProviderConnectionError(
                f"Failed to connect to Google Geocoding API: {exc}"
            ) from exc

        if response.status_code != 200:
            logger.error(
                "Google Geocoding API HTTP error %d: %s", response.status_code, response.text
            )
            if response.status_code in (401, 403):
                raise ProviderAuthenticationError("Invalid or unauthorized Google Maps API key")
            if response.status_code == 429:
                raise ProviderQuotaExceededError("Google Maps Geocoding API rate limit exceeded")
            raise ProviderUnavailableError(f"Google Geocoding API HTTP {response.status_code}")

        data: dict[str, Any] = response.json()
        status = data.get("status")

        if status == "OK":
            results = data.get("results", [])
            if not results:
                raise GeocodingFailedError(cleaned_location, "No results returned")
            location = results[0]["geometry"]["location"]
            coords = Coordinates(latitude=location["lat"], longitude=location["lng"])
            logger.info(
                "Geocoded '%s' to (%f, %f)", cleaned_location, coords.latitude, coords.longitude
            )
            return coords

        if status == "ZERO_RESULTS":
            raise GeocodingFailedError(cleaned_location, "No matching location found")
        if status in ("OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED"):
            raise ProviderQuotaExceededError("Google Maps Geocoding API quota exceeded")
        if status == "REQUEST_DENIED":
            error_message = data.get("error_message", "Request denied by Google Maps API")
            raise ProviderAuthenticationError(
                f"Google Geocoding API rejected request: {error_message}"
            )

        error_message = data.get("error_message", status)
        raise GeocodingFailedError(
            cleaned_location, f"Google Geocoding API status '{error_message}'"
        )

    async def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_meters: int,
    ) -> list[Place]:
        """Search for POIs within circular spatial bounds using Google Places API (New)."""
        key = self._ensure_api_key()
        url = self._settings.places_search_base_url

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": PLACES_FIELD_MASK,
        }

        payload: dict[str, Any] = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": center.latitude,
                        "longitude": center.longitude,
                    },
                    "radius": float(radius_meters),
                }
            },
            "maxResultCount": 20,
        }

        logger.info(
            "Searching Places API (New) for '%s' near (%f, %f) within %dm",
            query,
            center.latitude,
            center.longitude,
            radius_meters,
        )

        try:
            if self._external_client is not None:
                response = await self._external_client.post(url, headers=headers, json=payload)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("Timeout contacting Google Places API: %s", exc)
            raise ProviderTimeoutError(f"Places search timed out for query '{query}'") from exc
        except httpx.NetworkError as exc:
            logger.error("Network error contacting Google Places API: %s", exc)
            raise ProviderConnectionError(f"Failed to connect to Google Places API: {exc}") from exc

        if response.status_code != 200:
            logger.error("Google Places API error %d: %s", response.status_code, response.text)
            if response.status_code in (401, 403):
                raise ProviderAuthenticationError("Invalid or unauthorized Google Maps API key")
            if response.status_code == 429:
                raise ProviderQuotaExceededError("Google Places API rate limit or quota exceeded")
            raise ProviderUnavailableError(
                f"Google Places API returned HTTP {response.status_code}"
            )

        data = response.json()
        places_raw: list[dict[str, Any]] = data.get("places", [])

        if not places_raw:
            logger.info("No places found for query '%s' within %dm", query, radius_meters)
            raise ZeroPlacesFoundError(query=query, radius_meters=radius_meters)

        places: list[Place] = []
        for p in places_raw:
            name = p.get("displayName", {}).get("text", "Unknown Place")
            formatted_address = p.get("formattedAddress", "N/A")
            maps_url = p.get("googleMapsUri")
            rating = p.get("rating")
            user_rating_count = p.get("userRatingCount")

            loc_data = p.get("location", {})
            place_coords = None
            if "latitude" in loc_data and "longitude" in loc_data:
                place_coords = Coordinates(
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                )

            # Spatial boundary check: filter out places outside the circular perimeter
            if place_coords is not None:
                distance = haversine_distance_meters(center, place_coords)
                if distance > radius_meters * 1.15:
                    logger.debug(
                        "Place '%s' at %.0fm filtered (outside %dm radius)",
                        name,
                        distance,
                        radius_meters,
                    )
                    continue

            places.append(
                Place(
                    name=name,
                    formatted_address=formatted_address,
                    maps_url=maps_url,
                    rating=rating,
                    user_rating_count=user_rating_count,
                    location=place_coords,
                )
            )

        if not places:
            logger.info("No places within radius %dm for query '%s'", radius_meters, query)
            raise ZeroPlacesFoundError(query=query, radius_meters=radius_meters)

        logger.info("Retrieved %d places from Google Places API", len(places))
        return places
