# Core Configuration Package

## Overview
Provides centralized runtime configuration management and environment parameter resolution for Paridhi using `pydantic-settings`.

## Interface
- `[config.py:Settings]`: Pydantic `BaseSettings` schema defining all server, spatial boundary, HTTP client, and geospatial provider settings.
- `[config.py:get_settings]`: LRU-cached factory function returning the application configuration singleton instance.

## Invariants
- `[config.py:Settings.model_config]`: Reads environment variables using prefix `PARIDHI_` and ignores unexpected extra attributes.
- `[config.py:Settings.google_maps_api_key]`: Resolves API keys across alias list: `GOOGLE_MAPS_API_KEY`, `GOOGLE_API_KEY`, `PARIDHI_GOOGLE_MAPS_API_KEY`, `PARIDHI_GOOGLE_API_KEY`.
- `[config.py:Settings.transport]`: Must be one of literal choices: `"stdio"`, `"http"`, `"streamable-http"`, `"sse"`.
- `[config.py:get_settings]`: Cached via `@lru_cache(maxsize=1)`; subsequent invocations return the exact same in-memory object instance.

## Side Effects
- `[config.py:Settings]`: Reads filesystem `.env` file if present at process working directory.

## Verification
- Run: `uv run pytest tests/test_config.py`
