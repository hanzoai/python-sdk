"""Version tool for hanzo-mcp."""

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

import hanzo_mcp


def register_version_tool(mcp: FastMCP) -> None:
    """Register the version tool with the MCP server."""

    @mcp.tool()
    async def version() -> dict[str, Any]:
        """Get hanzo-mcp version and environment information.

        Returns version info including:
        - hanzo-mcp version
        - Python version
        - Platform info
        """
        import platform

        return {
            "hanzo_mcp": hanzo_mcp.__version__,
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "arch": platform.machine(),
        }
