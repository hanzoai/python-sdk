"""Database tools for Hanzo AI.

This package provides tools for working with embedded SQLite databases
and graph databases in projects.

Tools:
- sql_query: Execute SQL queries
- sql_search: Search database content
- sql_stats: Get database statistics
- graph_add: Add nodes/edges to graph
- graph_remove: Remove from graph
- graph_query: Query graph database
- graph_search: Search graph
- graph_stats: Graph statistics

Install:
    pip install hanzo-tools-database

Usage:
    from hanzo_tools.database import register_tools, TOOLS
    
    # Register with MCP server
    register_tools(mcp_server, permission_manager)
"""

from hanzo_tools.core import BaseTool, PermissionManager, ToolRegistry

from .database_manager import DatabaseManager
from .sql_query import SqlQueryTool
from .sql_stats import SqlStatsTool
from .sql_search import SqlSearchTool
from .graph_add import GraphAddTool
from .graph_query import GraphQueryTool
from .graph_stats import GraphStatsTool
from .graph_remove import GraphRemoveTool
from .graph_search import GraphSearchTool

# Export list for tool discovery
TOOLS = [
    SqlQueryTool,
    SqlSearchTool,
    SqlStatsTool,
    GraphAddTool,
    GraphRemoveTool,
    GraphQueryTool,
    GraphSearchTool,
    GraphStatsTool,
]

__all__ = [
    "register_tools",
    "TOOLS",
    "DatabaseManager",
    "SqlQueryTool",
    "SqlSearchTool",
    "SqlStatsTool",
    "GraphAddTool",
    "GraphRemoveTool",
    "GraphQueryTool",
    "GraphSearchTool",
    "GraphStatsTool",
]


def register_tools(
    mcp_server,
    permission_manager: PermissionManager,
    db_manager: DatabaseManager | None = None,
    enabled_tools: dict[str, bool] | None = None,
) -> list[BaseTool]:
    """Register database tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        db_manager: Optional database manager instance
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tools
    """
    # Create database manager if not provided
    if db_manager is None:
        db_manager = DatabaseManager(permission_manager)

    enabled = enabled_tools or {}
    registered = []

    # Create and register tool instances
    tool_instances = [
        SqlQueryTool(permission_manager, db_manager),
        SqlSearchTool(permission_manager, db_manager),
        SqlStatsTool(permission_manager, db_manager),
        GraphAddTool(permission_manager, db_manager),
        GraphRemoveTool(permission_manager, db_manager),
        GraphQueryTool(permission_manager, db_manager),
        GraphSearchTool(permission_manager, db_manager),
        GraphStatsTool(permission_manager, db_manager),
    ]

    for tool in tool_instances:
        tool_name = tool.name if hasattr(tool, 'name') else tool.__class__.__name__.lower()
        if enabled.get(tool_name, True):  # Enabled by default
            ToolRegistry.register_tool(mcp_server, tool)
            registered.append(tool)

    return registered
