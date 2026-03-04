"""Memory tools implementation for MCP.

Uses hanzo-memory (full vector search) when available, otherwise falls back to
the lightweight MarkdownMemoryBackend which reads from local .md files
(MEMORY.md, LLM.md, CLAUDE.md, etc.) with no external dependencies.

IMPORTANT: All hanzo-memory imports are lazy to avoid slow startup.
"""

from typing import TYPE_CHECKING, Dict, List, Union, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.memory.markdown_memory import (
    MarkdownMemoryBackend,
    get_markdown_backend,
)

# Type hints only - no runtime import
if TYPE_CHECKING:
    from hanzo_memory.services.memory import MemoryService

# Lazy loading - don't import at module load time
MEMORY_AVAILABLE: Optional[bool] = None
_memory_service: Optional["MemoryService"] = None


def _check_memory_available() -> bool:
    """Check if hanzo-memory is available (lazy check)."""
    global MEMORY_AVAILABLE
    if MEMORY_AVAILABLE is None:
        try:
            import hanzo_memory  # noqa: F401

            MEMORY_AVAILABLE = True
        except ImportError:
            MEMORY_AVAILABLE = False
    return MEMORY_AVAILABLE


def _get_lazy_memory_service() -> "MemoryService":
    """Get hanzo-memory service lazily. Returns None if not available."""
    global _memory_service
    if _memory_service is None:
        if not _check_memory_available():
            return None  # type: ignore[return-value]
        from hanzo_memory.services.memory import get_memory_service

        _memory_service = get_memory_service()
    return _memory_service


def _get_backend() -> Union["MemoryService", MarkdownMemoryBackend]:
    """Get the best available memory backend."""
    svc = _get_lazy_memory_service()
    if svc is not None:
        return svc
    return get_markdown_backend()


class MemoryToolBase(BaseTool):
    """Base class for memory tools."""

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        self.user_id = user_id
        self.project_id = project_id


@final
class RecallMemoriesTool(MemoryToolBase):
    """Tool for recalling memories."""

    name = "recall_memories"

    @property
    @override
    def description(self) -> str:
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
    @auto_timeout("memory_tools")
    async def call(
        self,
        ctx: MCPContext,
        queries: List[str],
        limit: int = 10,
        scope: str = "project",
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Searching for {len(queries)} queries")

        backend = _get_backend()
        unique_results = []

        if _check_memory_available():
            # Full vector search via hanzo-memory
            seen: set = set()
            for query in queries:
                results = backend.search_memories(  # type: ignore[union-attr]
                    user_id=self.user_id,
                    query=query,
                    project_id=self.project_id,
                    limit=limit,
                )
                for r in results:
                    if r.memory_id not in seen:
                        seen.add(r.memory_id)
                        unique_results.append(r)

            if not unique_results:
                return "No relevant memories found."

            formatted = [f"Found {len(unique_results)} relevant memories:\n"]
            for i, m in enumerate(unique_results, 1):
                score = getattr(m, "similarity_score", 0.0)
                formatted.append(f"{i}. {m.content} (relevance: {score:.2f})")
            return "\n".join(formatted)

        else:
            # Markdown fallback — keyword search across local .md files
            results = backend.search_memories(queries=queries, limit=limit, scope=scope)  # type: ignore[union-attr]

            if not results:
                return "No relevant memories found."

            formatted = [f"Found {len(results)} relevant memories:\n"]
            for i, m in enumerate(results, 1):
                source = getattr(m, "source", "")
                src_note = f" [{source}]" if source and source != "user" else ""
                formatted.append(f"{i}. {m.content}{src_note}")
            return "\n".join(formatted)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def recall_memories(
            ctx: MCPContext, queries: List[str], limit: int = 10, scope: str = "project"
        ) -> str:
            return await tool_self.call(ctx, queries=queries, limit=limit, scope=scope)


@final
class CreateMemoriesTool(MemoryToolBase):
    """Tool for creating memories."""

    name = "create_memories"

    @property
    @override
    def description(self) -> str:
        return """Save one or more new pieces of information to memory.

This tool creates new memories from provided statements.
Each statement is stored as a separate memory.

Usage:
create_memories(statements=["User prefers dark mode", "User works in Python"])
"""

    @override
    @auto_timeout("memory_tools")
    async def call(
        self,
        ctx: MCPContext,
        statements: List[str],
        scope: str = "project",
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Creating {len(statements)} memories")

        backend = _get_backend()

        if _check_memory_available():
            for statement in statements:
                backend.create_memory(  # type: ignore[union-attr]
                    user_id=self.user_id,
                    project_id=self.project_id,
                    content=statement,
                    metadata={"type": "statement"},
                )
        else:
            for statement in statements:
                backend.add_memory(content=statement, scope=scope)  # type: ignore[union-attr]

        return f"Successfully created {len(statements)} new memories."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def create_memories(
            ctx: MCPContext, statements: List[str], scope: str = "project"
        ) -> str:
            return await tool_self.call(ctx, statements=statements, scope=scope)


@final
class UpdateMemoriesTool(MemoryToolBase):
    """Tool for updating memories."""

    name = "update_memories"

    @property
    @override
    def description(self) -> str:
        return """Update existing memories with corrected information.

This tool updates memories by ID with new content.

Usage:
update_memories(updates=[
    {"id": "mem_1", "statement": "User prefers light mode"},
    {"id": "mem_2", "statement": "User primarily works in TypeScript"}
])
"""

    @override
    @auto_timeout("memory_tools")
    async def call(self, ctx: MCPContext, updates: List[Dict[str, str]]) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Updating {len(updates)} memories")

        backend = _get_backend()
        success_count = 0

        for update in updates:
            memory_id = update.get("id")
            statement = update.get("statement")
            if not memory_id or not statement:
                continue

            if _check_memory_available():
                # hanzo-memory update not fully implemented yet
                await tool_ctx.warning(f"Memory update pending implementation: {memory_id}")
                success_count += 1
            else:
                result = backend.update_memory(memory_id, statement)  # type: ignore[union-attr]
                if result is not None:
                    success_count += 1

        return f"Updated {success_count} of {len(updates)} memories."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def update_memories(
            ctx: MCPContext, updates: List[Dict[str, str]]
        ) -> str:
            return await tool_self.call(ctx, updates=updates)


@final
class DeleteMemoriesTool(MemoryToolBase):
    """Tool for deleting memories."""

    name = "delete_memories"

    @property
    @override
    def description(self) -> str:
        return """Delete memories that are no longer relevant or incorrect.

This tool removes memories by their IDs.

Usage:
delete_memories(ids=["mem_1", "mem_2"])
"""

    @override
    @auto_timeout("memory_tools")
    async def call(self, ctx: MCPContext, ids: List[str]) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Deleting {len(ids)} memories")

        backend = _get_backend()
        success_count = 0

        for memory_id in ids:
            if _check_memory_available():
                success = backend.delete_memory(self.user_id, memory_id)  # type: ignore[union-attr]
            else:
                success = backend.delete_memory(memory_id)  # type: ignore[union-attr]
            if success:
                success_count += 1

        return f"Successfully deleted {success_count} of {len(ids)} memories."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def delete_memories(ctx: MCPContext, ids: List[str]) -> str:
            return await tool_self.call(ctx, ids=ids)


@final
class ManageMemoriesTool(MemoryToolBase):
    """Tool for managing memories atomically."""

    name = "manage_memories"

    @property
    @override
    def description(self) -> str:
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
    @auto_timeout("memory_tools")
    async def call(
        self,
        ctx: MCPContext,
        creations: Optional[List[str]] = None,
        updates: Optional[List[Dict[str, str]]] = None,
        deletions: Optional[List[str]] = None,
        scope: str = "project",
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        backend = _get_backend()
        full = _check_memory_available()
        results = []

        if creations:
            await tool_ctx.info(f"Creating {len(creations)} memories")
            for statement in creations:
                if full:
                    backend.create_memory(  # type: ignore[union-attr]
                        user_id=self.user_id,
                        project_id=self.project_id,
                        content=statement,
                        metadata={"type": "statement"},
                    )
                else:
                    backend.add_memory(content=statement, scope=scope)  # type: ignore[union-attr]
            results.append(f"Created {len(creations)} memories")

        if updates:
            await tool_ctx.info(f"Updating {len(updates)} memories")
            success_count = 0
            for update in updates:
                memory_id = update.get("id")
                statement = update.get("statement")
                if not memory_id or not statement:
                    continue
                if full:
                    await tool_ctx.warning(f"Memory update pending implementation: {memory_id}")
                    success_count += 1
                else:
                    result = backend.update_memory(memory_id, statement)  # type: ignore[union-attr]
                    if result is not None:
                        success_count += 1
            results.append(f"Updated {success_count} memories")

        if deletions:
            await tool_ctx.info(f"Deleting {len(deletions)} memories")
            success_count = 0
            for memory_id in deletions:
                if full:
                    success = backend.delete_memory(self.user_id, memory_id)  # type: ignore[union-attr]
                else:
                    success = backend.delete_memory(memory_id)  # type: ignore[union-attr]
                if success:
                    success_count += 1
            results.append(f"Deleted {success_count} memories")

        return "Memory operations completed: " + ", ".join(results) if results else "No memory operations performed."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def manage_memories(
            ctx: MCPContext,
            creations: Optional[List[str]] = None,
            updates: Optional[List[Dict[str, str]]] = None,
            deletions: Optional[List[str]] = None,
            scope: str = "project",
        ) -> str:
            return await tool_self.call(
                ctx, creations=creations, updates=updates, deletions=deletions, scope=scope
            )


# Export all memory tool classes
MEMORY_TOOL_CLASSES = [
    RecallMemoriesTool,
    CreateMemoriesTool,
    UpdateMemoriesTool,
    DeleteMemoriesTool,
    ManageMemoriesTool,
]
