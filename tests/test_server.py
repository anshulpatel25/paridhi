"""Tests for Paridhi FastMCP server endpoints and tools."""

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from paridhi.core.config import Settings
from paridhi.presentation.server import create_server


@pytest.fixture
def server() -> FastMCP:
    """Fixture providing a fresh FastMCP server instance."""
    settings = Settings(
        server_name="ParidhiTest",
        server_version="0.1.0-test",
    )
    return create_server(settings)


@pytest.mark.asyncio
async def test_ping_tool(server: FastMCP) -> None:
    """Verify health-check ping tool returns healthy status."""
    result = await server.call_tool("ping", {})
    assert result.structured_content is not None
    assert result.structured_content["status"] == "healthy"
    assert result.structured_content["service"] == "ParidhiTest"
    assert result.structured_content["version"] == "0.1.0-test"


@pytest.mark.asyncio
async def test_discover_pois_default(server: FastMCP) -> None:
    """Verify discover_pois tool with default parameters."""
    result = await server.call_tool(
        "discover_pois",
        {"latitude": 19.0760, "longitude": 72.8777},
    )
    assert result.structured_content is not None
    content = result.structured_content
    assert content["radius_meters"] == 1000.0
    assert content["center"]["latitude"] == 19.0760
    assert content["center"]["longitude"] == 72.8777
    assert content["total_found"] == 0
    assert isinstance(content["pois"], list)


@pytest.mark.asyncio
async def test_discover_pois_clamping_lower_bound(server: FastMCP) -> None:
    """Verify discover_pois clamps radius values below 100m to 100m."""
    result = await server.call_tool(
        "discover_pois",
        {"latitude": 19.0760, "longitude": 72.8777, "radius_meters": 25.0},
    )
    assert result.structured_content is not None
    content = result.structured_content
    assert content["radius_meters"] == 100.0
    assert "clamped" in content["message"].lower()


@pytest.mark.asyncio
async def test_discover_pois_clamping_upper_bound(server: FastMCP) -> None:
    """Verify discover_pois clamps radius values above 50,000m to 50,000m."""
    result = await server.call_tool(
        "discover_pois",
        {"latitude": 19.0760, "longitude": 72.8777, "radius_meters": 75000.0},
    )
    assert result.structured_content is not None
    content = result.structured_content
    assert content["radius_meters"] == 50000.0
    assert "clamped" in content["message"].lower()


@pytest.mark.asyncio
async def test_discover_pois_invalid_coordinate(server: FastMCP) -> None:
    """Verify discover_pois rejects out-of-bounds latitude."""
    with pytest.raises(ToolError):
        await server.call_tool(
            "discover_pois",
            {"latitude": 95.0, "longitude": 72.8777},
        )
