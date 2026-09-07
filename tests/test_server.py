"""Tests for Paridhi FastMCP server endpoints and tools."""

from typing import Any

import pytest
from fastmcp import FastMCP
from mcp.types import TextContent

from paridhi.core.config import Settings
from paridhi.infrastructure.mock import MockSpatialProvider
from paridhi.presentation.server import create_server


@pytest.fixture
def server() -> FastMCP:
    """Fixture providing a FastMCP server instance configured with MockSpatialProvider."""
    settings = Settings(
        server_name="ParidhiTest",
        server_version="0.1.0-test",
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = MockSpatialProvider()
    return create_server(settings=settings, provider=provider)


def get_response_text(result: Any) -> str:
    """Helper to extract text from FastMCP ToolResult."""
    assert result.content is not None
    item = result.content[0]
    assert isinstance(item, TextContent)
    return str(item.text)


@pytest.mark.asyncio
async def test_ping_tool(server: FastMCP) -> None:
    """Verify health-check ping tool returns healthy status."""
    result = await server.call_tool("ping", {})
    assert result.structured_content is not None
    assert result.structured_content["status"] == "healthy"
    assert result.structured_content["service"] == "ParidhiTest"
    assert result.structured_content["version"] == "0.1.0-test"


@pytest.mark.asyncio
async def test_discover_pois_with_location_string(server: FastMCP) -> None:
    """Verify discover_pois with informal origin string returns Markdown table with deep links."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "vadapav shops",
            "location": "Bhatta, Paldi",
            "radius_meters": 3000.0,
        },
    )
    text = get_response_text(result)
    assert "Discovered 'vadapav shops' within 3000m of 'Bhatta, Paldi'" in text
    assert "| Place Name | Address | Google Map location | Google Ratings |" in text
    assert "| **Jay Bhavani Vadapav** |" in text
    assert "[Pin](https://maps.google.com/?cid=123456789012345)" in text
    assert "[4.3 ★ (2,450)](https://maps.google.com/?cid=123456789012345)" in text


@pytest.mark.asyncio
async def test_discover_pois_with_coordinates(server: FastMCP) -> None:
    """Verify discover_pois with direct coordinates."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "street food",
            "latitude": 23.0128,
            "longitude": 72.5629,
            "radius_meters": 1500.0,
        },
    )
    text = get_response_text(result)
    assert "| Place Name | Address | Google Map location | Google Ratings |" in text
    assert "Jay Bhavani Vadapav" in text


@pytest.mark.asyncio
async def test_discover_pois_clamping_lower_bound(server: FastMCP) -> None:
    """Verify discover_pois clamps radius below 100m to 100m."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "food",
            "location": "Bhatta, Paldi",
            "radius_meters": 25.0,
        },
    )
    text = get_response_text(result)
    assert "within 100m of 'Bhatta, Paldi'" in text
    assert "adjusted from 25m to minimum 100m" in text


@pytest.mark.asyncio
async def test_discover_pois_clamping_upper_bound(server: FastMCP) -> None:
    """Verify discover_pois clamps radius above 50,000m to 50,000m."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "food",
            "location": "Bhatta, Paldi",
            "radius_meters": 75000.0,
        },
    )
    text = get_response_text(result)
    assert "within 50000m of 'Bhatta, Paldi'" in text
    assert "adjusted from 75000m to maximum 50000m" in text


@pytest.mark.asyncio
async def test_discover_pois_geocoding_failure_clean_message(server: FastMCP) -> None:
    """Verify unresolvable location returns friendly message without stack trace."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "food",
            "location": "UnknownInvalidPlace123",
        },
    )
    text = get_response_text(result)
    assert "⚠️ **Geocoding Error**" in text
    assert "Please check the location spelling" in text


@pytest.mark.asyncio
async def test_discover_pois_zero_results_clean_message(server: FastMCP) -> None:
    """Verify zero results query returns clean informational message."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "empty nonexistent query",
            "location": "Bhatta, Paldi",
        },
    )
    text = get_response_text(result)
    assert "ℹ️ **No Places Found**" in text


@pytest.mark.asyncio
async def test_discover_pois_missing_origin(server: FastMCP) -> None:
    """Verify missing origin returns clean input error message."""
    result = await server.call_tool(
        "discover_pois",
        {
            "query": "food",
        },
    )
    text = get_response_text(result)
    assert "⚠️ **Invalid Input**" in text
