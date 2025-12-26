"""LLM tools for Hanzo AI.

Tools:
- llm: Unified LLM interface
- llm_manage: Model management
- consensus: Multi-model consensus

Install:
    pip install hanzo-tools-llm[full]
"""

import logging
logger = logging.getLogger(__name__)

# Lazy imports for heavy dependencies
_tools = []

try:
    from .llm_tool import LLMTool
    _tools.append(LLMTool)
except ImportError as e:
    logger.debug(f"LLMTool not available: {e}")
    LLMTool = None

try:
    from .llm_unified import UnifiedLLMTool
    _tools.append(UnifiedLLMTool)
except ImportError as e:
    logger.debug(f"UnifiedLLMTool not available: {e}")
    UnifiedLLMTool = None

try:
    from .consensus_tool import ConsensusTool
    _tools.append(ConsensusTool)
except ImportError as e:
    logger.debug(f"ConsensusTool not available: {e}")
    ConsensusTool = None

try:
    from .llm_manage import LLMManageTool
    _tools.append(LLMManageTool)
except ImportError as e:
    logger.debug(f"LLMManageTool not available: {e}")
    LLMManageTool = None

TOOLS = _tools
LLM_AVAILABLE = len(_tools) > 0

__all__ = [
    "TOOLS",
    "LLM_AVAILABLE",
    "LLMTool",
    "UnifiedLLMTool",
    "ConsensusTool",
    "LLMManageTool",
    "register_tools",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register LLM tools with MCP server."""
    from hanzo_tools.core import ToolRegistry
    
    enabled = enabled_tools or {}
    registered = []
    
    for tool_class in TOOLS:
        if tool_class is None:
            continue
        tool_name = getattr(tool_class, 'name', tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")
    
    return registered
