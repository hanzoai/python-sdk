"""Shell tools package for Hanzo AI.

This package provides tools for executing shell commands and scripts.
"""

from mcp.server import FastMCP

from hanzo_mcp.tools.shell.open import open_tool
from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.shell.npx_tool import npx_tool
from hanzo_mcp.tools.shell.uvx_tool import uvx_tool

# Import tools
from hanzo_mcp.tools.shell.bash_tool import bash_tool
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.shell.process_tool import process_tool

# from hanzo_mcp.tools.shell.streaming_command import StreamingCommandTool

# Export all tool classes
__all__ = [
    "get_shell_tools",
    "register_shell_tools",
]


def get_shell_tools(
    permission_manager: PermissionManager,
) -> list[BaseTool]:
    """Create instances of all shell tools.

    Args:
        permission_manager: Permission manager for access control

    Returns:
        List of shell tool instances
    """
    # Set permission manager for tools that need it
    bash_tool.permission_manager = permission_manager
    npx_tool.permission_manager = permission_manager
    uvx_tool.permission_manager = permission_manager

    # Note: StreamingCommandTool is abstract and shouldn't be instantiated directly
    # It's used as a base class for other streaming tools

    return [
        bash_tool,
        npx_tool,
        uvx_tool,
        process_tool,
        open_tool,
        # streaming_command_tool,  # Removed as it's abstract
    ]


def register_shell_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
) -> list[BaseTool]:
    """Register all shell tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control

    Returns:
        List of registered tools
    """
    tools = get_shell_tools(permission_manager)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools
