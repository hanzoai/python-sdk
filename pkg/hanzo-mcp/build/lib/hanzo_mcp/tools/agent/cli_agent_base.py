"""Base class for CLI-based AI agent tools.

This provides common functionality for spawning CLI-based AI coding assistants
like Claude Code, OpenAI Codex, Google Gemini, and Grok.
"""

import os
import shutil
import asyncio
import tempfile
from abc import abstractmethod
from typing import List, Optional

from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.common.permissions import PermissionManager


class CLIAgentBase(BaseTool):
    """Base class for CLI-based AI agent tools."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        command_name: str,
        provider_name: str,
        default_model: Optional[str] = None,
        env_vars: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize CLI agent base.

        Args:
            permission_manager: Permission manager for access control
            command_name: The CLI command name (e.g., 'claude', 'openai')
            provider_name: The provider name (e.g., 'Claude', 'OpenAI')
            default_model: Default model to use
            env_vars: List of environment variables to check for API keys
            **kwargs: Additional arguments
        """
        self.permission_manager = permission_manager
        self.command_name = command_name
        self.provider_name = provider_name
        self.default_model = default_model
        self.env_vars = env_vars or []

    def is_installed(self) -> bool:
        """Check if the CLI tool is installed."""
        return shutil.which(self.command_name) is not None

    def has_api_key(self) -> bool:
        """Check if API key is available in environment."""
        if not self.env_vars:
            return True  # No API key needed

        for var in self.env_vars:
            if os.environ.get(var):
                return True
        return False

    @abstractmethod
    def get_cli_args(self, prompt: str, **kwargs) -> List[str]:
        """Get CLI arguments for the specific tool.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments

        Returns:
            List of command arguments
        """
        pass

    async def execute_cli(
        self,
        ctx: MCPContext,
        prompt: str,
        working_dir: Optional[str] = None,
        timeout: int = 300,
        **kwargs,
    ) -> str:
        """Execute the CLI command.

        Args:
            ctx: MCP context
            prompt: The prompt to send
            working_dir: Working directory for the command
            timeout: Command timeout in seconds
            **kwargs: Additional arguments

        Returns:
            Command output
        """
        tool_ctx = create_tool_context(ctx)

        # Check if installed
        if not self.is_installed():
            error_msg = f"{self.provider_name} CLI ({self.command_name}) is not installed. "
            error_msg += f"Please install it first: https://github.com/anthropics/{self.command_name}"
            await tool_ctx.error(error_msg)
            return f"Error: {error_msg}"

        # Check API key if needed
        if not self.has_api_key():
            error_msg = f"No API key found for {self.provider_name}. "
            error_msg += f"Set one of: {', '.join(self.env_vars)}"
            await tool_ctx.error(error_msg)
            return f"Error: {error_msg}"

        # Get command arguments
        cli_args = self.get_cli_args(prompt, **kwargs)

        # Log command
        await tool_ctx.info(f"Executing {self.provider_name}: {self.command_name} {' '.join(cli_args[:3])}...")

        try:
            # Create temp file for prompt if needed
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            # Some CLIs might need the prompt via stdin or file
            if "--prompt-file" in cli_args:
                # Replace placeholder with actual file
                cli_args = [
                    (arg.replace("--prompt-file", prompt_file) if arg == "--prompt-file" else arg) for arg in cli_args
                ]

            # Execute command
            process = await asyncio.create_subprocess_exec(
                self.command_name,
                *cli_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                cwd=working_dir or os.getcwd(),
            )

            # Send prompt via stdin if not using file
            if "--prompt-file" not in cli_args:
                stdout, stderr = await asyncio.wait_for(process.communicate(input=prompt.encode()), timeout=timeout)
            else:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            # Clean up temp file
            try:
                os.unlink(prompt_file)
            except Exception:
                pass

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                await tool_ctx.error(f"{self.provider_name} failed: {error_msg}")
                return f"Error: {error_msg}"

            result = stdout.decode()
            await tool_ctx.info(f"{self.provider_name} completed successfully")
            return result

        except asyncio.TimeoutError:
            await tool_ctx.error(f"{self.provider_name} timed out after {timeout} seconds")
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            await tool_ctx.error(f"{self.provider_name} error: {str(e)}")
            return f"Error: {str(e)}"

    async def call(self, ctx: MCPContext, prompts: str, **kwargs) -> str:
        """Execute the CLI agent.

        Args:
            ctx: MCP context
            prompts: The prompt(s) to send
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        return await self.execute_cli(ctx, prompts, **kwargs)
