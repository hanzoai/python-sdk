"""Vector/embedding tools for Hanzo AI.

Default surface is the cloud-backed `VectorTool` (real Qdrant + zen embeddings
via api.hanzo.ai). Actions: search, index, embed.

The local Infinity store (infinity_store / vector_search / vector_index) remains
importable for offline use but is NOT the default and never substitutes a mock
silently — the random-vector mock is opt-in via HANZO_VECTOR_ALLOW_MOCK=1.

Install:
    pip install hanzo-tools-vector          # cloud (default)
    pip install hanzo-tools-vector[full]    # + local Infinity store
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
