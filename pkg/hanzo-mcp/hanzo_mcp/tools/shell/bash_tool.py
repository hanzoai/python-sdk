"""Bash/Shell tool for command execution."""

import os
import platform
from typing import Optional, override
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.shell.base_process import BaseScriptTool


class BashTool(BaseScriptTool):
    """Tool for running shell commands."""

    name = "bash"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def bash(
            ctx: MCPContext,
            command: str,
            cwd: Optional[str] = None,
            env: Optional[dict[str, str]] = None,
            timeout: Optional[int] = None,
        ) -> str:
            return await tool_self.run(ctx, command=command, cwd=cwd, env=env, timeout=timeout)

    async def call(self, ctx: MCPContext, **params) -> str:
        """Call the tool with arguments."""
        return await self.run(
            ctx,
            command=params["command"],
            cwd=params.get("cwd"),
            env=params.get("env"),
            timeout=params.get("timeout"),
        )

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Run shell commands with automatic backgrounding for long-running processes.

Commands that run for more than 2 minutes will automatically continue in the background.
You can check their status and logs using the 'process' tool.

Usage:
bash "ls -la"
bash "python server.py"  # Auto-backgrounds after 2 minutes
bash "git status && git diff"
bash "npm run dev" --cwd ./frontend  # Auto-backgrounds if needed"""

    @override
    def get_interpreter(self) -> str:
        """Get the bash interpreter."""
        if platform.system() == "Windows":
            # Try to find bash on Windows (Git Bash, WSL, etc.)
            bash_paths = [
                "C:\\Program Files\\Git\\bin\\bash.exe",
                "C:\\cygwin64\\bin\\bash.exe",
                "C:\\msys64\\usr\\bin\\bash.exe",
            ]
            for path in bash_paths:
                if Path(path).exists():
                    return path
            return "cmd.exe"  # Fall back to cmd if no bash found

        # On Unix-like systems, always use bash
        return "bash"

    @override
    def get_script_flags(self) -> list[str]:
        """Get interpreter flags."""
        if platform.system() == "Windows":
            return ["/c"]
        return ["-c"]

    @override
    def get_tool_name(self) -> str:
        """Get the tool name."""
        return "bash"

    @override
    async def run(
        self,
        ctx: MCPContext,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """Run a shell command with auto-backgrounding.

        Args:
            ctx: MCP context
            command: Shell command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout in seconds (ignored - auto-backgrounds after 2 minutes)

        Returns:
            Command output or background status
        """
        # Prepare working directory
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Always use execute_sync which now has auto-backgrounding
        output = await self.execute_sync(command, cwd=work_dir, env=env, timeout=timeout)
        return output if output else "Command completed successfully (no output)"


# Create tool instance
bash_tool = BashTool()
