"""Paridhi: FastMCP server for discovering and enriching local points of interest.

Paridhi (परिधि) provides circular spatial boundary enforcement and POI enrichment
for Model Context Protocol (MCP) clients.
"""

from paridhi.main import main
from paridhi.presentation.server import create_server, mcp

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "create_server",
    "main",
    "mcp",
]
