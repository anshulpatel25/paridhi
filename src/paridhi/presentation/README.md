# Presentation Package

## Overview
Exposes Paridhi capabilities over the Model Context Protocol (MCP) using `FastMCP`. Configures endpoints, registers tool handlers, validates incoming requests, handles errors gracefully, and formats output responses as Markdown tables.

## Interface
- `[server.py:create_server]`: Factory creating a configured `FastMCP` instance with dependency injection for `Settings` and `SpatialProvider`.
- `[server.py:mcp]`: Default module-level `FastMCP` instance initialized with default settings and provider.
- `[server.py:root_info]`: HTTP route `GET /` returning JSON service status and MCP endpoint information.
- `[server.py:ping]`: FastMCP tool verifying operational health status.
- `[server.py:discover_pois]`: FastMCP tool executing circular perimeter searches and returning formatted Markdown tables with deep links.

## Invariants
- `[server.py:discover_pois]`: Traps domain exceptions (`GeocodingFailedError`, `ZeroPlacesFoundError`, `ProviderAuthenticationError`, `ProviderQuotaExceededError`, `ProviderUnavailableError`, `ParidhiError`) and converts them into user-facing Markdown alert strings (`⚠️`, `ℹ️`) rather than leaking stack traces.
- `[server.py:discover_pois]`: Detects if requested radius was adjusted by clamping and appends a human-readable adjustment note to the rendered table.
- `[server.py:create_server]`: Injects `SpatialProvider` protocol instance into handlers, maintaining strict decoupling from concrete transport and infrastructure implementations.

## Side Effects
- `[server.py:discover_pois]`: Delegates geocoding and search queries to the injected `SpatialProvider` (incurring network I/O in production).
- `[server.py:create_server]`: Registers FastMCP route handlers and tool schemas.
- `[server.py]`: Writes logs to logger `paridhi.server`.

## Verification
- Run: `uv run pytest tests/test_server.py`
