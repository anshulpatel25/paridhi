"""Tests for Paridhi domain models and validation."""

import pytest
from pydantic import ValidationError

from paridhi.domain.models import (
    CircularBound,
    Coordinates,
    DiscoverPOIsRequest,
    HealthCheckResponse,
    Place,
    PlaceSearchRequest,
    PointOfInterest,
    clamp_radius,
    format_places_table,
)


def test_valid_coordinates() -> None:
    """Test valid coordinate instantiations."""
    coords = Coordinates(latitude=12.9716, longitude=77.5946)
    assert coords.latitude == 12.9716
    assert coords.longitude == 77.5946


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (90.1, 0.0),
        (-90.1, 0.0),
        (0.0, 180.1),
        (0.0, -180.1),
    ],
)
def test_invalid_coordinates(lat: float, lon: float) -> None:
    """Test out-of-bounds coordinates raise validation error."""
    with pytest.raises(ValidationError):
        Coordinates(latitude=lat, longitude=lon)


def test_clamp_radius_function() -> None:
    """Test standalone clamp_radius helper."""
    assert clamp_radius(50.0) == 100.0
    assert clamp_radius(100.0) == 100.0
    assert clamp_radius(2500.0) == 2500.0
    assert clamp_radius(50000.0) == 50000.0
    assert clamp_radius(99999.0) == 50000.0


@pytest.mark.parametrize(
    ("input_radius", "expected_radius"),
    [
        (10.0, 100.0),  # Clamped below min
        (99.9, 100.0),  # Clamped below min
        (100.0, 100.0),  # Exact min
        (500.0, 500.0),  # Valid within range
        (10000.0, 10000.0),  # Valid within range
        (50000.0, 50000.0),  # Exact max
        (50001.0, 50000.0),  # Clamped above max
        (250000.0, 50000.0),  # Clamped above max
    ],
)
def test_circular_bound_clamping(input_radius: float, expected_radius: float) -> None:
    """Test CircularBound clamps radius correctly."""
    bound = CircularBound(
        center=Coordinates(latitude=28.6139, longitude=77.2090),
        radius_meters=input_radius,
    )
    assert bound.radius_meters == expected_radius


def test_discover_pois_request_clamping() -> None:
    """Test DiscoverPOIsRequest enforces radius clamping."""
    req_low = DiscoverPOIsRequest(
        query="vadapav",
        latitude=0.0,
        longitude=0.0,
        radius_meters=15.0,
    )
    assert req_low.radius_meters == 100.0

    req_high = DiscoverPOIsRequest(
        query="vadapav",
        latitude=0.0,
        longitude=0.0,
        radius_meters=80000.0,
    )
    assert req_high.radius_meters == 50000.0

    bound = req_low.to_circular_bound()
    assert bound.radius_meters == 100.0
    assert bound.center.latitude == 0.0


def test_discover_pois_request_with_location_string() -> None:
    """Test DiscoverPOIsRequest accepting informal neighborhood string."""
    req = DiscoverPOIsRequest(
        query="vadapav shops",
        location="Bhatta, Paldi",
        radius_meters=3000.0,
    )
    assert req.location == "Bhatta, Paldi"
    assert req.radius_meters == 3000.0
    assert req.query == "vadapav shops"


def test_discover_pois_request_missing_origin() -> None:
    """Test DiscoverPOIsRequest rejects when neither location nor coords provided."""
    with pytest.raises(ValidationError):
        DiscoverPOIsRequest(query="coffee")


def test_place_model_and_formatting() -> None:
    """Test Place entity markdown formatting for deep links."""
    place = Place(
        name="Jay Bhavani Vadapav",
        formatted_address="Paldi Cross Road, Ahmedabad",
        maps_url="https://maps.google.com/?cid=123456789012345",
        rating=4.3,
        user_rating_count=2450,
        location=Coordinates(latitude=23.0125, longitude=72.5635),
    )
    assert place.map_location_link == "[Pin](https://maps.google.com/?cid=123456789012345)"
    assert place.ratings_link == "[4.3 ★ (2,450)](https://maps.google.com/?cid=123456789012345)"

    table = format_places_table([place])
    assert "| **Jay Bhavani Vadapav** |" in table
    assert "[Pin](https://maps.google.com/?cid=123456789012345)" in table
    assert "[4.3 ★ (2,450)](https://maps.google.com/?cid=123456789012345)" in table


def test_place_without_ratings() -> None:
    """Test Place formatting when ratings are missing."""
    place = Place(
        name="Hidden Gems",
        formatted_address="Ahmedabad",
        location=Coordinates(latitude=23.0, longitude=72.0),
    )
    assert place.ratings_link == "N/A"
    assert place.map_location_link == "[Pin](https://maps.google.com/?q=23.0,72.0)"


def test_place_search_request_clamping() -> None:
    """Test PlaceSearchRequest clamps radius."""
    req = PlaceSearchRequest(
        query="vadapav",
        center=Coordinates(latitude=23.0, longitude=72.0),
        radius_meters=50,
    )
    assert req.radius_meters == 100


def test_point_of_interest_model() -> None:
    """Test PointOfInterest model creation."""
    poi = PointOfInterest(
        id="poi-001",
        name="India Gate",
        location=Coordinates(latitude=28.6129, longitude=77.2295),
        category="monument",
        address="Rajpath, India Gate, New Delhi",
        distance_meters=350.5,
        tags={"wheelchair_accessible": True},
    )
    assert poi.id == "poi-001"
    assert poi.name == "India Gate"
    assert poi.distance_meters == 350.5


def test_health_check_response() -> None:
    """Test HealthCheckResponse model."""
    res = HealthCheckResponse(version="0.1.0")
    assert res.status == "healthy"
    assert res.service == "Paridhi"
    assert res.version == "0.1.0"
    assert res.timestamp is not None
