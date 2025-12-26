"""Zsh shell tool for command execution with enhanced features."""

import os
import json
import shutil
import platform
from typing import Optional, override
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.shell.base_process import BaseScriptTool
from hanzo_mcp.tools.common.auto_timeout import auto_timeout
from hanzo_mcp.tools.shell.output_format import format_shell_result


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

    @auto_timeout("zsh")
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
        return """Run commands in Zsh shell with enhanced features.

This tool returns JSON with these fields:
- summary: Brief description of what happened
- stdout_markdown: Output formatted as markdown code block
- stderr_markdown: Errors formatted as markdown (if any)
- status: "success", "error", or "backgrounded"
- exit_code: Command exit code (0 = success)

DISPLAY INSTRUCTIONS: Show the summary as a bullet point, then render
stdout_markdown and stderr_markdown directly as markdown. Never show raw JSON.

Example rendering:
• Listed 12 items in /project
```
total 48K
drwxr-xr-x  5 user staff 160 Dec 26 10:00 .
...
```

Commands that exceed timeout automatically continue in background.
Use `ps --logs <id>` to view output, `ps --kill <id>` to stop.

Usage:
zsh "ls -la"
zsh "git status && git diff"
zsh "npm run dev" --cwd ./frontend"""

    @override
    def get_interpreter(self) -> str:
        """Get the zsh interpreter path.

        Respects HANZO_MCP_FORCE_SHELL environment variable to override.
        """
        # Check for forced shell override
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

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
            JSON with summary, stdout_markdown, stderr_markdown, status, exit_code
        """
        # Check if zsh is available
        if not shutil.which("zsh") and platform.system() != "Windows":
            return format_shell_result(
                command=command,
                stdout="",
                stderr="Zsh is not installed. Please install zsh first.",
                exit_code=1,
                cwd=str(cwd) if cwd else None,
            )

        # Prepare working directory
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Use execute_sync which has auto-backgrounding
        try:
            output = await self.execute_sync(command, cwd=work_dir, env=env, timeout=timeout)

            # Check if it was backgrounded
            if output and "automatically backgrounded" in output.lower():
                # Extract process ID from the message
                import re

                pid_match = re.search(r"Process ID: (\S+)", output)
                process_id = pid_match.group(1) if pid_match else None

                return format_shell_result(
                    command=command,
                    stdout=output,
                    exit_code=0,
                    cwd=str(work_dir),
                    was_backgrounded=True,
                    process_id=process_id,
                )

            # Check for error in output
            if output and output.startswith("Command failed"):
                # Extract exit code from message
                import re

                exit_match = re.search(r"exit code (\d+)", output)
                exit_code = int(exit_match.group(1)) if exit_match else 1

                return format_shell_result(
                    command=command,
                    stdout="",
                    stderr=output,
                    exit_code=exit_code,
                    cwd=str(work_dir),
                )

            # Success case
            return format_shell_result(
                command=command,
                stdout=output if output else "",
                exit_code=0,
                cwd=str(work_dir),
            )

        except RuntimeError as e:
            # Handle execution errors
            return format_shell_result(
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=1,
                cwd=str(work_dir),
            )


class ShellTool(BaseScriptTool):
    """Smart shell tool that uses the best available shell (zsh > bash)."""

    name = "shell"

    def __init__(self):
        """Initialize and detect the best shell."""
        super().__init__()
        self._best_shell = self._detect_best_shell()

    def _detect_best_shell(self) -> str:
        """Detect the best available shell.

        Respects HANZO_MCP_FORCE_SHELL environment variable to override.
        """
        # Check for forced shell override first
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

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

    @auto_timeout("shell")
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

This tool returns JSON with these fields:
- summary: Brief description of what happened
- stdout_markdown: Output formatted as markdown code block
- stderr_markdown: Errors formatted as markdown (if any)
- status: "success", "error", or "backgrounded"
- exit_code: Command exit code (0 = success)

DISPLAY INSTRUCTIONS: Show the summary as a bullet point, then render
stdout_markdown and stderr_markdown directly as markdown. Never show raw JSON.

Automatically selects: Zsh > User's $SHELL > Bash

Commands that exceed timeout automatically continue in background.
Use `ps --logs <id>` to view output, `ps --kill <id>` to stop.

Usage:
shell "ls -la"
shell "git status && git diff"
shell "npm run dev" --cwd ./frontend"""

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
            JSON with summary, stdout_markdown, stderr_markdown, status, exit_code
        """
        # Prepare working directory
        work_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Use execute_sync which has auto-backgrounding
        try:
            output = await self.execute_sync(command, cwd=work_dir, env=env, timeout=timeout)

            # Check if it was backgrounded
            if output and "automatically backgrounded" in output.lower():
                import re

                pid_match = re.search(r"Process ID: (\S+)", output)
                process_id = pid_match.group(1) if pid_match else None

                return format_shell_result(
                    command=command,
                    stdout=output,
                    exit_code=0,
                    cwd=str(work_dir),
                    was_backgrounded=True,
                    process_id=process_id,
                )

            # Check for error in output
            if output and output.startswith("Command failed"):
                import re

                exit_match = re.search(r"exit code (\d+)", output)
                exit_code = int(exit_match.group(1)) if exit_match else 1

                return format_shell_result(
                    command=command,
                    stdout="",
                    stderr=output,
                    exit_code=exit_code,
                    cwd=str(work_dir),
                )

            # Success case
            return format_shell_result(
                command=command,
                stdout=output if output else "",
                exit_code=0,
                cwd=str(work_dir),
            )

        except RuntimeError as e:
            return format_shell_result(
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=1,
                cwd=str(work_dir),
            )


# Create tool instances
zsh_tool = ZshTool()
shell_tool = ShellTool()  # Smart shell that prefers zsh
