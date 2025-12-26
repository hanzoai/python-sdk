"""Memory and knowledge tools for Hanzo MCP.

This package provides tools for managing memories and knowledge bases:
- RecallMemoriesTool: Search and retrieve memories
- CreateMemoriesTool: Store new memories
- UpdateMemoriesTool: Update existing memories
- DeleteMemoriesTool: Remove memories
- ManageMemoriesTool: Atomic memory operations
- RecallFactsTool: Search knowledge bases
- StoreFactsTool: Store facts in knowledge bases
- SummarizeToMemoryTool: Summarize and store information
- ManageKnowledgeBasesTool: Create and manage knowledge bases
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
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
    # Memory tools
    "RecallMemoriesTool",
    "CreateMemoriesTool",
    "UpdateMemoriesTool",
    "DeleteMemoriesTool",
    "ManageMemoriesTool",
    # Knowledge tools
    "RecallFactsTool",
    "StoreFactsTool",
    "SummarizeToMemoryTool",
    "ManageKnowledgeBasesTool",
    # Registration helpers
    "get_memory_tools",
    "register_memory_tools",
    "TOOLS",
]

# All tool classes for the TOOLS entry point
ALL_TOOL_CLASSES = MEMORY_TOOL_CLASSES + KNOWLEDGE_TOOL_CLASSES


def get_memory_tools(
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Create instances of all memory and knowledge tools.

    Args:
        user_id: User ID for memory operations
        project_id: Project ID for memory operations
        **kwargs: Additional configuration

    Returns:
        List of tool instances
    """
    return [
        cls(user_id=user_id, project_id=project_id, **kwargs)
        for cls in ALL_TOOL_CLASSES
    ]


def register_memory_tools(
    mcp_server: FastMCP,
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Register all memory and knowledge tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        user_id: User ID for memory operations
        project_id: Project ID for memory operations
        **kwargs: Additional configuration

    Returns:
        List of registered tools
    """
    tools = get_memory_tools(user_id=user_id, project_id=project_id, **kwargs)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery
TOOLS = [
    RecallMemoriesTool,
    CreateMemoriesTool,
    UpdateMemoriesTool,
    DeleteMemoriesTool,
    ManageMemoriesTool,
    RecallFactsTool,
    StoreFactsTool,
    SummarizeToMemoryTool,
    ManageKnowledgeBasesTool,
]
