"""Memory tools for Hanzo MCP.

External MCP surface is intentionally one tool: `memory`.
Default backend is local markdown context + session persistence, with optional
hanzo-memory backends for cloud/vector/graph storage.
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.memory.memory_tool import MemoryTool

__all__ = [
    "MemoryTool",
    # Registration helpers
    "get_memory_tools",
    "register_memory_tools",
    "TOOLS",
]


def get_memory_tools(
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Create memory tool instances (single-tool surface)."""
    return [MemoryTool(user_id=user_id, project_id=project_id, **kwargs)]


def register_memory_tools(
    mcp_server: FastMCP,
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Register memory tools with the MCP server."""
    tools = get_memory_tools(user_id=user_id, project_id=project_id, **kwargs)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery — single `memory` tool surface
TOOLS = [MemoryTool]
