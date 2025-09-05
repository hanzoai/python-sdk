"""Claude Code CLI agent tool.

This tool provides integration with the Claude Code CLI (claude command),
allowing programmatic execution of Claude for code tasks.
"""

from typing import List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.agent.code_auth import get_latest_claude_model
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.cli_agent_base import CLIAgentBase


@final
class ClaudeCLITool(CLIAgentBase):
    """Tool for executing Claude Code CLI."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Claude CLI tool.

        Args:
            permission_manager: Permission manager for access control
            model: Optional model override (defaults to latest Sonnet)
            **kwargs: Additional arguments
        """
        super().__init__(
            permission_manager=permission_manager,
            command_name="claude",
            provider_name="Claude Code",
            default_model=model or get_latest_claude_model(),
            env_vars=["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
            **kwargs,
        )

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "claude_cli"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Execute Claude Code CLI for advanced code tasks.

This tool runs the Claude Code CLI (claude command) for code generation,
editing, analysis, and other programming tasks. It uses the latest
Claude 3.5 Sonnet model by default.

Features:
- Direct access to Claude's coding capabilities
- File-aware context and editing
- Interactive code generation
- Supports all Claude Code CLI features

Usage:
claude_cli(prompts="Fix the bug in main.py and add tests")
claude_cli(prompts="Refactor this class to use dependency injection", model="claude-3-opus-20240229")

Requirements:
- Claude Code CLI must be installed
- ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable
"""

    @override
    def get_cli_args(self, prompt: str, **kwargs) -> List[str]:
        """Get CLI arguments for Claude.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments (model, temperature, etc.)

        Returns:
            List of command arguments
        """
        args = []

        # Add model if specified
        model = kwargs.get("model", self.default_model)
        if model:
            args.extend(["--model", model])

        # Add temperature if specified
        if "temperature" in kwargs:
            args.extend(["--temperature", str(kwargs["temperature"])])

        # Add max tokens if specified
        if "max_tokens" in kwargs:
            args.extend(["--max-tokens", str(kwargs["max_tokens"])])

        # Add the prompt
        args.append(prompt)

        return args

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def claude_cli(
            ctx: MCPContext,
            prompts: str,
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            working_dir: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                prompts=prompts,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                working_dir=working_dir,
            )
