"""CLI entrypoint for Paridhi: launches the FastMCP runner."""

import argparse
import logging
import sys
from typing import Any

from paridhi.core.config import get_settings
from paridhi.presentation.server import create_server


def setup_logging(level: str, debug: bool = False) -> None:
    """Configure structured logging for Paridhi."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    effective_level = logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=effective_level, format=log_format, stream=sys.stderr)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    settings = get_settings()
    parser = argparse.ArgumentParser(
        prog="paridhi",
        description="Paridhi MCP server: Discover and enrich POIs within circular spatial bounds.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {settings.server_version}",
        help="Show application version and exit",
    )
    parser.add_argument(
        "--server-version",
        type=str,
        default=settings.server_version,
        help=f"Paridhi application version (default: {settings.server_version})",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http", "streamable-http", "sse"],
        default=settings.transport,
        help=f"Transport mechanism to use (default: {settings.transport})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.host,
        help=f"Host interface to bind for network transports (default: {settings.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port to listen on for network transports (default: {settings.port})",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=settings.path,
        help="Custom endpoint path (e.g. /mcp or /sse) for network transports",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=settings.debug,
        help="Enable debug logging mode",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI execution handler."""
    args = parse_args()
    settings = get_settings()
    if args.server_version:
        settings.server_version = args.server_version

    setup_logging(level=settings.log_level, debug=args.debug)
    logger = logging.getLogger("paridhi.main")

    logger.info(
        "Starting %s v%s (transport=%s)",
        settings.server_name,
        settings.server_version,
        args.transport,
    )

    server = create_server(settings)

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport in ("http", "streamable-http", "sse"):
        kwargs: dict[str, Any] = {
            "host": args.host,
            "port": args.port,
        }
        if args.path:
            kwargs["path"] = args.path
        server.run(transport=args.transport, **kwargs)
    else:
        server.run()


if __name__ == "__main__":
    main()
