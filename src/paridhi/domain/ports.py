"""Domain ports defining the abstract interfaces for geospatial providers."""

from typing import Protocol, runtime_checkable

from paridhi.domain.models import Coordinates, Place


@runtime_checkable
class SpatialProvider(Protocol):
    """Abstract interface (Port) for geospatial services following Ports & Adapters architecture.

    Allows plugging in diverse providers (Google Maps, OpenStreetMap/Nominatim, Mapbox, Radar)
    without mutating domain models or presentation logic.
    """

    async def geocode(self, location_name: str) -> Coordinates:
        """Resolve an address or informal neighborhood string into geographic coordinates.

        Args:
            location_name: Name of place, address, or neighborhood (e.g. 'Bhatta, Paldi').

        Returns:
            Coordinates: WGS 84 latitude and longitude.

        Raises:
            GeocodingFailedError: If location cannot be found or geocoding fails.
            ProviderUnavailableError: If the remote provider service is unreachable.
        """
        ...

    async def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_meters: int,
    ) -> list[Place]:
        """Search for points of interest within a circular perimeter.

        Args:
            query: Search prompt or category (e.g. 'vadapav shops').
            center: Geographic coordinates of the circular search center.
            radius_meters: Circular radius in meters.

        Returns:
            list[Place]: List of matching places.

        Raises:
            ZeroPlacesFoundError: If no places are found matching the criteria.
            ProviderUnavailableError: If the remote provider service is unreachable.
        """
        ...
