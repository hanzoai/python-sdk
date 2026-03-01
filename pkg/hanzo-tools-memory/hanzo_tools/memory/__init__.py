"""Memory and knowledge tools for Hanzo MCP.

Works out of the box with NO backend — reads from local .md files
(MEMORY.md, LLM.md, CLAUDE.md, etc.) and stores memories to MEMORY.md.

Install hanzo-memory for full vector search and persistent storage:
    pip install hanzo-tools-memory[full]

Tool list (registered individually as MCP tools):
  recall_memories, create_memories, update_memories, delete_memories, manage_memories
  recall_facts, store_facts, summarize_to_memory, manage_knowledge_bases
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
from hanzo_tools.memory.unified_memory_tool import UnifiedMemoryTool

ALL_TOOL_CLASSES = MEMORY_TOOL_CLASSES + KNOWLEDGE_TOOL_CLASSES

__all__ = [
    # Individual tools
    "RecallMemoriesTool",
    "CreateMemoriesTool",
    "UpdateMemoriesTool",
    "DeleteMemoriesTool",
    "ManageMemoriesTool",
    "RecallFactsTool",
    "StoreFactsTool",
    "SummarizeToMemoryTool",
    "ManageKnowledgeBasesTool",
    # Unified tool
    "UnifiedMemoryTool",
    # Registration helpers
    "get_memory_tools",
    "register_memory_tools",
    "ALL_TOOL_CLASSES",
    "TOOLS",
]


def get_memory_tools(
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Create all memory tool instances."""
    return [cls(user_id=user_id, project_id=project_id, **kwargs) for cls in ALL_TOOL_CLASSES]


def register_memory_tools(
    mcp_server: FastMCP,
    user_id: str = "default",
    project_id: str = "default",
    **kwargs,
) -> list[BaseTool]:
    """Register all memory tools with the MCP server."""
    tools = get_memory_tools(user_id=user_id, project_id=project_id, **kwargs)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


# TOOLS list for entry point discovery — single unified memory tool
TOOLS = [UnifiedMemoryTool]
