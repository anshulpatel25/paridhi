# Paridhi Core Package

## Overview
Root Python package containing the main application entry point, CLI orchestration, and architectural subpackages organized following Hexagonal (Ports & Adapters) design.

## Interface
- `[main.py:main]`: CLI entrypoint parsing command line arguments, setting up structured logging, and running the `FastMCP` server.
- `[main.py:parse_args]`: Argument parser for CLI flags (`--version`, `--transport`, `--host`, `--port`, `--path`, `--debug`).
- `[main.py:setup_logging]`: Configures stderr logging format and log level.
- `[__init__.py:__version__]`: Application version string (`"0.1.0"`).
- [Core Configuration](./core/README.md): Environment settings and runtime configuration.
- [Domain](./domain/README.md): Domain models, spatial clamping, exception hierarchy, and abstract provider ports.
- [Infrastructure](./infrastructure/README.md): Geospatial provider implementations and factory mechanisms.
- [Presentation](./presentation/README.md): FastMCP server definition and tool endpoints (`ping`, `discover_pois`).

## Invariants
- `[main.py:parse_args]`: Restricts transport options to `stdio`, `http`, `streamable-http`, and `sse`.
- `[main.py:main]`: Overrides `settings.server_version` with CLI argument if supplied, prior to launching the server.

## Side Effects
- `[main.py:setup_logging]`: Configures global logging stream to `sys.stderr`.
- `[main.py:main]`: Binds socket listeners or standard input/output streams for MCP transport processing.

## Verification
- Run: `uv run pytest`
