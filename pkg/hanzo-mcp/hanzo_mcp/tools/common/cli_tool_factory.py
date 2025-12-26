"""Dynamic CLI tool factory for creating tools from shell commands at runtime.

Allows exposing any CLI tool to Claude without creating a Python package.

Usage:
    cli_create(name="git", command="git", description="Git version control")
    cli_create(name="docker", command="docker", description="Docker container management")
    cli_create(name="kubectl", command="kubectl", description="Kubernetes CLI")

    cli_list()  # List all dynamic CLI tools
    cli_remove(name="git")  # Remove a dynamic tool
"""

from __future__ import annotations

import os
import json
import asyncio
import logging
from typing import TYPE_CHECKING, Any
from pathlib import Path
from dataclasses import field, asdict, dataclass

if TYPE_CHECKING:
    from mcp.server import FastMCP

logger = logging.getLogger(__name__)

# Storage for dynamic CLI tool definitions
CLI_TOOLS_CONFIG = Path.home() / ".hanzo" / "mcp" / "cli_tools.json"


@dataclass
class CLIToolDefinition:
    """Definition for a dynamic CLI tool."""

    name: str
    command: str
    description: str
    args_description: str = "Arguments to pass to the command"
    timeout: int = 120
    working_dir: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class CLIToolFactory:
    """Factory for creating and managing dynamic CLI tools.

    Tools are persisted to ~/.hanzo/mcp/cli_tools.json and
    automatically loaded on startup.
    """

    _instance: "CLIToolFactory | None" = None

    def __init__(self):
        self._tools: dict[str, CLIToolDefinition] = {}
        self._registered_handlers: dict[str, Any] = {}
        self._mcp_server: "FastMCP | None" = None
        self._load_config()

    @classmethod
    def get_instance(cls) -> "CLIToolFactory":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = CLIToolFactory()
        return cls._instance

    def set_mcp_server(self, mcp_server: "FastMCP") -> None:
        """Set the MCP server for tool registration."""
        self._mcp_server = mcp_server
        # Register all existing tools
        for tool_def in self._tools.values():
            if tool_def.enabled:
                self._register_tool(tool_def)

    def _load_config(self) -> None:
        """Load CLI tool definitions from disk."""
        if CLI_TOOLS_CONFIG.exists():
            try:
                with open(CLI_TOOLS_CONFIG) as f:
                    data = json.load(f)
                for name, tool_data in data.get("tools", {}).items():
                    self._tools[name] = CLIToolDefinition(**tool_data)
                logger.info(f"Loaded {len(self._tools)} dynamic CLI tools")
            except Exception as e:
                logger.warning(f"Failed to load CLI tools config: {e}")

    def _save_config(self) -> None:
        """Save CLI tool definitions to disk."""
        CLI_TOOLS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        data = {"tools": {name: asdict(tool) for name, tool in self._tools.items()}}
        with open(CLI_TOOLS_CONFIG, "w") as f:
            json.dump(data, f, indent=2)

    def _register_tool(self, tool_def: CLIToolDefinition) -> None:
        """Register a CLI tool with the MCP server."""
        if not self._mcp_server:
            return

        # Create the async handler
        async def cli_handler(
            args: str = "",
            timeout: int | None = None,
            cwd: str | None = None,
        ) -> str:
            """Execute the CLI command."""
            cmd = tool_def.command
            if args:
                cmd = f"{cmd} {args}"

            effective_timeout = timeout or tool_def.timeout
            effective_cwd = cwd or tool_def.working_dir

            # Build environment
            env = os.environ.copy()
            env.update(tool_def.env)

            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=effective_cwd,
                    env=env,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=effective_timeout)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    return f"Command timed out after {effective_timeout}s"

                result = stdout.decode() if stdout else ""
                if stderr:
                    err = stderr.decode()
                    if err:
                        result += f"\n[stderr]\n{err}"

                if proc.returncode != 0:
                    result = f"[exit code: {proc.returncode}]\n{result}"

                return result or "(no output)"

            except Exception as e:
                return f"Error executing command: {e}"

        # Register with MCP server
        try:
            self._mcp_server.tool(
                name=tool_def.name, description=f"{tool_def.description}\n\nCommand: {tool_def.command}"
            )(cli_handler)
            self._registered_handlers[tool_def.name] = cli_handler
            logger.info(f"Registered dynamic CLI tool: {tool_def.name}")
        except Exception as e:
            logger.error(f"Failed to register CLI tool {tool_def.name}: {e}")

    def create(
        self,
        name: str,
        command: str,
        description: str,
        args_description: str = "Arguments to pass to the command",
        timeout: int = 120,
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a new dynamic CLI tool.

        Args:
            name: Tool name (e.g., "git", "docker")
            command: Base command to execute (e.g., "git", "docker")
            description: Tool description for Claude
            args_description: Description of the args parameter
            timeout: Default timeout in seconds
            working_dir: Default working directory
            env: Additional environment variables

        Returns:
            Result dict with success status
        """
        if name in self._tools:
            return {"success": False, "error": f"Tool '{name}' already exists"}

        tool_def = CLIToolDefinition(
            name=name,
            command=command,
            description=description,
            args_description=args_description,
            timeout=timeout,
            working_dir=working_dir,
            env=env or {},
        )

        self._tools[name] = tool_def
        self._save_config()

        # Register if server is available
        if self._mcp_server:
            self._register_tool(tool_def)

        return {
            "success": True,
            "name": name,
            "command": command,
            "message": f"Created CLI tool '{name}'. Use {name}(args='...') to execute.",
        }

    def remove(self, name: str) -> dict[str, Any]:
        """Remove a dynamic CLI tool."""
        if name not in self._tools:
            return {"success": False, "error": f"Tool '{name}' not found"}

        del self._tools[name]
        self._registered_handlers.pop(name, None)
        self._save_config()

        return {"success": True, "name": name, "message": f"Removed CLI tool '{name}'"}

    def list(self) -> list[dict[str, Any]]:
        """List all dynamic CLI tools."""
        return [
            {
                "name": tool.name,
                "command": tool.command,
                "description": tool.description,
                "enabled": tool.enabled,
            }
            for tool in self._tools.values()
        ]

    def enable(self, name: str) -> dict[str, Any]:
        """Enable a CLI tool."""
        if name not in self._tools:
            return {"success": False, "error": f"Tool '{name}' not found"}

        self._tools[name].enabled = True
        self._save_config()

        if self._mcp_server and name not in self._registered_handlers:
            self._register_tool(self._tools[name])

        return {"success": True, "name": name}

    def disable(self, name: str) -> dict[str, Any]:
        """Disable a CLI tool."""
        if name not in self._tools:
            return {"success": False, "error": f"Tool '{name}' not found"}

        self._tools[name].enabled = False
        self._save_config()

        # Note: Can't unregister from FastMCP, but tool won't be re-registered on restart
        return {"success": True, "name": name, "message": "Tool disabled. Restart server to remove."}

    async def get_help(self, name: str) -> str:
        """Get help text for a CLI tool by running --help."""
        if name not in self._tools:
            return f"Tool '{name}' not found"

        tool = self._tools[name]

        try:
            proc = await asyncio.create_subprocess_shell(
                f"{tool.command} --help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            return stdout.decode() or stderr.decode() or "(no help available)"
        except Exception as e:
            return f"Error getting help: {e}"


def register_cli_factory_tools(mcp_server: "FastMCP") -> list:
    """Register CLI factory management tools with MCP server."""
    factory = CLIToolFactory.get_instance()
    factory.set_mcp_server(mcp_server)

    @mcp_server.tool(
        name="cli_create",
        description="""Create a new CLI tool that wraps a shell command.

This allows you to expose any CLI tool to Claude as a first-class tool.

Examples:
    cli_create(name="git", command="git", description="Git version control")
    cli_create(name="docker", command="docker", description="Docker containers")
    cli_create(name="kubectl", command="kubectl", description="Kubernetes CLI")
    cli_create(name="aws", command="aws", description="AWS CLI", timeout=300)
""",
    )
    async def cli_create(
        name: str,
        command: str,
        description: str,
        timeout: int = 120,
    ) -> str:
        result = factory.create(
            name=name,
            command=command,
            description=description,
            timeout=timeout,
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool(name="cli_list", description="List all dynamic CLI tools that have been created.")
    async def cli_list() -> str:
        tools = factory.list()
        if not tools:
            return "No dynamic CLI tools configured. Use cli_create() to add one."

        lines = ["# Dynamic CLI Tools\n"]
        for tool in tools:
            status = "✓" if tool["enabled"] else "✗"
            lines.append(f"{status} **{tool['name']}** - `{tool['command']}`")
            lines.append(f"  {tool['description']}\n")
        return "\n".join(lines)

    @mcp_server.tool(name="cli_remove", description="Remove a dynamic CLI tool.")
    async def cli_remove(name: str) -> str:
        result = factory.remove(name)
        return json.dumps(result, indent=2)

    @mcp_server.tool(name="cli_help", description="Get help text for a CLI tool by running --help.")
    async def cli_help(name: str) -> str:
        return await factory.get_help(name)

    # Return empty list since these are registered directly
    return []
