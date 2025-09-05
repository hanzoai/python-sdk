"""Grok CLI agent tool.

This tool provides integration with xAI's Grok CLI,
allowing programmatic execution of Grok models for code tasks.
"""

from typing import List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.cli_agent_base import CLIAgentBase


@final
class GrokCLITool(CLIAgentBase):
    """Tool for executing Grok CLI."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Grok CLI tool.

        Args:
            permission_manager: Permission manager for access control
            model: Optional model override (defaults to grok-2)
            **kwargs: Additional arguments
        """
        super().__init__(
            permission_manager=permission_manager,
            command_name="grok",
            provider_name="xAI Grok",
            default_model=model or "grok-2",
            env_vars=["XAI_API_KEY", "GROK_API_KEY"],
            **kwargs,
        )

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "grok_cli"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Execute xAI Grok CLI for code tasks.

This tool runs the Grok CLI for code generation, analysis,
and reasoning tasks. It uses Grok-2 by default.

Features:
- Grok-2 with advanced reasoning capabilities
- Real-time information access
- Code generation and analysis
- Humor and personality in responses

Usage:
grok_cli(prompts="Write a Python web scraper with async support")
grok_cli(prompts="Explain quantum computing like I'm a programmer", model="grok-1")

Requirements:
- Grok CLI must be installed
- XAI_API_KEY or GROK_API_KEY environment variable
"""

    @override
    def get_cli_args(self, prompt: str, **kwargs) -> List[str]:
        """Get CLI arguments for Grok.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments (model, temperature, etc.)

        Returns:
            List of command arguments
        """
        args = ["chat"]

        # Add model
        model = kwargs.get("model", self.default_model)
        args.extend(["--model", model])

        # Add temperature if specified
        if "temperature" in kwargs:
            args.extend(["--temperature", str(kwargs["temperature"])])

        # Add max tokens if specified
        if "max_tokens" in kwargs:
            args.extend(["--max-tokens", str(kwargs["max_tokens"])])

        # Add system prompt if specified
        if "system_prompt" in kwargs:
            args.extend(["--system", kwargs["system_prompt"]])

        # Add the prompt
        args.append(prompt)

        return args

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def grok_cli(
            ctx: MCPContext,
            prompts: str,
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            working_dir: Optional[str] = None,
            system_prompt: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                prompts=prompts,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                working_dir=working_dir,
                system_prompt=system_prompt,
            )
