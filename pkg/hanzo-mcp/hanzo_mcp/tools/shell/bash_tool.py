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
            return await tool_self.run(
                ctx, command=command, cwd=cwd, env=env, timeout=timeout
            )

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
        """Get the shell interpreter."""
        if platform.system() == "Windows":
            return "cmd.exe"

        # Check for user's preferred shell from environment
        shell = os.environ.get("SHELL", "/bin/bash")

        # Extract just the shell name from the path
        shell_name = os.path.basename(shell)

        # Check if it's a supported shell and the config file exists
        if shell_name == "zsh":
            # Check for .zshrc
            zshrc_path = Path.home() / ".zshrc"
            if zshrc_path.exists():
                return shell  # Use full path to zsh
        elif shell_name == "fish":
            # Check for fish config
            fish_config = Path.home() / ".config" / "fish" / "config.fish"
            if fish_config.exists():
                return shell  # Use full path to fish

        # Default to bash if no special shell config found
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
        if platform.system() == "Windows":
            return "shell"

        # Return the actual shell being used
        interpreter = self.get_interpreter()
        return os.path.basename(interpreter)

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
        output = await self.execute_sync(
            command, cwd=work_dir, env=env, timeout=timeout
        )
        return output if output else "Command completed successfully (no output)"


# Create tool instance
bash_tool = BashTool()
