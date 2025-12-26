"""Language Server Protocol tools for Hanzo MCP.

This package provides LSP-based code intelligence:
- LSPTool: Go-to-definition, find references, rename, hover, completion
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.lsp.lsp_tool import LSPTool, create_lsp_tool

__all__ = [
    "LSPTool",
    "create_lsp_tool",
    "get_lsp_tools",
    "register_lsp_tools",
    "TOOLS",
]


def get_lsp_tools() -> list[BaseTool]:
    """Create instances of all LSP tools.

    Returns:
        List of LSP tool instances
    """
    return [LSPTool()]


def register_lsp_tools(mcp_server: FastMCP) -> list[BaseTool]:
    """Register all LSP tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance

    Returns:
        List of registered tools
    """
    tools = get_lsp_tools()
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery
TOOLS = [LSPTool]
