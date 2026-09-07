"""Mock spatial provider for testing and offline development."""

import logging

from paridhi.domain.exceptions import GeocodingFailedError, ZeroPlacesFoundError
from paridhi.domain.models import Coordinates, Place
from paridhi.domain.ports import SpatialProvider

logger = logging.getLogger("paridhi.infrastructure.mock")

# Realistic offline places fixture (e.g. Paldi, Ahmedabad)
SAMPLE_PLACES: list[Place] = [
    Place(
        name="Jay Bhavani Vadapav",
        formatted_address="Paldi Cross Road, Paldi, Ahmedabad, Gujarat 380007",
        maps_url="https://maps.google.com/?cid=123456789012345",
        rating=4.3,
        user_rating_count=2450,
        location=Coordinates(latitude=23.0125, longitude=72.5635),
    ),
    Place(
        name="Shreeji Krupa Bombay Vadapav",
        formatted_address="Near Bhatta Circle, Paldi, Ahmedabad, Gujarat 380007",
        maps_url="https://maps.google.com/?cid=234567890123456",
        rating=4.5,
        user_rating_count=1820,
        location=Coordinates(latitude=23.0140, longitude=72.5610),
    ),
    Place(
        name="Gajanand Pauva & Vadapav Center",
        formatted_address="Fatehpura Road, Near Bhatta, Paldi, Ahmedabad 380007",
        maps_url="https://maps.google.com/?cid=345678901234567",
        rating=4.1,
        user_rating_count=940,
        location=Coordinates(latitude=23.0110, longitude=72.5650),
    ),
    Place(
        name="Karnavati Dabeli & Vadapav",
        formatted_address="Mahalaxmi Cross Road, Paldi, Ahmedabad, Gujarat 380007",
        maps_url="https://maps.google.com/?cid=456789012345678",
        rating=4.2,
        user_rating_count=1150,
        location=Coordinates(latitude=23.0165, longitude=72.5620),
    ),
]


class MockSpatialProvider(SpatialProvider):
    """Offline mock spatial provider implementing SpatialProvider interface."""

    def __init__(self, sample_places: list[Place] | None = None) -> None:
        self.places = sample_places if sample_places is not None else SAMPLE_PLACES

    async def geocode(self, location_name: str) -> Coordinates:
        """Mock geocoder returning known coordinates or fallback."""
        cleaned = location_name.strip().lower()
        if not cleaned:
            raise GeocodingFailedError(location_name, "Empty location provided")
        if "invalid" in cleaned or "unknown" in cleaned:
            raise GeocodingFailedError(location_name, "No matching location found")

        # Specific known coordinate mapping for testing
        if "bhatta" in cleaned or "paldi" in cleaned:
            return Coordinates(latitude=23.0128, longitude=72.5629)

        return Coordinates(latitude=23.0225, longitude=72.5714)

    async def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_meters: int,
    ) -> list[Place]:
        """Return sample places or filter by query keyword."""
        if "empty" in query.lower() or "nonexistent" in query.lower():
            raise ZeroPlacesFoundError(query=query, radius_meters=radius_meters)

        return list(self.places)
