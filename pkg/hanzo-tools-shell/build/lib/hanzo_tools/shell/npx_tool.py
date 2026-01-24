"""NPX tool for both sync and background execution."""

from typing import Optional, override
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import auto_timeout
from hanzo_tools.shell.base_process import BaseBinaryTool


class NpxTool(BaseBinaryTool):
    """Tool for running npx commands."""

    name = "npx"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Run npx packages with automatic backgrounding for long-running processes.

Commands that run for more than 2 minutes will automatically continue in the background.

Usage:
npx create-react-app my-app
npx http-server -p 8080  # Auto-backgrounds after 2 minutes
npx prettier --write "**/*.js"
npx json-server db.json  # Auto-backgrounds if needed"""

    @override
    def get_binary_name(self) -> str:
        """Get the binary name."""
        return "npx"

    @override
    async def run(
        self,
        ctx: MCPContext,
        package: str,
        args: str = "",
        cwd: Optional[str] = None,
        yes: bool = True,
    ) -> str:
        """Run an npx command with auto-backgrounding."""
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        flags = []
        if yes:
            flags.append("-y")

        full_args = args.split() if args else []

        return await self.execute_sync(
            package,
            cwd=work_dir,
            flags=flags,
            args=full_args,
            timeout=None,
        )

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def npx(
            ctx: MCPContext,
            package: str,
            args: str = "",
            cwd: Optional[str] = None,
            yes: bool = True,
        ) -> str:
            return await tool_self.run(ctx, package=package, args=args, cwd=cwd, yes=yes)

    @auto_timeout("npx")
    async def call(self, ctx: MCPContext, **params) -> str:
        """Call the tool with arguments."""
        return await self.run(
            ctx,
            package=params["package"],
            args=params.get("args", ""),
            cwd=params.get("cwd"),
            yes=params.get("yes", True),
        )


# Create tool instance
npx_tool = NpxTool()
