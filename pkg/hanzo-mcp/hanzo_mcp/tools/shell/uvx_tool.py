"""UVX tool for both sync and background execution."""

from typing import Optional, override
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.shell.base_process import BaseBinaryTool


class UvxTool(BaseBinaryTool):
    """Tool for running uvx commands."""

    name = "uvx"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Run Python packages with uvx with automatic backgrounding for long-running processes.

Commands that run for more than 2 minutes will automatically continue in the background.

Usage:
uvx ruff check .
uvx mkdocs serve  # Auto-backgrounds after 2 minutes
uvx black --check src/
uvx jupyter lab --port 8888  # Auto-backgrounds if needed"""

    @override
    def get_binary_name(self) -> str:
        """Get the binary name."""
        return "uvx"

    @override
    async def run(
        self,
        ctx: MCPContext,
        package: str,
        args: str = "",
        cwd: Optional[str] = None,
        python: Optional[str] = None,
    ) -> str:
        """Run a uvx command with auto-backgrounding.

        Args:
            ctx: MCP context
            package: Python package to run
            args: Additional arguments
            cwd: Working directory
            python: Python version constraint

        Returns:
            Command output or background status
        """
        # Prepare working directory
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Prepare flags
        flags = []
        if python:
            flags.extend(["--python", python])

        # Build full command
        full_args = args.split() if args else []

        # Always use execute_sync which now has auto-backgrounding
        return await self.execute_sync(
            package,
            cwd=work_dir,
            flags=flags,
            args=full_args,
            timeout=None,  # Let auto-backgrounding handle timeout
        )

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def uvx(
            ctx: MCPContext,
            package: str,
            args: str = "",
            cwd: Optional[str] = None,
            python: Optional[str] = None,
        ) -> str:
            return await tool_self.run(ctx, package=package, args=args, cwd=cwd, python=python)

    async def call(self, ctx: MCPContext, **params) -> str:
        """Call the tool with arguments."""
        return await self.run(
            ctx,
            package=params["package"],
            args=params.get("args", ""),
            cwd=params.get("cwd"),
            python=params.get("python"),
        )


# Create tool instance
uvx_tool = UvxTool()
