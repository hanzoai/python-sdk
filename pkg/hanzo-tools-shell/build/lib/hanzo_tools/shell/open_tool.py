"""Open files or URLs in the default application."""

import asyncio
import platform
import webbrowser
from typing import override
from pathlib import Path
from urllib.parse import urlparse

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout


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
        """Run an opener command asynchronously (fire-and-forget pattern)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
                return proc.returncode == 0
            except asyncio.TimeoutError:
                # Process is still running, which is fine for opener commands
                return True
        except Exception:
            return False

    async def run(self, ctx: MCPContext, path: str) -> str:
        """Open a file or URL in the default application."""
        parsed = urlparse(path)
        is_url = parsed.scheme in ("http", "https", "ftp", "file")

        if is_url:
            try:
                # Run webbrowser.open in executor to avoid blocking
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, webbrowser.open, path)
                return f"Opened URL in browser: {path}"
            except Exception as e:
                raise RuntimeError(f"Failed to open URL: {e}")

        file_path = Path(path).expanduser().resolve()

        # Check file exists asynchronously
        loop = asyncio.get_running_loop()
        exists = await loop.run_in_executor(None, file_path.exists)
        if not exists:
            raise RuntimeError(f"File not found: {file_path}")

        system = platform.system().lower()

        try:
            if system == "darwin":  # macOS
                if await self._run_opener(["open", str(file_path)], str(file_path)):
                    return f"Opened file: {file_path}"
                raise RuntimeError("Failed to open file with 'open' command")
            elif system == "linux":
                # Try xdg-open first
                if await self._run_opener(["xdg-open", str(file_path)], str(file_path)):
                    return f"Opened file: {file_path}"
                # Fallback to other openers
                for opener in ["gnome-open", "kde-open", "exo-open"]:
                    if await self._run_opener([opener, str(file_path)], str(file_path)):
                        return f"Opened file: {file_path}"
                raise RuntimeError("No suitable file opener found on Linux")
            elif system == "windows":
                import os

                # Run os.startfile in executor to avoid blocking
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, os.startfile, str(file_path))
                return f"Opened file: {file_path}"
            else:
                raise RuntimeError(f"Unsupported platform: {system}")

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error opening file: {e}")


# Create tool instance
open_tool = OpenTool()
