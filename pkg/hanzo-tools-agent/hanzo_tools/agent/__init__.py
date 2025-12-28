"""Agent tools for Hanzo AI.

Provides consolidated agent tools:
- agent: Multi-agent orchestration (run, dag, swarm, consensus, dispatch)
- iching: I Ching wisdom for decisions
- review: Code review tool

Install:
    pip install hanzo-tools-agent

Usage:
    from hanzo_tools.agent import register_tools, TOOLS, AgentTool

    # Register with MCP server
    register_tools(mcp_server)

Consensus: https://github.com/luxfi/consensus
"""

import logging

logger = logging.getLogger(__name__)

# Core tools
from .agent_tool import AgentTool

# Legacy imports for backwards compatibility
from .critic_tool import CriticTool  # Legacy - use reasoning.critic instead
from .iching_tool import IChingTool
from .review_tool import ReviewTool
from .grok_cli_tool import GrokCLITool
from .cli_agent_base import CLIAgentBase
from .codex_cli_tool import CodexCLITool
from .claude_cli_tool import ClaudeCLITool
from .gemini_cli_tool import GeminiCLITool

# Export list for tool discovery
TOOLS = [
    AgentTool,   # Multi-agent orchestration
    IChingTool,  # I Ching wisdom
    ReviewTool,  # Code review
]

__all__ = [
    "register_tools",
    "TOOLS",
    # Primary tools
    "AgentTool",
    "IChingTool",
    "ReviewTool",
    # Legacy (for backwards compatibility)
    "CriticTool",
    "CLIAgentBase",
    "ClaudeCLITool",
    "CodexCLITool",
    "GeminiCLITool",
    "GrokCLITool",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register agent tools with the MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, "name") else tool_class.__name__.lower()

        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")

    return registered
