"""Reasoning and critical analysis tools for Hanzo MCP.

This package provides tools for structured reasoning:
- ThinkTool: Structured thinking and brainstorming
- CriticTool: Critical analysis and code review
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.reasoning.think_tool import ThinkTool
from hanzo_tools.reasoning.critic_tool import CriticTool

__all__ = [
    "ThinkTool",
    "CriticTool",
    "get_reasoning_tools",
    "register_reasoning_tools",
    "TOOLS",
]


def get_reasoning_tools() -> list[BaseTool]:
    """Create instances of all reasoning tools.

    Returns:
        List of reasoning tool instances
    """
    return [ThinkTool(), CriticTool()]


def register_reasoning_tools(mcp_server: FastMCP) -> list[BaseTool]:
    """Register all reasoning tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance

    Returns:
        List of registered tools
    """
    tools = get_reasoning_tools()
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery
TOOLS = [ThinkTool, CriticTool]
