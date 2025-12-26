"""Refactoring tools for Hanzo AI.

Tools:
- refactor: Advanced code refactoring with LSP/AST support

Actions:
- rename: Rename symbols across codebase
- rename_batch: Batch rename multiple symbols
- extract_function: Extract code to new function
- extract_variable: Extract expression to variable
- inline: Inline variables or functions
- move: Move symbols between files
- change_signature: Modify function signatures
- find_references: Find all symbol references
- organize_imports: Sort and organize imports

Install:
    pip install hanzo-tools-refactor

Usage:
    from hanzo_tools.refactor import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access tool directly
    from hanzo_tools.refactor import RefactorTool
"""

from hanzo_tools.refactor.refactor_tool import RefactorTool, create_refactor_tool

# Export list for tool discovery
TOOLS = [RefactorTool]

__all__ = [
    "RefactorTool",
    "create_refactor_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register all refactor tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
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
            tool = tool_class()
            ToolRegistry.register_tool(mcp_server, tool)
            registered.append(tool)

    return registered
