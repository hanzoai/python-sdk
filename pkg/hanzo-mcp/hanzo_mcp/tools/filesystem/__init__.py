"""Filesystem tools package for Hanzo AI.

This package provides tools for interacting with the filesystem, including reading, writing,
and editing files, directory navigation, and content searching.
"""

from mcp.server import FastMCP

from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.filesystem.diff import create_diff_tool
from hanzo_mcp.tools.filesystem.edit import Edit
from hanzo_mcp.tools.filesystem.grep import Grep
from hanzo_mcp.tools.filesystem.read import ReadTool
from hanzo_mcp.tools.filesystem.watch import watch_tool
from hanzo_mcp.tools.filesystem.write import Write
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.filesystem.ast_tool import ASTTool
from hanzo_mcp.tools.filesystem.find_files import FindFilesTool
from hanzo_mcp.tools.filesystem.git_search import GitSearchTool
from hanzo_mcp.tools.filesystem.multi_edit import MultiEdit
from hanzo_mcp.tools.filesystem.rules_tool import RulesTool
from hanzo_mcp.tools.filesystem.search_tool import SearchTool
from hanzo_mcp.tools.filesystem.batch_search import BatchSearchTool
from hanzo_mcp.tools.filesystem.directory_tree import DirectoryTreeTool
from hanzo_mcp.tools.filesystem.content_replace import ContentReplaceTool

# Import new search tools
try:
    from hanzo_mcp.tools.search import (
        FindTool,
        SearchTool,
        create_find_tool,
        create_search_tool,
    )

    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

# Export all tool classes
__all__ = [
    "ReadTool",
    "Write",
    "Edit",
    "MultiEdit",
    "DirectoryTreeTool",
    "Grep",
    "ContentReplaceTool",
    "ASTTool",
    "GitSearchTool",
    "BatchSearchTool",
    "FindFilesTool",
    "RulesTool",
    "SearchTool",
    "get_filesystem_tools",
    "register_filesystem_tools",
]


def get_read_only_filesystem_tools(
    permission_manager: PermissionManager,
    project_manager=None,
) -> list[BaseTool]:
    """Create instances of read-only filesystem tools.

    Args:
        permission_manager: Permission manager for access control
        project_manager: Optional project manager for search

    Returns:
        List of read-only filesystem tool instances
    """
    tools = [
        ReadTool(permission_manager),
        DirectoryTreeTool(permission_manager),
        Grep(permission_manager),
        ASTTool(permission_manager),
        GitSearchTool(permission_manager),
        FindFilesTool(permission_manager),
        RulesTool(permission_manager),
        watch_tool,
        create_diff_tool(permission_manager),
    ]

    # Add search if project manager is available
    if project_manager:
        tools.append(SearchTool(permission_manager, project_manager))

    # Add new search tools if available
    if SEARCH_AVAILABLE:
        tools.extend([create_search_tool(), create_find_tool()])

    return tools


def get_filesystem_tools(permission_manager: PermissionManager, project_manager=None) -> list[BaseTool]:
    """Create instances of all filesystem tools.

    Args:
        permission_manager: Permission manager for access control
        project_manager: Optional project manager for search

    Returns:
        List of filesystem tool instances
    """
    tools = [
        ReadTool(permission_manager),
        Write(permission_manager),
        Edit(permission_manager),
        MultiEdit(permission_manager),
        DirectoryTreeTool(permission_manager),
        Grep(permission_manager),
        ContentReplaceTool(permission_manager),
        ASTTool(permission_manager),
        GitSearchTool(permission_manager),
        FindFilesTool(permission_manager),
        RulesTool(permission_manager),
        watch_tool,
        create_diff_tool(permission_manager),
    ]

    # Add search if project manager is available
    if project_manager:
        tools.append(SearchTool(permission_manager, project_manager))

    # Add new search tools if available
    if SEARCH_AVAILABLE:
        tools.extend([create_search_tool(), create_find_tool()])

    return tools


def register_filesystem_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    disable_write_tools: bool = False,
    disable_search_tools: bool = False,
    enabled_tools: dict[str, bool] | None = None,
    project_manager=None,
) -> list[BaseTool]:
    """Register filesystem tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        disable_write_tools: Whether to disable write tools (default: False)
        disable_search_tools: Whether to disable search tools (default: False)
        enabled_tools: Dictionary of individual tool enable states (default: None)
        project_manager: Optional project manager for search (default: None)

    Returns:
        List of registered tools
    """
    # Define tool mapping
    tool_classes = {
        "read": ReadTool,
        "write": Write,
        "edit": Edit,
        "multi_edit": MultiEdit,
        "tree": DirectoryTreeTool,
        "grep": Grep,
        "ast": ASTTool,  # AST-based code structure search with tree-sitter
        "git_search": GitSearchTool,
        "content_replace": ContentReplaceTool,
        "batch_search": BatchSearchTool,
        "find_files": FindFilesTool,
        "rules": RulesTool,
        "search": SearchTool,
        "watch": lambda pm: watch_tool,  # Singleton instance
        "diff": create_diff_tool,
    }

    # Add new search tools if available
    if SEARCH_AVAILABLE:
        tool_classes["search"] = lambda pm: create_search_tool()
        tool_classes["find"] = lambda pm: create_find_tool()

    tools = []

    if enabled_tools:
        # Use individual tool configuration
        for tool_name, enabled in enabled_tools.items():
            if enabled and tool_name in tool_classes:
                tool_class = tool_classes[tool_name]
                if tool_name == "batch_search":
                    # Batch search requires project_manager
                    tools.append(tool_class(permission_manager, project_manager))
                elif tool_name == "watch":
                    # Watch tool is a singleton
                    tools.append(tool_class(permission_manager))
                elif tool_name in ["search", "find"] and SEARCH_AVAILABLE:
                    # New search tools are factory functions that take no args
                    tools.append(tool_class(permission_manager))
                elif tool_name == "search":
                    # Old search tool requires project_manager
                    tools.append(tool_class(permission_manager, project_manager))
                else:
                    tools.append(tool_class(permission_manager))
    else:
        # Use category-level configuration (backward compatibility)
        if disable_write_tools and disable_search_tools:
            # Only read and directory tools
            tools = [
                ReadTool(permission_manager),
                DirectoryTreeTool(permission_manager),
            ]
        elif disable_write_tools:
            # Read-only tools including search
            tools = get_read_only_filesystem_tools(permission_manager, project_manager)
        elif disable_search_tools:
            # Write tools but no search
            tools = [
                ReadTool(permission_manager),
                Write(permission_manager),
                Edit(permission_manager),
                MultiEdit(permission_manager),
                DirectoryTreeTool(permission_manager),
                ContentReplaceTool(permission_manager),
            ]
        else:
            # All tools
            tools = get_filesystem_tools(permission_manager, project_manager)

    ToolRegistry.register_tools(mcp_server, tools)
    return tools
