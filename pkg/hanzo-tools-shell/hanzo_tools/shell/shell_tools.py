"""Shell tool shims - zsh, bash, fish, dash, shell wrappers over cmd.

These are thin wrappers that set the shell and delegate to CmdTool.
Use cmd directly for full control.

Supported shells:
- zsh: Z shell (default on macOS, popular on Linux)
- bash: Bourne-Again shell (most common, default on most Linux)
- fish: Friendly Interactive Shell (modern, user-friendly)
- dash: Debian Almquist Shell (fast POSIX shell, Ubuntu's /bin/sh)
- shell: Auto-selects best available (zsh > bash > fish > dash > sh)
"""

import os
import shutil
from typing import Any, Dict, List, Optional, Annotated, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.shell.cmd_tool import CmdTool, Command


class ZshTool(CmdTool):
    """Zsh shell - thin wrapper over cmd with shell=zsh.

    Usage:
        zsh("ls -la")                    # Single command
        zsh(["ls", "pwd"])               # Sequential
        zsh(["a", "b"], parallel=True)   # Parallel
    """

    name = "zsh"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize with zsh as default shell."""
        super().__init__(tools=tools, default_shell="zsh")

    def _resolve_shell(self, preferred: str) -> str:
        """Resolve zsh shell path."""
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        search_paths = [
            "/opt/homebrew/bin/zsh",
            "/usr/local/bin/zsh",
            "/bin/zsh",
            "/usr/bin/zsh",
        ]

        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        found = shutil.which("zsh")
        if found:
            return found

        # Fallback to bash if zsh not found
        return shutil.which("bash") or "sh"

    @property
    @override
    def description(self) -> str:
        shell_name = os.path.basename(self.default_shell)
        return f"""Zsh shell (using: {shell_name}).

SIMPLE:
  zsh("ls -la")                    # Single command
  zsh("A ; B ; C")                 # Sequential via shell

ARRAYS:
  zsh(["a", "b", "c"])             # Sequential
  zsh(["a", "b"], parallel=True)   # All parallel
  zsh(["a", ["b", "c"], "d"])      # Nested = parallel

OPTIONS:
  parallel: Run ALL commands concurrently
  strict: Stop on first error
  quiet: Suppress stdout
  timeout: Per-command timeout (default: 45s)
  cwd: Working directory
  env: Environment variables

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background.
Use ps --logs <id> to view, ps --kill <id> to stop."""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register zsh tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def zsh_handler(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands for DAG execution", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run all commands in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout per command (seconds)", default=45)] = 45,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=None,  # Use default (zsh)
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class BashTool(CmdTool):
    """Bash shell - thin wrapper over cmd with shell=bash."""

    name = "bash"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize with bash as default shell."""
        super().__init__(tools=tools, default_shell="bash")

    def _resolve_shell(self, preferred: str) -> str:
        """Resolve bash shell path."""
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        found = shutil.which("bash")
        if found:
            return found

        return "sh"

    @property
    @override
    def description(self) -> str:
        return """Bash shell - thin wrapper over cmd.

USAGE:
  bash("ls -la")                   # Single command
  bash(["a", "b", "c"])            # Sequential
  bash(["a", "b"], parallel=True)  # Parallel

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background."""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register bash tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def bash_handler(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout (seconds)", default=45)] = 45,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=None,  # Use default (bash)
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class FishTool(CmdTool):
    """Fish shell - thin wrapper over cmd with shell=fish."""

    name = "fish"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize with fish as default shell."""
        super().__init__(tools=tools, default_shell="fish")

    def _resolve_shell(self, preferred: str) -> str:
        """Resolve fish shell path."""
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        search_paths = [
            "/opt/homebrew/bin/fish",
            "/usr/local/bin/fish",
            "/usr/bin/fish",
        ]

        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        found = shutil.which("fish")
        if found:
            return found

        # Fallback to zsh/bash if fish not found
        return shutil.which("zsh") or shutil.which("bash") or "sh"

    @property
    @override
    def description(self) -> str:
        shell_name = os.path.basename(self.default_shell)
        return f"""Fish shell (using: {shell_name}).

USAGE:
  fish("ls -la")                   # Single command
  fish(["a", "b", "c"])            # Sequential
  fish(["a", "b"], parallel=True)  # Parallel

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background."""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register fish tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def fish_handler(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout (seconds)", default=45)] = 45,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=None,  # Use default (fish)
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class DashTool(CmdTool):
    """Dash shell - fast POSIX-compliant shell (Ubuntu's /bin/sh)."""

    name = "dash"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize with dash as default shell."""
        super().__init__(tools=tools, default_shell="dash")

    def _resolve_shell(self, preferred: str) -> str:
        """Resolve dash shell path."""
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        # dash is often /bin/sh on Debian/Ubuntu
        search_paths = [
            "/bin/dash",
            "/usr/bin/dash",
        ]

        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        found = shutil.which("dash")
        if found:
            return found

        # Fallback to sh (which may be dash on Ubuntu)
        return "sh"

    @property
    @override
    def description(self) -> str:
        return """Dash shell - fast POSIX-compliant shell.

Dash is the Debian Almquist Shell, a POSIX-compliant shell that's
faster than bash for scripts. It's the default /bin/sh on Ubuntu/Debian.

USAGE:
  dash("ls -la")                   # Single command
  dash(["a", "b", "c"])            # Sequential
  dash(["a", "b"], parallel=True)  # Parallel

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background."""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register dash tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def dash_handler(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout (seconds)", default=45)] = 45,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=None,  # Use default (dash)
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class ShellTool(CmdTool):
    """Smart shell - auto-selects best available shell (zsh > bash > fish > dash > sh)."""

    name = "shell"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize with best available shell."""
        super().__init__(tools=tools, default_shell="zsh")  # Will resolve to best available

    @property
    @override
    def description(self) -> str:
        shell_name = os.path.basename(self.default_shell)
        return f"""Smart shell (auto-selected: {shell_name}).

Automatically uses the best available shell:
  zsh > bash > fish > dash > sh

USAGE:
  shell("ls -la")                   # Single command
  shell(["a", "b", "c"])            # Sequential
  shell(["a", "b"], parallel=True)  # Parallel

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background."""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register shell tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def shell_handler(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout (seconds)", default=45)] = 45,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=None,  # Use default
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


# Singleton instances
zsh_tool = ZshTool()
bash_tool = BashTool()
fish_tool = FishTool()
dash_tool = DashTool()
shell_tool = ShellTool()
