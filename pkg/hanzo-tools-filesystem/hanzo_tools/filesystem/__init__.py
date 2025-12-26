"""Filesystem tools for Hanzo AI.

Tools:
- read: Read file contents
- write: Write/create files
- edit: Edit files with find/replace
- multi_edit: Multiple edits in one operation
- tree: Directory tree view
- find: Find files by pattern
- search: Search file contents
- ast: AST-based code search
- rules: Read project rules/config

Install:
    pip install hanzo-tools-filesystem

Usage:
    from hanzo_tools.filesystem import register_tools, TOOLS
    
    # Register with MCP server
    register_tools(mcp_server, permission_manager)
    
    # Or access individual tools
    from hanzo_tools.filesystem import ReadTool, WriteTool
"""

from hanzo_tools.filesystem.ast import ASTTool
from hanzo_tools.filesystem.edit import EditTool
from hanzo_tools.filesystem.find import FindTool
from hanzo_tools.filesystem.read import ReadTool
from hanzo_tools.filesystem.tree import TreeTool
from hanzo_tools.filesystem.write import WriteTool
from hanzo_tools.filesystem.search import SearchTool

# Export list for tool discovery
TOOLS = [
    ReadTool,
    WriteTool,
    EditTool,
    TreeTool,
    FindTool,
    SearchTool,
    ASTTool,
]

__all__ = [
    # Tool classes
    "ReadTool",
    "WriteTool", 
    "EditTool",
    "TreeTool",
    "FindTool",
    "SearchTool",
    "ASTTool",
    # Registration
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, permission_manager, enabled_tools: dict[str, bool] | None = None):
    """Register all filesystem tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
        permission_manager: PermissionManager for access control
        enabled_tools: Dict of tool_name -> enabled state
        
    Returns:
        List of registered tool instances
    """
    from hanzo_tools.core import ToolRegistry
    
    enabled = enabled_tools or {}
    registered = []
    
    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, 'name') else tool_class.__name__.lower()
        
        if enabled.get(tool_name, True):  # Enabled by default
            try:
                tool = tool_class(permission_manager)
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except TypeError:
                # Tool doesn't need permission_manager
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
    
    return registered
