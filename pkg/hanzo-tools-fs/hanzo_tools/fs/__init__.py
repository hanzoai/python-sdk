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
    pip install hanzo-tools-fs

Usage:
    from hanzo_tools.fs import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server, permission_manager)

    # Or access individual tools
    from hanzo_tools.fs import ReadTool, WriteTool
"""

from hanzo_tools.fs.ast import ASTTool
from hanzo_tools.fs.edit import EditTool
from hanzo_tools.fs.find import FindTool
from hanzo_tools.fs.read import ReadTool
from hanzo_tools.fs.tree import TreeTool
from hanzo_tools.fs.write import WriteTool
from hanzo_tools.fs.search import SearchTool

# Backwards compatibility aliases
Edit = EditTool
Read = ReadTool
Write = WriteTool

# Read-only tools (for agent sandboxing)
READ_ONLY_TOOLS = [
    ReadTool,
    TreeTool,
    FindTool,
    SearchTool,
    ASTTool,
]

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
    # Aliases
    "Edit",
    "Read",
    "Write",
    # Registration
    "register_tools",
    "get_read_only_filesystem_tools",
    "TOOLS",
    "READ_ONLY_TOOLS",
]


def get_read_only_filesystem_tools(permission_manager) -> list:
    """Get read-only filesystem tools for sandboxed agents.

    Returns tools that can only read files, not modify them:
    - read: Read file contents
    - tree: View directory structure
    - find: Find files by pattern
    - search: Search file contents
    - ast: Code structure analysis

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
        tool_name = tool_class.name if hasattr(tool_class, "name") else tool_class.__name__.lower()

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
