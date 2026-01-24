"""Network tools for Hanzo AI (HIP-0300).

Tools:
- net: Unified network tool (HIP-0300)
  - search: Web search (Query → [URL, title, snippet])
  - fetch: Retrieve URL content (URL → {text, mime})
  - download: Save URL with assets (URL → Path)
  - crawl: Recursive site mirror (URL, depth → [Path])
  - head: Get headers only

Effect lattice position: NONDETERMINISTIC_EFFECT
All operations involve network I/O.

Install:
    pip install hanzo-tools-net
    pip install hanzo-tools-net[full]  # With beautifulsoup4

Usage:
    from hanzo_tools.net import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access the unified tool
    from hanzo_tools.net import NetTool
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .net_tool import NetTool, net_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [NetTool]

__all__ = [
    "NetTool",
    "net_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register net tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional options (cwd, etc.)

    Returns:
        List of registered tool instances
    """
    cwd = kwargs.get("cwd")
    tool = NetTool(cwd=cwd)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
