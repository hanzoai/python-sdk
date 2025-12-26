"""Vector search and embedding tools.

Tools:
- vector_index: Index files for semantic search
- vector_search: Search indexed content

Install: pip install hanzo-tools-vector
"""

TOOLS = []

__all__ = ["TOOLS", "register_tools"]

def register_tools(mcp_server, permission_manager=None, enabled_tools=None):
    """Register vector tools with the MCP server."""
    return []
