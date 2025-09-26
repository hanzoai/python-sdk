"""Memory tools for MCP agents."""

from mcp.server import FastMCP

from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.common.permissions import PermissionManager

# Import memory tools if available
try:
    from hanzo_mcp.tools.memory.memory_tools import (
        CreateMemoriesTool,
        DeleteMemoriesTool,
        ManageMemoriesTool,
        RecallMemoriesTool,
        UpdateMemoriesTool,
    )
    from hanzo_mcp.tools.memory.knowledge_tools import (
        StoreFactsTool,
        RecallFactsTool,
        SummarizeToMemoryTool,
        ManageKnowledgeBasesTool,
    )

    MEMORY_TOOLS_AVAILABLE = True
except ImportError:
    MEMORY_TOOLS_AVAILABLE = False


def register_memory_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    user_id: str = "default",
    project_id: str = "default",
    **memory_config,
) -> list[BaseTool]:
    """Register memory tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        user_id: User ID for memory operations
        project_id: Project ID for memory operations
        **memory_config: Additional memory store configuration

    Returns:
        List of registered tools
    """
    if not MEMORY_TOOLS_AVAILABLE:
        print("Warning: Memory tools not available (hanzo-memory package not found)")
        return []

    # Create memory tools
    recall_tool = RecallMemoriesTool(user_id=user_id, project_id=project_id, **memory_config)
    create_tool = CreateMemoriesTool(user_id=user_id, project_id=project_id, **memory_config)
    update_tool = UpdateMemoriesTool(user_id=user_id, project_id=project_id, **memory_config)
    delete_tool = DeleteMemoriesTool(user_id=user_id, project_id=project_id, **memory_config)
    manage_tool = ManageMemoriesTool(user_id=user_id, project_id=project_id, **memory_config)

    # Create knowledge tools
    recall_facts_tool = RecallFactsTool(user_id=user_id, project_id=project_id, **memory_config)
    store_facts_tool = StoreFactsTool(user_id=user_id, project_id=project_id, **memory_config)
    summarize_tool = SummarizeToMemoryTool(user_id=user_id, project_id=project_id, **memory_config)
    manage_kb_tool = ManageKnowledgeBasesTool(user_id=user_id, project_id=project_id, **memory_config)

    # Register tools
    ToolRegistry.register_tool(mcp_server, recall_tool)
    ToolRegistry.register_tool(mcp_server, create_tool)
    ToolRegistry.register_tool(mcp_server, update_tool)
    ToolRegistry.register_tool(mcp_server, delete_tool)
    ToolRegistry.register_tool(mcp_server, manage_tool)
    ToolRegistry.register_tool(mcp_server, recall_facts_tool)
    ToolRegistry.register_tool(mcp_server, store_facts_tool)
    ToolRegistry.register_tool(mcp_server, summarize_tool)
    ToolRegistry.register_tool(mcp_server, manage_kb_tool)

    # Return list of registered tools
    return [
        recall_tool,
        create_tool,
        update_tool,
        delete_tool,
        manage_tool,
        recall_facts_tool,
        store_facts_tool,
        summarize_tool,
        manage_kb_tool,
    ]
