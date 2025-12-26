"""MCP management tools for Hanzo AI.

Tools:
- mcp: MCP server management
- mcp_add: Add MCP servers
- mcp_remove: Remove MCP servers
- mcp_stats: MCP statistics

Install:
    pip install hanzo-tools-mcp
"""

import logging

logger = logging.getLogger(__name__)

_tools = []

try:
    from .mcp_tool import MCPTool

    _tools.append(MCPTool)
except ImportError as e:
    logger.debug(f"MCPTool not available: {e}")
    MCPTool = None

try:
    from .mcp_add import McpAddTool

    _tools.append(McpAddTool)
except ImportError as e:
    logger.debug(f"McpAddTool not available: {e}")
    McpAddTool = None

try:
    from .mcp_remove import McpRemoveTool

    _tools.append(McpRemoveTool)
except ImportError as e:
    logger.debug(f"McpRemoveTool not available: {e}")
    McpRemoveTool = None

try:
    from .mcp_stats import McpStatsTool

    _tools.append(McpStatsTool)
except ImportError as e:
    logger.debug(f"McpStatsTool not available: {e}")
    McpStatsTool = None

TOOLS = _tools

__all__ = [
    "TOOLS",
    "MCPTool",
    "McpAddTool",
    "McpRemoveTool",
    "McpStatsTool",
    "register_tools",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register MCP tools with MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        if tool_class is None:
            continue
        tool_name = getattr(tool_class, "name", tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")

    return registered
