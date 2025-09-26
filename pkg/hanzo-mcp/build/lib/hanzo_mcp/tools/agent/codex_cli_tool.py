"""OpenAI Codex CLI agent tool.

This tool provides integration with OpenAI's CLI (openai command),
allowing programmatic execution of GPT-4 and other models for code tasks.
"""

from typing import List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.cli_agent_base import CLIAgentBase


@final
class CodexCLITool(CLIAgentBase):
    """Tool for executing OpenAI CLI (formerly Codex)."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Codex CLI tool.

        Args:
            permission_manager: Permission manager for access control
            model: Optional model override (defaults to gpt-4o)
            **kwargs: Additional arguments
        """
        super().__init__(
            permission_manager=permission_manager,
            command_name="openai",
            provider_name="OpenAI",
            default_model=model or "gpt-4o",
            env_vars=["OPENAI_API_KEY"],
            **kwargs,
        )

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "codex_cli"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Execute OpenAI CLI for code generation and analysis.

This tool runs the OpenAI CLI (openai command) for code generation,
completion, and analysis tasks. It uses GPT-4o by default but supports
all OpenAI models.

Features:
- GPT-4 and GPT-4o for advanced reasoning
- Code generation and completion
- Multi-modal support (with gpt-4-vision)
- Function calling capabilities

Usage:
codex_cli(prompts="Generate a Python function to sort a binary tree")
codex_cli(prompts="Explain this code and suggest improvements", model="gpt-4-turbo")

Requirements:
- OpenAI CLI must be installed: pip install openai
- OPENAI_API_KEY environment variable
"""

    @override
    def get_cli_args(self, prompt: str, **kwargs) -> List[str]:
        """Get CLI arguments for OpenAI.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments (model, temperature, etc.)

        Returns:
            List of command arguments
        """
        args = ["api", "chat.completions.create"]

        # Add model
        model = kwargs.get("model", self.default_model)
        args.extend(["-m", model])

        # Add temperature if specified
        if "temperature" in kwargs:
            args.extend(["--temperature", str(kwargs["temperature"])])

        # Add max tokens if specified
        if "max_tokens" in kwargs:
            args.extend(["--max-tokens", str(kwargs["max_tokens"])])

        # Add the prompt as a message
        args.extend(["-g", prompt])

        return args

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def codex_cli(
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
