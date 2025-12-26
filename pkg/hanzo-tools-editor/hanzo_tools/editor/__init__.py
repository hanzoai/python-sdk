"""Editor integration tools for Hanzo AI.

Tools:
- neovim_edit: Edit files in Neovim
- neovim_command: Execute Neovim commands
- neovim_session: Manage Neovim sessions

Install:
    pip install hanzo-tools-editor
    pip install hanzo-tools-editor[neovim]  # For Neovim support

Usage:
    from hanzo_tools.editor import register_tools, TOOLS
    
    # Register with MCP server
    register_tools(mcp_server)
"""

from hanzo_tools.core import BaseTool, ToolRegistry
from .neovim_edit import NeovimEditTool
from .neovim_command import NeovimCommandTool
from .neovim_session import NeovimSessionTool

# Export list for tool discovery
TOOLS = [
    NeovimEditTool,
    NeovimCommandTool,
    NeovimSessionTool,
]

__all__ = [
    "NeovimEditTool",
    "NeovimCommandTool",
    "NeovimSessionTool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register all editor tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tool instances
    """
    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, 'name') else tool_class.__name__.lower()
        if enabled.get(tool_name, True):  # Enabled by default
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception:
                pass  # Tool may require optional deps

    return registered
