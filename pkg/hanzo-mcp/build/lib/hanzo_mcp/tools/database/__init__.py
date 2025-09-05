"""Database tools for Hanzo AI.

This package provides tools for working with embedded SQLite databases
and graph databases in projects.
"""

from mcp.server import FastMCP

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager

from .graph_add import GraphAddTool

# Import database tools
from .sql_query import SqlQueryTool
from .sql_stats import SqlStatsTool
from .sql_search import SqlSearchTool
from .graph_query import GraphQueryTool
from .graph_stats import GraphStatsTool
from .graph_remove import GraphRemoveTool
from .graph_search import GraphSearchTool
from .database_manager import DatabaseManager

__all__ = [
    "register_database_tools",
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


def register_database_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    db_manager: DatabaseManager | None = None,
) -> list[BaseTool]:
    """Register database tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        db_manager: Optional database manager instance

    Returns:
        List of registered tools
    """
    # Create database manager if not provided
    if db_manager is None:
        db_manager = DatabaseManager(permission_manager)

    # Create tool instances
    tools = [
        SqlQueryTool(permission_manager, db_manager),
        SqlSearchTool(permission_manager, db_manager),
        SqlStatsTool(permission_manager, db_manager),
        GraphAddTool(permission_manager, db_manager),
        GraphRemoveTool(permission_manager, db_manager),
        GraphQueryTool(permission_manager, db_manager),
        GraphSearchTool(permission_manager, db_manager),
        GraphStatsTool(permission_manager, db_manager),
    ]

    # Register with MCP server
    from hanzo_mcp.tools.common.base import ToolRegistry

    ToolRegistry.register_tools(mcp_server, tools)

    return tools
