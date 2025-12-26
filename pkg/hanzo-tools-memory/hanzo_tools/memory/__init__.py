"""Memory and knowledge tools for Hanzo MCP.

Provides a unified `memory` tool for all memory and knowledge operations:
- recall: Search and retrieve memories
- create: Store new memories
- update: Update existing memories
- delete: Remove memories
- manage: Atomic operations
- facts: Recall from knowledge bases
- store: Store facts
- summarize: Summarize and store
- kb: Manage knowledge bases
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.memory.unified_memory_tool import UnifiedMemoryTool

# Legacy imports for backwards compatibility
from hanzo_tools.memory.memory_tools import (
    MEMORY_TOOL_CLASSES,
    CreateMemoriesTool,
    DeleteMemoriesTool,
    ManageMemoriesTool,
    RecallMemoriesTool,
    UpdateMemoriesTool,
)
from hanzo_tools.memory.knowledge_tools import (
    KNOWLEDGE_TOOL_CLASSES,
    StoreFactsTool,
    RecallFactsTool,
    SummarizeToMemoryTool,
    ManageKnowledgeBasesTool,
)

__all__ = [
    # Primary unified tool
    "UnifiedMemoryTool",
    # Legacy tools (for backwards compatibility)
    "RecallMemoriesTool",
    "CreateMemoriesTool",
    "UpdateMemoriesTool",
    "DeleteMemoriesTool",
    "ManageMemoriesTool",
    "RecallFactsTool",
    "StoreFactsTool",
    "SummarizeToMemoryTool",
    "ManageKnowledgeBasesTool",
    # Registration helpers
    "get_memory_tools",
    "register_memory_tools",
    "TOOLS",
]


def get_memory_tools(
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Create unified memory tool instance."""
    return [UnifiedMemoryTool(user_id=user_id, project_id=project_id, **kwargs)]


def register_memory_tools(
    mcp_server: FastMCP,
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Register unified memory tool with the MCP server."""
    tools = get_memory_tools(user_id=user_id, project_id=project_id, **kwargs)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery - single unified tool
TOOLS = [UnifiedMemoryTool]
