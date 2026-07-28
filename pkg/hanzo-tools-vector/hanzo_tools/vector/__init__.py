"""Vector/embedding tools for Hanzo AI.

The only surface is the cloud-backed `VectorTool`: real zen embeddings into the
in-cluster Qdrant via api.hanzo.ai. Actions: search, index, embed.

There is no local store. The former embedded-Infinity path shipped no embedder,
so it could only ever produce random vectors — which rank by noise and silently
lie to the caller. A tool that lies is worse than a missing tool, so it is gone
rather than flag-guarded: every vector here is computed by the real service.
"""

import logging

logger = logging.getLogger(__name__)

# Primary surface: cloud-backed, real vectors. Depends only on hanzo_tools.core.
from .cloud_vector import VectorTool, vector_tool

TOOLS = [VectorTool]
VECTOR_AVAILABLE = True

__all__ = [
    "TOOLS",
    "VECTOR_AVAILABLE",
    "VectorTool",
    "vector_tool",
    "register_tools",
]


def register_tools(mcp_server, permission_manager=None, enabled_tools=None):
    """Register the cloud vector tool with the MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []
    for tool_class in TOOLS:
        tool_name = getattr(tool_class, "name", tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")
    return registered
