"""Unified CLI Tools - DRY implementation using base agent classes.

This module provides the single, clean implementation of all CLI tools
following Python best practices and eliminating all duplication.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context

from ..common.base import BaseTool
from ...core.base_agent import CLIAgent, AgentConfig
from ..common.permissions import PermissionManager
from ...core.model_registry import registry


class UnifiedCLITool(BaseTool, CLIAgent):
    """Unified CLI tool that combines BaseTool and CLIAgent functionality.

    MRO: BaseTool first for proper method resolution order.
    """

    def __init__(
        self,
        name: str,
        description: str,
        cli_command: str,
        default_model: str,
        permission_manager: Optional[PermissionManager] = None,
    ):
        """Initialize unified CLI tool.

        Args:
            name: Tool name
            description: Tool description
            cli_command: CLI command to execute
            default_model: Default model to use
            permission_manager: Permission manager for access control
        """
        # Initialize CLIAgent with config
        config = AgentConfig(model=default_model)
        CLIAgent.__init__(self, config)

        # Store tool metadata
        self._name = name
        self._description = description
        self._cli_command = cli_command
        self.permission_manager = permission_manager

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def cli_command(self) -> str:
        return self._cli_command

    def build_command(self, prompt: str, **kwargs: Any) -> List[str]:
        """Build the CLI command with model-specific formatting.

        Args:
            prompt: The prompt
            **kwargs: Additional parameters

        Returns:
            Command arguments list
        """
        command = [self.cli_command]

        # Get model config from registry
        model_config = registry.get(self.config.model)

        # Handle different CLI tool formats
        if self.cli_command == "claude":
            if model_config:
                command.extend(["--model", model_config.full_name])
            # Claude takes prompt via stdin
            return command

        elif self.cli_command == "openai":
            # OpenAI CLI format
            command.extend(["api", "chat.completions.create"])
            if model_config:
                command.extend(["-m", model_config.full_name])
            command.extend(["-g", "user", prompt])
            return command

        elif self.cli_command in ["gemini", "grok"]:
            # Simple format: command --model MODEL prompt
            if model_config:
                command.extend(["--model", model_config.full_name])
            command.append(prompt)
            return command

        elif self.cli_command == "openhands":
            # OpenHands format
            command.extend(["run", prompt])
            if model_config:
                command.extend(["--model", model_config.full_name])
            if self.config.working_dir:
                command.extend(["--workspace", str(self.config.working_dir)])
            return command

        elif self.cli_command == "hanzo":
            # Hanzo dev format
            command.append("dev")
            if model_config:
                command.extend(["--model", model_config.full_name])
            command.extend(["--prompt", prompt])
            return command

        elif self.cli_command == "cline":
            # Cline format
            command.append(prompt)
            command.append("--no-interactive")
            return command

        elif self.cli_command == "aider":
            # Aider format
            if model_config:
                command.extend(["--model", model_config.full_name])
            command.extend(["--message", prompt])
            command.extend(["--yes", "--no-stream"])
            return command

        elif self.cli_command == "ollama":
            # Ollama format for local models
            command.extend(["run", self.config.model.replace("ollama/", "")])
            command.append(prompt)
            return command

        # Default format
        command.append(prompt)
        return command

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        """Execute the CLI tool via MCP interface.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Execution result
        """
        # Update config from params
        if params.get("model"):
            self.config.model = registry.resolve(params["model"])
        if params.get("working_dir"):
            self.config.working_dir = Path(params["working_dir"])
        if params.get("timeout"):
            self.config.timeout = params["timeout"]

        # Execute using base agent
        result = await self.execute(
            params.get("prompt", ""),
            context=ctx,
        )

        return result.content

    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server.

        Args:
            mcp_server: The FastMCP server instance
        """
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def tool_wrapper(
            prompt: str,
            ctx: Context[Any, Any, Any],
            model: Optional[str] = None,
            working_dir: Optional[str] = None,
            timeout: int = 300,
        ) -> str:
            return await tool_self.call(
                ctx,
                prompt=prompt,
                model=model,
                working_dir=working_dir,
                timeout=timeout,
            )


def create_cli_tools(permission_manager: Optional[PermissionManager] = None) -> Dict[str, UnifiedCLITool]:
    """Create all CLI tools with unified implementation.

    Args:
        permission_manager: Permission manager for access control

    Returns:
        Dictionary of tool name to tool instance
    """
    tools = {}

    # Define all tools with their configurations
    tool_configs = [
        ("claude", "Execute Claude CLI for AI assistance", "claude", "claude"),
        ("cc", "Claude Code CLI (alias for claude)", "claude", "claude"),
        ("codex", "Execute OpenAI Codex/GPT-4 CLI", "openai", "gpt-4-turbo"),
        ("gemini", "Execute Google Gemini CLI", "gemini", "gemini"),
        ("grok", "Execute xAI Grok CLI", "grok", "grok"),
        ("openhands", "Execute OpenHands for autonomous coding", "openhands", "claude"),
        ("oh", "OpenHands CLI (alias)", "openhands", "claude"),
        ("hanzo_dev", "Execute Hanzo Dev AI assistant", "hanzo", "claude"),
        ("cline", "Execute Cline for autonomous coding", "cline", "claude"),
        ("aider", "Execute Aider for AI pair programming", "aider", "gpt-4-turbo"),
    ]

    for name, description, cli_command, default_model in tool_configs:
        tools[name] = UnifiedCLITool(
            name=name,
            description=description,
            cli_command=cli_command,
            default_model=default_model,
            permission_manager=permission_manager,
        )

    return tools


def register_cli_tools(
    mcp_server: FastMCP,
    permission_manager: Optional[PermissionManager] = None,
) -> List[BaseTool]:
    """Register all CLI tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control

    Returns:
        List of registered CLI tools
    """
    tools = create_cli_tools(permission_manager)

    # Register each tool
    for tool in tools.values():
        tool.register(mcp_server)

    return list(tools.values())


__all__ = [
    "UnifiedCLITool",
    "create_cli_tools",
    "register_cli_tools",
]
