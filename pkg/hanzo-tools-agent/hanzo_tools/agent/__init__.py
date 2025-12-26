"""Agent tools for Hanzo AI.

This package provides agent orchestration and multi-agent tools:
- agent: Agent spawning and orchestration
- swarm: Multi-agent swarm coordination
- CLI agents: Claude, Codex, Gemini, Grok CLI tools
- critic: Critical analysis tool
- review: Code review tool

Install:
    pip install hanzo-tools-agent

Usage:
    from hanzo_tools.agent import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

Optional dependencies:
    pip install hanzo-tools-agent[full]  # For LLM provider support
"""

import logging

logger = logging.getLogger(__name__)

# Core tools that don't have external dependencies
from .critic_tool import CriticTool
from .iching_tool import IChingTool
from .review_tool import ReviewTool
from .network_tool import NetworkTool
from .grok_cli_tool import GrokCLITool

# CLI agent tools
from .cli_agent_base import CLIAgentBase
from .code_auth_tool import CodeAuthTool
from .codex_cli_tool import CodexCLITool
from .claude_cli_tool import ClaudeCLITool
from .gemini_cli_tool import GeminiCLITool
from .clarification_tool import ClarificationTool

# Tools with optional dependencies - imported lazily
_optional_tools = []

try:
    from .agent_tool import AgentTool

    _optional_tools.append(AgentTool)
except ImportError as e:
    logger.debug(f"AgentTool not available: {e}")

try:
    from .swarm_tool import SwarmTool

    _optional_tools.append(SwarmTool)
except ImportError as e:
    logger.debug(f"SwarmTool not available: {e}")

# Export list for tool discovery
TOOLS = [
    CriticTool,
    IChingTool,
    ReviewTool,
    ClarificationTool,
    NetworkTool,
    CodeAuthTool,
    ClaudeCLITool,
    CodexCLITool,
    GeminiCLITool,
    GrokCLITool,
] + _optional_tools

__all__ = [
    "register_tools",
    "TOOLS",
    "CriticTool",
    "IChingTool",
    "ReviewTool",
    "ClarificationTool",
    "NetworkTool",
    "CodeAuthTool",
    "CLIAgentBase",
    "ClaudeCLITool",
    "CodexCLITool",
    "GeminiCLITool",
    "GrokCLITool",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register all agent tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tool instances
    """
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, "name") else tool_class.__name__.lower()

        if enabled.get(tool_name, True):  # Enabled by default
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")

    return registered
