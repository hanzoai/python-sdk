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

# Read-only tools (for agent sandboxing) - jupyter is read-only by default
READ_ONLY_TOOLS = [JupyterTool]

__all__ = [
    "JupyterTool",
    "register_tools",
    "get_read_only_jupyter_tools",
    "TOOLS",
    "READ_ONLY_TOOLS",
]


def get_read_only_jupyter_tools(permission_manager) -> list:
    """Get read-only jupyter tools for sandboxed agents.

    Returns tools that can read jupyter notebooks:
    - jupyter: Read and analyze notebook contents

    Args:
        permission_manager: PermissionManager instance

    Returns:
        List of instantiated read-only tools
    """
    tools = []
    for tool_class in READ_ONLY_TOOLS:
        try:
            tools.append(tool_class(permission_manager))
        except TypeError:
            tools.append(tool_class())
    return tools


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
        tool_name = tool_class.name if hasattr(tool_class, "name") else tool_class.__name__.lower()
        if enabled.get(tool_name, True):  # Enabled by default
            tool = tool_class(permission_manager)
            ToolRegistry.register_tool(mcp_server, tool)
            registered.append(tool)

    return registered
