# AGENTS.md — Operational Manual for AI Agents

> **Context**: This document provides absolute instructions, architectural contracts, development procedures, and synchronization protocols for AI coding assistants (such as Antigravity, Cursor, Claude Code, and Copilot) and human contributors working within the **Paridhi** codebase.

---

## 1. Project Mission & Identity

**Paridhi** (*परिधि* — Sanskrit for *perimeter*, *circumference*, or *boundary*) is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server built with Python and [FastMCP](https://github.com/jlowin/fastmcp). It provides spatial boundary enforcement and points of interest (POI) discovery with Google Maps Platform integration (Geocoding API & Places API New).

### Core Design Principles
1. **Hexagonal Architecture (Ports & Adapters)**: Business logic and spatial domain concepts are decoupled from upstream geospatial APIs and transport protocols.
2. **Deterministic Spatial Bounds**: Radii are strictly validated and clamped to `[100m, 50,000m]`.
3. **Billing Efficiency**: Geospatial queries use explicit field masks (`PLACES_FIELD_MASK`) to minimize Google Maps Platform API consumption.
4. **Resilience over Failure**: Upstream errors (quota, 404, network timeouts, auth errors) are captured into typed domain exceptions and presented gracefully to MCP clients without exposing stack traces.
5. **Strict Type Safety**: Full strict typing verified with `mypy --strict` and modern Python 3.11+ constructs.
6. **`uv` as Single Source of Truth**: All environment provisioning, dependency locking, and test runs use `uv`.
7. **Permissive Open-Source Licensing**: The codebase is strictly and uniformly licensed under the MIT License (`LICENSE`, `pyproject.toml`, `README.md`, and OCI container metadata).

---

## 2. Mandatory Documentation Synchronization Mandate

> [!IMPORTANT]
> **CRITICAL AGENT PROTOCOL: CONTINUOUS DOCUMENTATION SYNCHRONIZATION**
>
> Whenever ANY functionality in this codebase is:
> - **Added** (e.g., new tool, provider adapter, config variable, CLI option, domain schema field)
> - **Removed** (e.g., deleted endpoint, deprecated model property)
> - **Updated** (e.g., modified tool arguments, revised clamping thresholds, changed output formatting)
>
> **You MUST update both `README.md` and `AGENTS.md` in the exact same task/commit before completing your work.**
>
> Specifically:
> 1. **`README.md`**: Update user-facing tool signatures, parameters, configuration tables, and Mermaid sequence diagrams.
> 2. **`AGENTS.md`**: Update architectural contracts, tool manifests, domain schemas, error handling matrices, and development checklists.
> 3. Verify compliance by running `uv run pytest tests/test_docs_sync.py`.

---

## 3. Repository Architecture & Layout

```text
paridhi/
├── .dockerignore                               # Files excluded from Docker container builds
├── .env.example                                # Template for configuration & API keys
├── .python-version                             # Python runtime pinned (3.14)
├── Dockerfile                                  # Production multi-stage OCI container image definition
├── pyproject.toml                              # Packaging, dependencies, and tool settings
├── uv.lock                                     # Deterministic lockfile managed by uv
├── LICENSE                                     # MIT License definition
├── RELEASE.md                                  # Release lifecycle & CI/CD deployment guide
├── README.md                                   # User documentation with GitHub-rendered Mermaid diagrams
├── AGENTS.md                                   # Agent operational specification (this file)
├── src/
│   └── paridhi/
│       ├── __init__.py                         # Package exports and __version__
│       ├── py.typed                            # PEP 561 marker for static type checkers
│       ├── main.py                             # CLI entrypoint (FastMCP runner with stdio, http, sse)
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py                       # pydantic-settings Settings model & singleton
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── exceptions.py                   # Typed domain error hierarchy (ParidhiError)
│       │   ├── models.py                       # Coordinates, CircularBound, Place, DiscoverPOIsRequest
│       │   └── ports.py                        # SpatialProvider Protocol (Port interface)
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── factory.py                      # SpatialProvider dependency-injection factory
│       │   ├── mock.py                         # MockSpatialProvider for offline tests and fixture data
│       │   └── google/
│       │       ├── __init__.py
│       │       ├── adapter.py                  # GoogleSpatialAdapter (Geocoding & Places API New)
│       │       └── client.py                   # Client backward-compatibility alias
│       └── presentation/
│           ├── __init__.py
│           └── server.py                       # FastMCP server definition & @server.tool handlers
└── tests/
    ├── __init__.py
    ├── test_config.py                          # Configuration parsing & validation tests
    ├── test_domain_models.py                   # Domain schemas, clamping, and table formatting tests
    ├── test_google_adapter.py                  # Google adapter unit tests with mocked httpx transport
    ├── test_server.py                          # End-to-end tool integration tests with Mock provider
    └── test_docs_sync.py                       # Automated test ensuring README & AGENTS remain in sync
```

---

## 4. Component Responsibilities & Contracts

### 4.1. Presentation Layer (`src/paridhi/presentation/server.py`)
- Instantiates `FastMCP(name=..., instructions=...)`.
- Injects `SpatialProvider` via `create_server(settings, provider)`.
- Implements tool handlers:
  - `ping() -> HealthCheckResponse`
  - `discover_pois(query, location, latitude, longitude, radius_meters, limit) -> str`
- Implements custom informational landing route `GET /`.
- Translates domain exceptions into human-friendly Markdown error notices (`⚠️`, `ℹ️`) instead of bubbling raw unhandled exceptions.

### 4.2. Domain Layer (`src/paridhi/domain/`)
- **`ports.py`**: Defines `SpatialProvider` protocol with:
  ```python
  async def geocode(self, location_name: str) -> Coordinates: ...
  async def search_places(
      self, query: str, center: Coordinates, radius_meters: int
  ) -> list[Place]: ...
  ```
- **`models.py`**:
  - `Coordinates`: Immutable lat/lng representation.
  - `CircularBound`: Geometric center and radius with clamping.
  - `Place`: Discovered entity with deep-link properties (`map_location_link`, `ratings_link`).
  - `format_places_table(places: list[Place]) -> str`: Formats results into GitHub-compatible Markdown tables.
  - `DiscoverPOIsRequest`: Validates input arguments, ensures either `location` or coords are passed, clamps radius to `[100m, 50000m]`.
- **`exceptions.py`**:
  - `ParidhiError` (base)
  - `GeocodingFailedError`
  - `ZeroPlacesFoundError`
  - `ProviderAuthenticationError`
  - `ProviderQuotaExceededError`
  - `ProviderUnavailableError`
  - `ProviderTimeoutError`
  - `ProviderConnectionError`

### 4.3. Infrastructure Layer (`src/paridhi/infrastructure/`)
- **`factory.py`**: Selects spatial provider implementation based on `settings.spatial_provider`.
- **`google/adapter.py`**:
  - `GoogleSpatialAdapter` connects to Google Geocoding API and Google Places API (New) Text Search (`places.googleapis.com/v1/places:searchText`).
  - Explicit `X-Goog-FieldMask` header ensures lean data transfer.
  - Computes `haversine_distance_meters` to enforce circular spatial perimeter and filter out outliers returned by upstream broad text search.
- **`mock.py`**:
  - `MockSpatialProvider` provides deterministic mock results for offline local runs and automated tests.

### 4.4. Configuration Layer (`src/paridhi/core/config.py`)
- Loads settings from environment variables prefixed with `PARIDHI_` (or `.env` file).
- Supports standard aliases for `GOOGLE_MAPS_API_KEY` / `GOOGLE_API_KEY`.
- Provides caching via `@lru_cache` in `get_settings()`.

---

## 5. Tool Specifications Manifest

| Tool Name | Purpose | Key Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| `ping` | Operational health check | None | JSON `HealthCheckResponse` (`status`, `service`, `version`, `timestamp`) |
| `discover_pois` | Spatial POI discovery | `query: str`<br/>`location: str \| None`<br/>`latitude: float \| None`<br/>`longitude: float \| None`<br/>`radius_meters: float` (100–50000)<br/>`limit: int` (1–20) | Markdown table with Google Map pin & rating deep links, plus clamping notices if applicable |

---

## 6. Standard Operating Procedures (SOPs) for Agents

### SOP 1: Adding a New Tool to Paridhi
1. **Domain Request & Response**: If new models are needed, define them in `src/paridhi/domain/models.py`.
2. **Port Definition**: If a new provider capability is required, update `SpatialProvider` in `src/paridhi/domain/ports.py`.
3. **Adapter Implementation**: Implement the method in `GoogleSpatialAdapter` (`src/paridhi/infrastructure/google/adapter.py`) and `MockSpatialProvider` (`src/paridhi/infrastructure/mock.py`).
4. **Tool Registration**: Expose the tool via `@server.tool` in `src/paridhi/presentation/server.py`.
5. **Unit & Integration Tests**: Add test cases to `tests/test_server.py`.
6. **Documentation Sync (Mandatory)**:
   - Update `README.md` (Tool parameters, sequence diagram, example output).
   - Update `AGENTS.md` (Tool manifest, schema references).
7. **Verification**: Run `uv run pytest && uv run ruff check . && uv run mypy src tests`.

### SOP 2: Adding an Alternative Geospatial Provider (e.g. Mapbox, OpenStreetMap, Radar)
1. Create `src/paridhi/infrastructure/<provider_name>/adapter.py`.
2. Implement the `SpatialProvider` protocol methods (`geocode`, `search_places`).
3. Add any necessary provider configuration keys in `src/paridhi/core/config.py`.
4. Update `get_spatial_provider()` in `src/paridhi/infrastructure/factory.py` to route the new provider name.
5. Add unit tests for the new adapter using mocked HTTP responses.
6. **Documentation Sync (Mandatory)**: Document the new provider options in `README.md` and `AGENTS.md`.

### SOP 3: Releasing and Versioning Paridhi
1. Review [`RELEASE.md`](./RELEASE.md) for full architecture and SemVer rules (starting at `0.1.0`).
2. Ensure changes follow Conventional Commits (`feat:`, `fix:`, `BREAKING CHANGE:`) so automated SemVer calculation increments properly.
3. Trigger the CI & Release Pipeline manually (`workflow_dispatch` in Actions tab or `gh workflow run ci.yml --ref main`): CI auto-corrects format, verifies tests, calculates SemVer, creates the Git tag, and crafts a GitHub Draft release.
4. Review and publish the draft release in GitHub Releases to finalize the release.
5. The tag creation event automatically runs Aquasecurity Trivy on Python dependencies and the local ARM64 container (`paridhi:local`), generates SPDX 2.3 JSON SBOMs, audits license compliance, detects vulnerabilities across severities, publishes the verified image to GitHub Container Registry (`ghcr.io`), and publishes the security, SBOM, and license report to the GitHub Actions run summary.

---

## 7. Verification & Quality Commands

Always execute the complete verification pipeline before finishing any task:

```bash
# 1. Run test suite (including docs sync test)
uv run pytest

# 2. Check code formatting and linting
uv run ruff check .
uv run ruff format --check .

# 3. Strict type analysis
uv run mypy src tests

# 4. Container build verification (when modifying Dockerfile or packaging)
docker build -t paridhi .
```
