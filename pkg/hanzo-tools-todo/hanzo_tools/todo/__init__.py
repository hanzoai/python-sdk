"""Todo tools for Hanzo MCP.

This package provides task management tools:
- TodoTool: Unified todo management with add, update, remove, list, clear operations
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.todo.base import TodoStorage, TodoBaseTool
from hanzo_tools.todo.todo_tool import TodoTool

__all__ = [
    "TodoTool",
    "TodoStorage",
    "TodoBaseTool",
    "get_todo_tools",
    "register_todo_tools",
    "TOOLS",
]


def get_todo_tools() -> list[BaseTool]:
    """Create instances of all todo tools.

    Returns:
        List of todo tool instances
    """
    return [TodoTool()]


def register_todo_tools(
    mcp_server: FastMCP,
    enabled_tools: dict[str, bool] | None = None,
) -> list[BaseTool]:
    """Register todo tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        enabled_tools: Dictionary of individual tool enable states (default: None)

    Returns:
        List of registered tools
    """
    tools = get_todo_tools()
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery
TOOLS = [TodoTool]
