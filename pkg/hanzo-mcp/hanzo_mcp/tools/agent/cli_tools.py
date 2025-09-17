"""CLI tool implementations for direct batch execution.

This module provides CLI tool wrappers that can be used directly in batch operations,
including claude (cc), codex, gemini, grok, openhands (oh), hanzo-dev, cline, and aider.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Unpack, Optional, Annotated, TypedDict, final, override
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.common.permissions import PermissionManager

# Parameter types for CLI tools
Prompt = Annotated[
    str,
    Field(
        description="The prompt or command to send to the CLI tool",
        min_length=1,
    ),
]

Model = Annotated[
    Optional[str],
    Field(
        description="Optional model override for the CLI tool",
        default=None,
    ),
]

WorkingDir = Annotated[
    Optional[str],
    Field(
        description="Working directory for the command",
        default=None,
    ),
]

Timeout = Annotated[
    Optional[int],
    Field(
        description="Timeout in seconds for the command",
        default=300,  # 5 minutes default
    ),
]


class CLIToolParams(TypedDict, total=False):
    """Common parameters for CLI tools."""

    prompt: str
    model: Optional[str]
    working_dir: Optional[str]
    timeout: Optional[int]


class BaseCLITool(BaseTool):
    """Base class for CLI tool implementations."""

    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        default_model: Optional[str] = None,
        api_key_env: Optional[str] = None,
    ):
        """Initialize CLI tool.

        Args:
            permission_manager: Permission manager for access control
            default_model: Default model to use
            api_key_env: Environment variable name for API key
        """
        self.permission_manager = permission_manager
        self.default_model = default_model
        self.api_key_env = api_key_env

    def get_auth_env(self) -> dict[str, str]:
        """Get authentication environment variables."""
        env = os.environ.copy()

        # Add API key if configured
        if self.api_key_env and self.api_key_env in os.environ:
            env[self.api_key_env] = os.environ[self.api_key_env]

        # Add Hanzo API key for unified auth
        if "HANZO_API_KEY" in os.environ:
            env["HANZO_API_KEY"] = os.environ["HANZO_API_KEY"]

        return env

    async def execute_cli(
        self,
        command: list[str],
        input_text: Optional[str] = None,
        working_dir: Optional[str] = None,
        timeout: int = 300,
    ) -> str:
        """Execute CLI command with proper error handling.

        Args:
            command: Command and arguments
            input_text: Optional stdin input
            working_dir: Working directory
            timeout: Timeout in seconds

        Returns:
            Command output
        """
        try:
            # Set up environment with auth
            env = self.get_auth_env()

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE if input_text else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env,
            )

            # Send input and get output
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input_text.encode() if input_text else None),
                timeout=timeout,
            )

            # Check for errors
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return f"Error: {error_msg}"

            return stdout.decode()

        except asyncio.TimeoutError:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server.

        Args:
            mcp_server: The FastMCP server instance
        """
        tool_self = self  # Create a reference to self for use in the closure

        @mcp_server.tool(name=self.name, description=self.description)
        async def tool_wrapper(
            prompt: str,
            ctx: Context[Any, Any, Any],
            model: Optional[str] = None,
            working_dir: Optional[str] = None,
            timeout: int = 300,
        ) -> str:
            result: str = await tool_self.call(
                ctx, prompt=prompt, model=model, working_dir=working_dir, timeout=timeout
            )
            return result


class ClaudeCLITool(BaseCLITool):
    """Claude CLI tool (also available as 'cc' alias)."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="claude-3-5-sonnet-20241022",
            api_key_env="ANTHROPIC_API_KEY",
        )

    @property
    def name(self) -> str:
        return "claude"

    @property
    def description(self) -> str:
        return "Execute Claude CLI for AI assistance using Anthropic's models"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt: str = params.get("prompt", "")
        model: Optional[str] = params.get("model") or self.default_model
        working_dir: Optional[str] = params.get("working_dir")
        timeout: int = params.get("timeout", 300)

        # Build command
        command: list[str] = ["claude"]
        if model:
            command.extend(["--model", model])

        # Execute
        return await self.execute_cli(
            command,
            input_text=prompt,
            working_dir=working_dir,
            timeout=timeout,
        )


class ClaudeCodeCLITool(ClaudeCLITool):
    """Claude Code CLI tool (cc alias)."""

    @property
    def name(self) -> str:
        return "cc"

    @property
    def description(self) -> str:
        return "Claude Code CLI (alias for claude)"


class CodexCLITool(BaseCLITool):
    """OpenAI Codex/GPT-4 CLI tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="gpt-4-turbo",
            api_key_env="OPENAI_API_KEY",
        )

    @property
    def name(self) -> str:
        return "codex"

    @property
    def description(self) -> str:
        return "Execute OpenAI Codex/GPT-4 CLI for code generation and AI assistance"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt: str = params.get("prompt", "")
        model: Optional[str] = params.get("model") or self.default_model
        working_dir: Optional[str] = params.get("working_dir")
        timeout: int = params.get("timeout", 300)

        # Build command (using openai CLI or custom wrapper)
        command: list[str] = ["openai", "api", "chat.completions.create"]
        if model:
            command.extend(["-m", model])
        command.extend(["-g", "user", prompt])

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class GeminiCLITool(BaseCLITool):
    """Google Gemini CLI tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="gemini-1.5-pro",
            api_key_env="GEMINI_API_KEY",
        )

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def description(self) -> str:
        return "Execute Google Gemini CLI for multimodal AI assistance"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt: str = params.get("prompt", "")
        model: Optional[str] = params.get("model") or self.default_model
        working_dir: Optional[str] = params.get("working_dir")
        timeout: int = params.get("timeout", 300)

        # Build command
        command: list[str] = ["gemini"]
        if model:
            command.extend(["--model", model])
        command.append(prompt)

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class GrokCLITool(BaseCLITool):
    """xAI Grok CLI tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="grok-4",
            api_key_env="XAI_API_KEY",
        )

    @property
    def name(self) -> str:
        return "grok"

    @property
    def description(self) -> str:
        return "Execute xAI Grok CLI for real-time AI assistance"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt: str = params.get("prompt", "")
        model: Optional[str] = params.get("model") or self.default_model
        working_dir: Optional[str] = params.get("working_dir")
        timeout: int = params.get("timeout", 300)

        # Build command
        command: list[str] = ["grok"]
        if model:
            command.extend(["--model", model])
        command.append(prompt)

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class OpenHandsCLITool(BaseCLITool):
    """OpenHands (OpenDevin) CLI tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="claude-3-5-sonnet-20241022",
            api_key_env="OPENAI_API_KEY",
        )

    @property
    def name(self) -> str:
        return "openhands"

    @property
    def description(self) -> str:
        return "Execute OpenHands (OpenDevin) for autonomous coding assistance"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt = params.get("prompt", "")
        model = params.get("model") or self.default_model
        working_dir: str = params.get("working_dir") or os.getcwd()
        timeout: int = params.get("timeout", 600)  # 10 minutes for OpenHands

        # Build command
        command: list[str] = ["openhands", "run", prompt]
        if model:
            command.extend(["--model", model])
        command.extend(["--workspace", working_dir])

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class OpenHandsShortCLITool(OpenHandsCLITool):
    """OpenHands CLI tool (oh alias)."""

    @property
    def name(self) -> str:
        return "oh"

    @property
    def description(self) -> str:
        return "OpenHands CLI (alias for openhands)"


class HanzoDevCLITool(BaseCLITool):
    """Hanzo Dev AI coding assistant."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="claude-3-5-sonnet-20241022",
            api_key_env="HANZO_API_KEY",
        )

    @property
    def name(self) -> str:
        return "hanzo_dev"

    @property
    def description(self) -> str:
        return "Execute Hanzo Dev for AI-powered code editing and development"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt = params.get("prompt", "")
        model = params.get("model") or self.default_model
        working_dir: str = params.get("working_dir") or os.getcwd()
        timeout: int = params.get("timeout", 600)

        # Build command
        command: list[str] = ["dev"]
        if model:
            command.extend(["--model", model])
        command.extend(["--prompt", prompt])

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class ClineCLITool(BaseCLITool):
    """Cline (formerly Claude Engineer) CLI tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="claude-3-5-sonnet-20241022",
            api_key_env="ANTHROPIC_API_KEY",
        )

    @property
    def name(self) -> str:
        return "cline"

    @property
    def description(self) -> str:
        return "Execute Cline for autonomous coding with Claude"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt = params.get("prompt", "")
        working_dir: str = params.get("working_dir") or os.getcwd()
        timeout: int = params.get("timeout", 600)

        # Build command
        command: list[str] = ["cline", prompt]
        command.extend(["--no-interactive"])  # Non-interactive mode for batch

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


class AiderCLITool(BaseCLITool):
    """Aider AI pair programming tool."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(
            permission_manager=permission_manager,
            default_model="gpt-4-turbo",
            api_key_env="OPENAI_API_KEY",
        )

    @property
    def name(self) -> str:
        return "aider"

    @property
    def description(self) -> str:
        return "Execute Aider for AI pair programming"

    async def call(self, ctx: Context[Any, Any, Any], **params: Any) -> str:
        prompt = params.get("prompt", "")
        model = params.get("model") or self.default_model
        working_dir: str = params.get("working_dir") or os.getcwd()
        timeout: int = params.get("timeout", 600)

        # Build command
        command: list[str] = ["aider"]
        if model:
            command.extend(["--model", model])
        command.extend(["--message", prompt])
        command.extend(["--yes"])  # Auto-approve changes
        command.extend(["--no-stream"])  # No streaming for batch

        # Execute
        return await self.execute_cli(
            command,
            working_dir=working_dir,
            timeout=timeout,
        )


def register_cli_tools(
    mcp_server: FastMCP,
    permission_manager: Optional[PermissionManager] = None,
) -> list[BaseTool]:
    """Register all CLI tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control

    Returns:
        List of registered CLI tools
    """
    tools: list[BaseTool] = [
        ClaudeCLITool(permission_manager),
        ClaudeCodeCLITool(permission_manager),  # cc alias
        CodexCLITool(permission_manager),
        GeminiCLITool(permission_manager),
        GrokCLITool(permission_manager),
        OpenHandsCLITool(permission_manager),
        OpenHandsShortCLITool(permission_manager),  # oh alias
        HanzoDevCLITool(permission_manager),
        ClineCLITool(permission_manager),
        AiderCLITool(permission_manager),
    ]

    # Register each tool
    for tool in tools:
        tool.register(mcp_server)

    return tools


# Export all CLI tool classes
__all__ = [
    "ClaudeCLITool",
    "ClaudeCodeCLITool",
    "CodexCLITool",
    "GeminiCLITool",
    "GrokCLITool",
    "OpenHandsCLITool",
    "OpenHandsShortCLITool",
    "HanzoDevCLITool",
    "ClineCLITool",
    "AiderCLITool",
    "register_cli_tools",
]
