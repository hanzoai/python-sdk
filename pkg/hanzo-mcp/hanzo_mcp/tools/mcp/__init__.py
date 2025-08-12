"""MCP management tools."""

# Legacy imports
from hanzo_mcp.tools.mcp.mcp_add import McpAddTool
from hanzo_mcp.tools.mcp.mcp_tool import MCPTool
from hanzo_mcp.tools.mcp.mcp_stats import McpStatsTool
from hanzo_mcp.tools.mcp.mcp_remove import McpRemoveTool

__all__ = [
    "MCPTool",
    "McpAddTool",
    "McpRemoveTool",
    "McpStatsTool",
]
