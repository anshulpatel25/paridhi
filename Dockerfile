# syntax=docker/dockerfile:1

# ==============================================================================
# Stage 1: Build virtual environment with uv
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

# Install uv from official Astral binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment configurations for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies without the application source
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application source and documentation required by pyproject.toml
COPY README.md ./
COPY src/ ./src/

# Install the application itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ==============================================================================
# Stage 2: Minimal runtime image
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Metadata labels
LABEL maintainer="Anshul Patel <er.anshul.patel@gmail.com>"
LABEL description="Paridhi FastMCP server for discovering and enriching points of interest within circular spatial bounds"
LABEL org.opencontainers.image.title="Paridhi"
LABEL org.opencontainers.image.description="FastMCP server for discovering and enriching points of interest within circular spatial bounds"
LABEL org.opencontainers.image.authors="Anshul Patel <er.anshul.patel@gmail.com>"

# Install curl for HEALTHCHECK and ca-certificates for upstream HTTPS APIs
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root system user and group
RUN groupadd --gid 10001 paridhi && \
    useradd --uid 10001 --gid paridhi --shell /bin/sh --no-create-home paridhi

WORKDIR /app

# Copy virtual environment and project from builder with non-root ownership
COPY --from=builder --chown=paridhi:paridhi /app/.venv /app/.venv
COPY --from=builder --chown=paridhi:paridhi /app /app

# Set runtime environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PARIDHI_TRANSPORT=http \
    PARIDHI_HOST=0.0.0.0 \
    PARIDHI_PORT=8000

# Expose network transport port
EXPOSE 8000

# Switch to non-root user
USER paridhi:paridhi

# Health check using custom informational GET / route
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/ || exit 1

# Default CLI entrypoint and execution arguments
ENTRYPOINT ["paridhi"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
