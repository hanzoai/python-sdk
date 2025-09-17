"""Zsh shell tool for command execution with enhanced features."""

import os
import shutil
import platform
from typing import Optional, override
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.shell.base_process import BaseScriptTool


class ZshTool(BaseScriptTool):
    """Tool for running commands in Zsh shell with enhanced features."""

    name = "zsh"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def zsh(
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
        return """Run commands in Zsh shell with enhanced features like better globbing and completion.

Zsh provides advanced features over bash:
- Extended globbing patterns
- Better tab completion
- Array and associative array support
- Powerful command line editing
- Plugin ecosystem (oh-my-zsh, etc.)

Commands that run for more than 2 minutes will automatically continue in the background.

Usage:
zsh "ls -la"
zsh "echo $ZSH_VERSION"
zsh "git status && git diff"
zsh "npm run dev" --cwd ./frontend  # Auto-backgrounds if needed"""

    @override
    def get_interpreter(self) -> str:
        """Get the zsh interpreter path."""
        if platform.system() == "Windows":
            # Try to find zsh on Windows (WSL, Git Bash, etc.)
            zsh_paths = [
                "C:\\Program Files\\Git\\usr\\bin\\zsh.exe",
                "C:\\cygwin64\\bin\\zsh.exe",
                "C:\\msys64\\usr\\bin\\zsh.exe",
            ]
            for path in zsh_paths:
                if Path(path).exists():
                    return path
            # Fall back to bash if no zsh found
            return "bash"

        # On Unix-like systems, check for zsh
        zsh_path = shutil.which("zsh")
        if zsh_path:
            return zsh_path

        # Fall back to bash if zsh not found
        return "bash"

    @override
    def get_script_flags(self) -> list[str]:
        """Get interpreter flags."""
        if platform.system() == "Windows" and self.get_interpreter().endswith(".exe"):
            return ["-c"]
        return ["-c"]

    @override
    def get_tool_name(self) -> str:
        """Get the tool name."""
        return "zsh"

    @override
    async def run(
        self,
        ctx: MCPContext,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """Run a zsh command with auto-backgrounding.

        Args:
            ctx: MCP context
            command: Zsh command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout in seconds (ignored - auto-backgrounds after 2 minutes)

        Returns:
            Command output or background status
        """
        # Check if zsh is available
        if not shutil.which("zsh") and platform.system() != "Windows":
            return "Error: Zsh is not installed. Please install zsh first."

        # Prepare working directory
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Use execute_sync which has auto-backgrounding
        output = await self.execute_sync(command, cwd=work_dir, env=env, timeout=timeout)
        return output if output else "Command completed successfully (no output)"


class ShellTool(BaseScriptTool):
    """Smart shell tool that uses the best available shell (zsh > bash)."""

    name = "shell"

    def __init__(self):
        """Initialize and detect the best shell."""
        super().__init__()
        self._best_shell = self._detect_best_shell()

    def _detect_best_shell(self) -> str:
        """Detect the best available shell."""
        # Check for zsh first
        if shutil.which("zsh"):
            # Also check if .zshrc exists
            if (Path.home() / ".zshrc").exists():
                return "zsh"

        # Check for user's preferred shell
        user_shell = os.environ.get("SHELL", "")
        if user_shell and Path(user_shell).exists():
            return user_shell

        # Default to bash
        return "bash"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def shell(
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
        return f"""Run shell commands using the best available shell (currently: {os.path.basename(self._best_shell)}).

Automatically selects:
- Zsh if available (with .zshrc)
- User's preferred shell ($SHELL)
- Bash as fallback

Commands that run for more than 2 minutes will automatically continue in the background.

Usage:
shell "ls -la"
shell "echo $SHELL"  # Shows which shell is being used
shell "git status && git diff"
shell "npm run dev" --cwd ./frontend  # Auto-backgrounds if needed"""

    @override
    def get_interpreter(self) -> str:
        """Get the best shell interpreter."""
        return self._best_shell

    @override
    def get_script_flags(self) -> list[str]:
        """Get interpreter flags."""
        if platform.system() == "Windows":
            return ["/c"] if self._best_shell == "cmd.exe" else ["-c"]
        return ["-c"]

    @override
    def get_tool_name(self) -> str:
        """Get the tool name."""
        return "shell"

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

        # Add shell info to output if verbose
        shell_name = os.path.basename(self._best_shell)

        # Use execute_sync which has auto-backgrounding
        output = await self.execute_sync(command, cwd=work_dir, env=env, timeout=timeout)

        if output:
            return output
        else:
            return f"Command completed successfully in {shell_name} (no output)"


# Create tool instances
zsh_tool = ZshTool()
shell_tool = ShellTool()  # Smart shell that prefers zsh
