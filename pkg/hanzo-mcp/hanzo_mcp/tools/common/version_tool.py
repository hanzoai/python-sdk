"""Version tool for hanzo-mcp."""

import sys

from hanzo_async import using_uvloop
from mcp.server.fastmcp import FastMCP

import hanzo_mcp


def register_version_tool(mcp: FastMCP) -> None:
    """Register the version tool with the MCP server."""

    @mcp.tool()
    async def version() -> str:
        """Get hanzo-mcp version and environment information.

        Returns version info including:
        - hanzo-mcp version
        - Python version
        - Platform info
        - Async backend (uvloop or asyncio)
        """
        import platform

        # Get uvloop version if active
        async_backend = "asyncio"
        if using_uvloop():
            try:
                import uvloop

                async_backend = f"uvloop {uvloop.__version__}"
            except ImportError:
                async_backend = "uvloop"

        info = {
            "hanzo_mcp": hanzo_mcp.__version__,
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "arch": platform.machine(),
            "async": async_backend,
        }

        # Return formatted string for clean display
        lines = [
            f"hanzo-mcp: v{info['hanzo_mcp']}",
            f"python: {info['python']}",
            f"platform: {info['platform']} ({info['arch']})",
            f"async: {info['async']}",
        ]
        return "\n".join(lines)
