"""Vector/embedding tools for Hanzo AI.

Tools:
- vector_index: Index documents for semantic search
- vector_search: Search indexed documents
- index: Project indexing

Install:
    pip install hanzo-tools-vector[full]
"""

import logging
logger = logging.getLogger(__name__)

_tools = []
VECTOR_AVAILABLE = False

try:
    from .index_tool import IndexTool
    _tools.append(IndexTool)
    from .vector_index import VectorIndexTool
    _tools.append(VectorIndexTool)
    from .vector_search import VectorSearchTool
    _tools.append(VectorSearchTool)
    VECTOR_AVAILABLE = True
except ImportError as e:
    logger.debug(f"Vector tools not available: {e}")

TOOLS = _tools

__all__ = [
    "TOOLS",
    "VECTOR_AVAILABLE",
    "register_tools",
]

if VECTOR_AVAILABLE:
    __all__.extend(["IndexTool", "VectorIndexTool", "VectorSearchTool"])


def register_tools(mcp_server, permission_manager=None, enabled_tools: dict[str, bool] | None = None):
    """Register vector tools with MCP server."""
    if not VECTOR_AVAILABLE:
        logger.warning("Vector tools not available - missing dependencies")
        return []
    
    from hanzo_tools.core import ToolRegistry
    
    enabled = enabled_tools or {}
    registered = []
    
    for tool_class in TOOLS:
        tool_name = getattr(tool_class, 'name', tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class(permission_manager) if permission_manager else tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")
    
    return registered
