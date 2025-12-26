"""Open files or URLs in the default application."""

import asyncio
import platform
import shutil
import webbrowser
from typing import override
from pathlib import Path
from urllib.parse import urlparse

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.auto_timeout import auto_timeout


class OpenTool(BaseTool):
    """Tool for opening files or URLs in the default application."""

    name = "open"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def open(path: str, ctx: MCPContext) -> str:
            return await tool_self.run(ctx, path)

    @auto_timeout("open")
    async def call(self, ctx: MCPContext, **params) -> str:
        """Call the tool with arguments."""
        return await self.run(ctx, params["path"])

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Open files or URLs. Platform-aware.

Usage:
open https://example.com
open ./document.pdf
open /path/to/image.png"""

    async def _run_opener(self, cmd: list[str], file_path: str) -> bool:
        """Run opener command asynchronously.
        
        Returns True if successful, False otherwise.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            # Don't wait long - these are fire-and-forget
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
                return proc.returncode == 0
            except asyncio.TimeoutError:
                # Process is running (which is fine for opener commands)
                return True
        except Exception:
            return False

    @override
    async def run(self, ctx: MCPContext, path: str) -> str:
        """Open a file or URL in the default application.

        Args:
            ctx: MCP context
            path: File path or URL to open

        Returns:
            Success message

        Raises:
            RuntimeError: If opening fails
        """
        # Check if it's a URL
        parsed = urlparse(path)
        is_url = parsed.scheme in ("http", "https", "ftp", "file")

        if is_url:
            # Open URL in default browser
            try:
                webbrowser.open(path)
                return f"Opened URL in browser: {path}"
            except Exception as e:
                raise RuntimeError(f"Failed to open URL: {e}")

        # It's a file path
        file_path = Path(path).expanduser().resolve()

        if not file_path.exists():
            raise RuntimeError(f"File not found: {file_path}")

        system = platform.system().lower()

        try:
            if system == "darwin":  # macOS
                success = await self._run_opener(["open", str(file_path)], str(file_path))
                if not success:
                    raise RuntimeError("Failed to open file with 'open' command")
            elif system == "linux":
                # Try xdg-open first (most common)
                success = False
                openers = ["xdg-open", "gnome-open", "kde-open", "exo-open"]
                
                for opener in openers:
                    if shutil.which(opener):
                        success = await self._run_opener([opener, str(file_path)], str(file_path))
                        if success:
                            break
                
                if not success:
                    raise RuntimeError("No suitable file opener found on Linux")
            elif system == "windows":
                # Use os.startfile on Windows (this is sync but fast)
                import os
                os.startfile(str(file_path))
            else:
                raise RuntimeError(f"Unsupported platform: {system}")

            return f"Opened file: {file_path}"

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error opening file: {e}")


# Create tool instance
open_tool = OpenTool()
