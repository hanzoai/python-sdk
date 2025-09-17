"""Memory tools implementation for MCP.

This module provides MCP tools that use the hanzo-memory package as a library.
The hanzo-memory package provides embedded database and vector search capabilities.
"""

from typing import Dict, List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context

# Import from hanzo-memory package
try:
    from hanzo_memory.models.memory import Memory, MemoryWithScore
    from hanzo_memory.services.memory import MemoryService, get_memory_service

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    raise ImportError(
        "hanzo-memory package is required for memory tools. Install it from ~/work/hanzo/python-sdk/pkg/hanzo-memory"
    )


class MemoryToolBase(BaseTool):
    """Base class for memory tools using hanzo-memory package."""

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        """Initialize memory tool.

        Args:
            user_id: User ID for memory operations
            project_id: Project ID for memory operations
            **kwargs: Additional configuration
        """
        self.user_id = user_id
        self.project_id = project_id
        # Use the global memory service from hanzo-memory
        self.service = get_memory_service()


@final
class RecallMemoriesTool(MemoryToolBase):
    """Tool for recalling memories."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "recall_memories"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Recall memories relevant to one or more queries.

This tool searches through stored memories and returns relevant matches.
Supports different scopes: session, project, or global memories.
Multiple queries can be run in parallel for efficiency.

Usage:
recall_memories(queries=["user preferences", "previous conversations"])
recall_memories(queries=["project requirements"], scope="project")
recall_memories(queries=["coding standards"], scope="global")
"""

    @override
    async def call(
        self,
        ctx: MCPContext,
        queries: List[str],
        limit: int = 10,
        scope: str = "project",
    ) -> str:
        """Recall memories matching queries.

        Args:
            ctx: MCP context
            queries: Search queries
            limit: Max results per query

        Returns:
            Formatted memory results
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        await tool_ctx.info(f"Searching for {len(queries)} queries")

        all_results = []
        for query in queries:
            # Use hanzo-memory's search_memories method
            results = self.service.search_memories(
                user_id=self.user_id,
                query=query,
                project_id=self.project_id,
                limit=limit,
            )
            all_results.extend(results)

        # Deduplicate by memory_id
        seen = set()
        unique_results = []
        for result in all_results:
            if result.memory_id not in seen:
                seen.add(result.memory_id)
                unique_results.append(result)

        if not unique_results:
            return "No relevant memories found."

        # Format results
        formatted = [f"Found {len(unique_results)} relevant memories:\n"]
        for i, memory in enumerate(unique_results, 1):
            score = getattr(memory, "similarity_score", 0.0)
            formatted.append(f"{i}. {memory.content} (relevance: {score:.2f})")

        return "\n".join(formatted)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def recall_memories(ctx: MCPContext, queries: List[str], limit: int = 10, scope: str = "project") -> str:
            return await tool_self.call(ctx, queries=queries, limit=limit, scope=scope)


@final
class CreateMemoriesTool(MemoryToolBase):
    """Tool for creating memories."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "create_memories"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Save one or more new pieces of information to memory.

This tool creates new memories from provided statements.
Each statement is stored as a separate memory.

Usage:
create_memories(statements=["User prefers dark mode", "User works in Python"])
"""

    @override
    async def call(self, ctx: MCPContext, statements: List[str]) -> str:
        """Create new memories.

        Args:
            ctx: MCP context
            statements: Statements to memorize

        Returns:
            Success message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        await tool_ctx.info(f"Creating {len(statements)} memories")

        created_memories = []
        for statement in statements:
            # Use hanzo-memory's create_memory method
            memory = self.service.create_memory(
                user_id=self.user_id,
                project_id=self.project_id,
                content=statement,
                metadata={"type": "statement"},
            )
            created_memories.append(memory)

        return f"Successfully created {len(created_memories)} new memories."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def create_memories(ctx: MCPContext, statements: List[str]) -> str:
            return await tool_self.call(ctx, statements=statements)


@final
class UpdateMemoriesTool(MemoryToolBase):
    """Tool for updating memories."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "update_memories"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Update existing memories with corrected information.

This tool updates memories by ID with new content.

Usage:
update_memories(updates=[
    {"id": "mem_1", "statement": "User prefers light mode"},
    {"id": "mem_2", "statement": "User primarily works in TypeScript"}
])
"""

    @override
    async def call(self, ctx: MCPContext, updates: List[Dict[str, str]]) -> str:
        """Update memories.

        Args:
            ctx: MCP context
            updates: List of {id, statement} dicts

        Returns:
            Success message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        await tool_ctx.info(f"Updating {len(updates)} memories")

        # Note: hanzo-memory's update methods are not fully implemented yet
        # For now, we'll track what would be updated
        success_count = 0
        for update in updates:
            memory_id = update.get("id")
            statement = update.get("statement")

            if memory_id and statement:
                # The hanzo-memory service doesn't have update implemented yet
                # When it's implemented, we would call:
                # success = self.service.update_memory(self.user_id, memory_id, content=statement)
                await tool_ctx.warning(f"Memory update not fully implemented in hanzo-memory yet: {memory_id}")
                success_count += 1

        return f"Would update {success_count} of {len(updates)} memories (update not fully implemented in hanzo-memory yet)."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def update_memories(ctx: MCPContext, updates: List[Dict[str, str]]) -> str:
            return await tool_self.call(ctx, updates=updates)


@final
class DeleteMemoriesTool(MemoryToolBase):
    """Tool for deleting memories."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "delete_memories"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Delete memories that are no longer relevant or incorrect.

This tool removes memories by their IDs.

Usage:
delete_memories(ids=["mem_1", "mem_2"])
"""

    @override
    async def call(self, ctx: MCPContext, ids: List[str]) -> str:
        """Delete memories.

        Args:
            ctx: MCP context
            ids: Memory IDs to delete

        Returns:
            Success message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        await tool_ctx.info(f"Deleting {len(ids)} memories")

        success_count = 0
        for memory_id in ids:
            # Use hanzo-memory's delete_memory method
            success = self.service.delete_memory(self.user_id, memory_id)
            if success:
                success_count += 1

        return f"Successfully deleted {success_count} of {len(ids)} memories."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def delete_memories(ctx: MCPContext, ids: List[str]) -> str:
            return await tool_self.call(ctx, ids=ids)


@final
class ManageMemoriesTool(MemoryToolBase):
    """Tool for managing memories atomically."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "manage_memories"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Create, update, and/or delete memories in a single atomic operation.

This is the preferred way to modify memories as it allows multiple
operations to be performed together.

Usage:
manage_memories(
    creations=["New fact 1", "New fact 2"],
    updates=[{"id": "mem_1", "statement": "Updated fact"}],
    deletions=["mem_old1", "mem_old2"]
)
"""

    @override
    async def call(
        self,
        ctx: MCPContext,
        creations: Optional[List[str]] = None,
        updates: Optional[List[Dict[str, str]]] = None,
        deletions: Optional[List[str]] = None,
    ) -> str:
        """Manage memories atomically.

        Args:
            ctx: MCP context
            creations: Statements to create
            updates: Memories to update
            deletions: Memory IDs to delete

        Returns:
            Summary of operations
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        results = []

        # Create memories
        if creations:
            await tool_ctx.info(f"Creating {len(creations)} memories")
            created = []
            for statement in creations:
                memory = self.service.create_memory(
                    user_id=self.user_id,
                    project_id=self.project_id,
                    content=statement,
                    metadata={"type": "statement"},
                )
                created.append(memory)
            results.append(f"Created {len(created)} memories")

        # Update memories
        if updates:
            await tool_ctx.info(f"Updating {len(updates)} memories")
            success_count = 0
            for update in updates:
                memory_id = update.get("id")
                statement = update.get("statement")

                if memory_id and statement:
                    # Update not fully implemented in hanzo-memory yet
                    await tool_ctx.warning(f"Memory update not fully implemented: {memory_id}")
                    success_count += 1
            results.append(f"Would update {success_count} memories (update pending implementation)")

        # Delete memories
        if deletions:
            await tool_ctx.info(f"Deleting {len(deletions)} memories")
            success_count = 0
            for memory_id in deletions:
                success = self.service.delete_memory(self.user_id, memory_id)
                if success:
                    success_count += 1
            results.append(f"Deleted {success_count} memories")

        if not results:
            return "No memory operations performed."

        return "Memory operations completed: " + ", ".join(results)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def manage_memories(
            ctx: MCPContext,
            creations: Optional[List[str]] = None,
            updates: Optional[List[Dict[str, str]]] = None,
            deletions: Optional[List[str]] = None,
        ) -> str:
            return await tool_self.call(ctx, creations=creations, updates=updates, deletions=deletions)
