"""Jupyter notebook tools for Hanzo AI.

Tools:
- jupyter: Read, edit, and execute Jupyter notebooks

Install:
    pip install hanzo-tools-jupyter

Usage:
    from hanzo_tools.jupyter import register_tools, TOOLS
    
    # Register with MCP server
    register_tools(mcp_server, permission_manager)
"""

from hanzo_tools.core import BaseTool, ToolRegistry, PermissionManager
from .jupyter import JupyterTool

# Export list for tool discovery
TOOLS = [JupyterTool]

__all__ = [
    "JupyterTool",
    "register_tools",
    "TOOLS",
]


def register_tools(
    mcp_server,
    permission_manager: PermissionManager,
    enabled_tools: dict[str, bool] | None = None,
) -> list[BaseTool]:
    """Register Jupyter notebook tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tools
    """
    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, 'name') else tool_class.__name__.lower()
        if enabled.get(tool_name, True):  # Enabled by default
            tool = tool_class(permission_manager)
            ToolRegistry.register_tool(mcp_server, tool)
            registered.append(tool)

    return registered
