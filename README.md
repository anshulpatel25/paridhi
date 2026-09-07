# Paridhi (परिधि)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-4.0+-brightgreen.svg)](https://github.com/jlowin/fastmcp)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)

**Paridhi** (*परिधि* — Sanskrit for *perimeter*, *circumference*, or *boundary*) is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server built with Python and [FastMCP](https://github.com/jlowin/fastmcp). It is designed to discover and enrich local points of interest (POIs) within circular spatial bounds.

---

## Architecture & CUPID Design

Paridhi is architected according to **CUPID** principles and Clean Architecture:

- **Composable:** Each component (spatial boundary models, configuration, transport runners, and future enrichment providers) can be plugged together or tested in isolation.
- **Unix-like (Single Responsibility):**
  - `core/config.py`: Environment configuration and runtime settings.
  - `domain/models.py`: Immutable coordinates, circular boundaries, POI domain entities, and Pydantic validation schemas.
  - `domain/exceptions.py`: Rich domain error hierarchy.
  - `presentation/server.py`: FastMCP server instantiation and tool exposure.
  - `main.py`: CLI entrypoint and runner dispatch.
- **Predictable:** Strict validation with explicit bounds. Geographic coordinates are validated to WGS 84 limits, and spatial search radii are automatically clamped to valid bounds `[100m, 50,000m]`.
- **Idiomatic:** Built with modern Python 3.11+ patterns, Pydantic v2 schemas, type safety, and FastMCP annotations.
- **Domain-focused:** Ubiquitous spatial domain terminology: circular bounds, perimeters, coordinates, and points of interest.

---

## Project Structure

```text
paridhi/
├── .env.example                # Template for environment configuration
├── .python-version             # Python version pinned by uv (3.12)
├── pyproject.toml              # Build specifications, dependencies, and tool settings
├── uv.lock                     # Deterministic dependency lockfile
├── README.md                   # Project documentation
├── src/
│   └── paridhi/
│       ├── __init__.py         # Package root exposing version and entrypoints
│       ├── py.typed            # PEP 561 typing marker
│       ├── main.py             # CLI runner entrypoint
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py       # pydantic-settings configuration
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── exceptions.py   # Domain & infrastructure error hierarchy
│       │   └── models.py       # Pydantic schemas (POIs, bounds, clamping)
│       └── presentation/
│           ├── __init__.py
│           └── server.py       # FastMCP server & registered tool handlers
└── tests/
    ├── __init__.py
    ├── test_config.py          # Configuration tests
    ├── test_domain_models.py   # Coordinate validation & radius clamping tests
    └── test_server.py          # FastMCP tool execution tests (ping & discover_pois)
```

---

## Getting Started

Paridhi uses **`uv`** exclusively for virtual environment management, builds, and dependency handling.

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (v0.11+)

### Installation

Clone the repository and sync the dependencies:

```bash
git clone https://github.com/anshulpatel25/paridhi.git
cd paridhi
uv sync
```

To include development tools (`pytest`, `ruff`, `mypy`):

```bash
uv sync --all-groups
```

---

## Running the Server

### 1. Standard I/O (Default for MCP Clients)

Launch Paridhi over `stdio` transport:

```bash
uv run paridhi
# Or explicitly:
uv run paridhi --transport stdio
```

### 2. Network Transports (SSE)

Launch Paridhi as a Server-Sent Events (SSE) server for remote or HTTP-based clients:

```bash
uv run paridhi --transport sse --host 127.0.0.1 --port 8000
```

### 3. MCP Client Configuration

To integrate with an MCP client (such as Claude Desktop), add Paridhi to your MCP configuration:

```json
{
  "mcpServers": {
    "paridhi": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/paridhi",
        "run",
        "paridhi"
      ]
    }
  }
}
```

---

## Exposed MCP Tools

### `ping`
Health check tool that verifies that the server is operational.

- **Inputs:** None
- **Output:**
  ```json
  {
    "status": "healthy",
    "service": "Paridhi",
    "version": "0.1.0",
    "timestamp": "2026-09-07T11:15:00Z"
  }
  ```

### `discover_pois`
Discovers and filters points of interest within circular spatial bounds centered at the given coordinates.

- **Parameters:**
  - `latitude` (*float*, required): Center latitude in decimal degrees `[-90.0, 90.0]`.
  - `longitude` (*float*, required): Center longitude in decimal degrees `[-180.0, 180.0]`.
  - `radius_meters` (*float*, optional, default: `1000.0`): Search radius in meters.
    - **Geographic Constraint Clamping:** If provided value `< 100.0`, clamped to `100.0m`. If `> 50,000.0`, clamped to `50,000.0m`.
  - `categories` (*list[str]*, optional): Filter POIs by category (e.g., `["restaurant", "park"]`).
  - `query` (*str*, optional): Free-text search keyword.
  - `limit` (*int*, optional, default: `20`): Maximum results to return (`1` to `100`).
- **Output:**
  ```json
  {
    "center": {
      "latitude": 19.076,
      "longitude": 72.8777
    },
    "radius_meters": 1000.0,
    "total_found": 0,
    "pois": [],
    "message": "Spatial search perimeter established at radius 1000.0m."
  }
  ```

---

## Configuration

Paridhi loads configuration values from environment variables or a local `.env` file using `pydantic-settings` (with the `PARIDHI_` prefix):

| Variable | Type | Default | Description |
|---|---|---|---|
| `PARIDHI_SERVER_NAME` | string | `Paridhi` | Name of the FastMCP server instance |
| `PARIDHI_SERVER_VERSION` | string | `0.1.0` | Semantic version string |
| `PARIDHI_DEBUG` | boolean | `false` | Enable verbose debug logging |
| `PARIDHI_LOG_LEVEL` | string | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PARIDHI_MIN_RADIUS_METERS` | float | `100.0` | Minimum allowable spatial radius (meters) |
| `PARIDHI_MAX_RADIUS_METERS` | float | `50000.0` | Maximum allowable spatial radius (meters) |
| `PARIDHI_DEFAULT_RADIUS_METERS`| float | `1000.0` | Default search radius (meters) |
| `PARIDHI_DEFAULT_RESULTS_LIMIT`| integer | `20` | Default POI count limit |
| `PARIDHI_MAX_RESULTS_LIMIT` | integer | `100` | Upper limit for POI results |
| `PARIDHI_TRANSPORT` | string | `stdio` | Transport mechanism (`stdio`, `sse`, `stream`) |
| `PARIDHI_HOST` | string | `127.0.0.1` | Binding host for network transports |
| `PARIDHI_PORT` | integer | `8000` | Port for network transports |

---

## Developer Workflows

All development commands are orchestrated through `uv`:

```bash
# Run unit & integration test suite
uv run pytest

# Check code quality and style
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Run static type checking
uv run mypy src tests
```

---

## License

Apache-2.0
