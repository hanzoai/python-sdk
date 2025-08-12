"""Google Gemini CLI agent tool.

This tool provides integration with Google's Gemini CLI,
allowing programmatic execution of Gemini models for code tasks.
"""

from typing import List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.cli_agent_base import CLIAgentBase


@final
class GeminiCLITool(CLIAgentBase):
    """Tool for executing Google Gemini CLI."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Gemini CLI tool.

        Args:
            permission_manager: Permission manager for access control
            model: Optional model override (defaults to gemini-1.5-pro)
            **kwargs: Additional arguments
        """
        super().__init__(
            permission_manager=permission_manager,
            command_name="gemini",
            provider_name="Google Gemini",
            default_model=model or "gemini-1.5-pro",
            env_vars=["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            **kwargs,
        )

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "gemini_cli"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Execute Google Gemini CLI for code tasks.

This tool runs the Google Gemini CLI for code generation, analysis,
and multi-modal tasks. It uses Gemini 1.5 Pro by default.

Features:
- Gemini 1.5 Pro with 2M token context window
- Gemini 1.5 Flash for faster responses
- Multi-modal capabilities (code + images)
- Advanced reasoning and analysis

Usage:
gemini_cli(prompts="Create a React component for a data table")
gemini_cli(prompts="Analyze this code for security vulnerabilities", model="gemini-1.5-flash")

Requirements:
- Gemini CLI must be installed
- GOOGLE_API_KEY or GEMINI_API_KEY environment variable
"""

    @override
    def get_cli_args(self, prompt: str, **kwargs) -> List[str]:
        """Get CLI arguments for Gemini.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments (model, temperature, etc.)

        Returns:
            List of command arguments
        """
        args = ["generate"]

        # Add model
        model = kwargs.get("model", self.default_model)
        args.extend(["--model", model])

        # Add temperature if specified
        if "temperature" in kwargs:
            args.extend(["--temperature", str(kwargs["temperature"])])

        # Add max tokens if specified
        if "max_tokens" in kwargs:
            args.extend(["--max-output-tokens", str(kwargs["max_tokens"])])

        # Add safety settings if needed
        if kwargs.get("safety_settings"):
            args.extend(["--safety-settings", kwargs["safety_settings"]])

        # Add the prompt
        args.extend(["--prompt", prompt])

        return args

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def gemini_cli(
            ctx: MCPContext,
            prompts: str,
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            working_dir: Optional[str] = None,
            safety_settings: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                prompts=prompts,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                working_dir=working_dir,
                safety_settings=safety_settings,
            )
