"""Unified memory tool - consolidates all memory operations.

Single tool with action parameter replaces 9 separate memory tools.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Annotated, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

if TYPE_CHECKING:
    from hanzo_memory.services.memory import MemoryService

# Lazy loading
MEMORY_AVAILABLE: Optional[bool] = None
_memory_service: Optional["MemoryService"] = None


def _check_memory_available() -> bool:
    """Check if hanzo-memory is available."""
    global MEMORY_AVAILABLE
    if MEMORY_AVAILABLE is None:
        try:
            import hanzo_memory  # noqa: F401

            MEMORY_AVAILABLE = True
        except ImportError:
            MEMORY_AVAILABLE = False
    return MEMORY_AVAILABLE


def _get_lazy_memory_service() -> "MemoryService":
    """Get memory service lazily."""
    global _memory_service
    if _memory_service is None:
        if not _check_memory_available():
            raise ImportError("hanzo-memory required. Install: pip install hanzo-memory")
        from hanzo_memory.services.memory import get_memory_service

        _memory_service = get_memory_service()
    return _memory_service


Action = Annotated[
    Literal[
        "recall",  # Search memories
        "create",  # Store new memories
        "update",  # Update existing memories
        "delete",  # Delete memories
        "manage",  # Atomic create/update/delete
        "facts",  # Recall facts from knowledge bases
        "store",  # Store facts in knowledge bases
        "summarize",  # Summarize and store
        "kb",  # Manage knowledge bases
        "list",  # List memories/knowledge bases
    ],
    Field(description="Memory action to perform"),
]


@final
class UnifiedMemoryTool(BaseTool):
    """Unified memory tool for all memory operations.

    Consolidates: recall_memories, create_memories, update_memories,
    delete_memories, manage_memories, recall_facts, store_facts,
    summarize_to_memory, manage_knowledge_bases
    """

    name = "memory"

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        """Initialize memory tool."""
        self.user_id = user_id
        self.project_id = project_id
        self._service: Optional["MemoryService"] = None

    @property
    def service(self) -> "MemoryService":
        """Get memory service lazily."""
        if self._service is None:
            self._service = _get_lazy_memory_service()
        return self._service

    @property
    @override
    def description(self) -> str:
        return """Unified memory management tool.

Actions:
- recall: Search and retrieve memories
- create: Store new memories
- update: Update existing memories
- delete: Remove memories
- manage: Atomic operations (create + update + delete)
- facts: Recall facts from knowledge bases
- store: Store facts in knowledge bases
- summarize: Summarize information and store
- kb: Create/list/manage knowledge bases
- list: List all memories or knowledge bases

Examples:
  memory recall --query "user preferences"
  memory create --content "User prefers dark mode" --tags ["preferences"]
  memory update --id mem_123 --content "Updated content"
  memory delete --id mem_123
  memory facts --query "coding standards" --kb "project_docs"
  memory store --fact "Python uses 4-space indentation" --kb "coding"
  memory kb --action create --name "project_notes"
  memory list --type memories
"""

    @override
    @auto_timeout("memory")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "list",
        # Common params
        query: Optional[str] = None,
        queries: Optional[List[str]] = None,
        content: Optional[str] = None,
        id: Optional[str] = None,
        ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scope: str = "session",
        limit: int = 10,
        # Knowledge base params
        kb: Optional[str] = None,
        fact: Optional[str] = None,
        facts: Optional[List[str]] = None,
        # Manage params
        create_list: Optional[List[Dict]] = None,
        update_list: Optional[List[Dict]] = None,
        delete_ids: Optional[List[str]] = None,
        # KB management
        kb_action: Optional[str] = None,
        name: Optional[str] = None,
        # List params
        list_type: str = "memories",
        **kwargs,
    ) -> str:
        """Execute memory operation."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        try:
            if action == "recall":
                return await self._recall(queries or ([query] if query else []), scope, limit)
            elif action == "create":
                return await self._create(content, tags, metadata, scope)
            elif action == "update":
                return await self._update(id, content, tags, metadata)
            elif action == "delete":
                return await self._delete(ids or ([id] if id else []))
            elif action == "manage":
                return await self._manage(create_list, update_list, delete_ids)
            elif action == "facts":
                return await self._recall_facts(queries or ([query] if query else []), kb, limit)
            elif action == "store":
                return await self._store_facts(facts or ([fact] if fact else []), kb, metadata)
            elif action == "summarize":
                return await self._summarize(content, tags, scope)
            elif action == "kb":
                return await self._manage_kb(kb_action or "list", name)
            elif action == "list":
                return await self._list(list_type, scope, limit)
            else:
                return f"Unknown action: {action}. Use: recall, create, update, delete, manage, facts, store, summarize, kb, list"

        except ImportError as e:
            return f"Memory service not available: {e}"
        except Exception as e:
            return f"Memory operation failed: {e}"

    async def _recall(self, queries: List[str], scope: str, limit: int) -> str:
        """Search and retrieve memories."""
        if not queries:
            return "Error: query or queries required for recall"

        results = []
        for q in queries:
            memories = await self.service.recall(
                query=q,
                user_id=self.user_id,
                project_id=self.project_id,
                scope=scope,
                limit=limit,
            )
            results.extend(memories)

        if not results:
            return "No memories found matching the query."

        lines = [f"Found {len(results)} memories:"]
        for mem in results[:limit]:
            lines.append(f"  [{mem.id}] {mem.content[:100]}...")
            if mem.tags:
                lines.append(f"    Tags: {', '.join(mem.tags)}")
        return "\n".join(lines)

    async def _create(
        self,
        content: Optional[str],
        tags: Optional[List[str]],
        metadata: Optional[Dict],
        scope: str,
    ) -> str:
        """Store new memory."""
        if not content:
            return "Error: content required for create"

        memory = await self.service.create(
            content=content,
            user_id=self.user_id,
            project_id=self.project_id,
            tags=tags or [],
            metadata=metadata or {},
            scope=scope,
        )
        return f"Created memory: {memory.id}"

    async def _update(
        self,
        id: Optional[str],
        content: Optional[str],
        tags: Optional[List[str]],
        metadata: Optional[Dict],
    ) -> str:
        """Update existing memory."""
        if not id:
            return "Error: id required for update"

        await self.service.update(
            memory_id=id,
            content=content,
            tags=tags,
            metadata=metadata,
        )
        return f"Updated memory: {id}"

    async def _delete(self, ids: List[str]) -> str:
        """Delete memories."""
        if not ids:
            return "Error: id or ids required for delete"

        for mid in ids:
            await self.service.delete(memory_id=mid)
        return f"Deleted {len(ids)} memories"

    async def _manage(
        self,
        create_list: Optional[List[Dict]],
        update_list: Optional[List[Dict]],
        delete_ids: Optional[List[str]],
    ) -> str:
        """Atomic memory operations."""
        results = []

        if create_list:
            for item in create_list:
                mem = await self.service.create(
                    content=item["content"],
                    user_id=self.user_id,
                    project_id=self.project_id,
                    tags=item.get("tags", []),
                    metadata=item.get("metadata", {}),
                )
                results.append(f"Created: {mem.id}")

        if update_list:
            for item in update_list:
                await self.service.update(
                    memory_id=item["id"],
                    content=item.get("content"),
                    tags=item.get("tags"),
                    metadata=item.get("metadata"),
                )
                results.append(f"Updated: {item['id']}")

        if delete_ids:
            for mid in delete_ids:
                await self.service.delete(memory_id=mid)
                results.append(f"Deleted: {mid}")

        if not results:
            return "No operations specified. Provide create_list, update_list, or delete_ids."
        return "\n".join(results)

    async def _recall_facts(self, queries: List[str], kb: Optional[str], limit: int) -> str:
        """Search knowledge bases."""
        if not queries:
            return "Error: query required for facts"

        try:
            from hanzo_memory.services.knowledge import get_knowledge_service

            ks = get_knowledge_service()

            results = []
            for q in queries:
                facts = await ks.recall(query=q, knowledge_base=kb, limit=limit)
                results.extend(facts)

            if not results:
                return "No facts found."

            lines = [f"Found {len(results)} facts:"]
            for fact in results[:limit]:
                lines.append(f"  • {fact.content[:100]}...")
            return "\n".join(lines)

        except ImportError:
            return "Knowledge service not available"

    async def _store_facts(
        self,
        facts: List[str],
        kb: Optional[str],
        metadata: Optional[Dict],
    ) -> str:
        """Store facts in knowledge base."""
        if not facts:
            return "Error: fact or facts required"

        try:
            from hanzo_memory.services.knowledge import get_knowledge_service

            ks = get_knowledge_service()

            stored = []
            for fact in facts:
                result = await ks.store(
                    content=fact,
                    knowledge_base=kb or "default",
                    metadata=metadata or {},
                )
                stored.append(result.id)

            return f"Stored {len(stored)} facts in '{kb or 'default'}'"

        except ImportError:
            return "Knowledge service not available"

    async def _summarize(
        self,
        content: Optional[str],
        tags: Optional[List[str]],
        scope: str,
    ) -> str:
        """Summarize and store."""
        if not content:
            return "Error: content required for summarize"

        # For now, just store as-is; could integrate with LLM for actual summarization
        memory = await self.service.create(
            content=f"[Summary] {content}",
            user_id=self.user_id,
            project_id=self.project_id,
            tags=(tags or []) + ["summary"],
            scope=scope,
        )
        return f"Stored summary: {memory.id}"

    async def _manage_kb(self, action: str, name: Optional[str]) -> str:
        """Manage knowledge bases."""
        try:
            from hanzo_memory.services.knowledge import get_knowledge_service

            ks = get_knowledge_service()

            if action == "list":
                kbs = await ks.list_knowledge_bases()
                if not kbs:
                    return "No knowledge bases found."
                lines = ["Knowledge bases:"]
                for kb in kbs:
                    lines.append(f"  • {kb.name}: {kb.description or 'No description'}")
                return "\n".join(lines)

            elif action == "create":
                if not name:
                    return "Error: name required for kb create"
                await ks.create_knowledge_base(name=name)
                return f"Created knowledge base: {name}"

            elif action == "delete":
                if not name:
                    return "Error: name required for kb delete"
                await ks.delete_knowledge_base(name=name)
                return f"Deleted knowledge base: {name}"

            else:
                return f"Unknown kb action: {action}. Use: list, create, delete"

        except ImportError:
            return "Knowledge service not available"

    async def _list(self, list_type: str, scope: str, limit: int) -> str:
        """List memories or knowledge bases."""
        if list_type == "kb":
            return await self._manage_kb("list", None)

        # List memories
        memories = await self.service.list(
            user_id=self.user_id,
            project_id=self.project_id,
            scope=scope,
            limit=limit,
        )

        if not memories:
            return "No memories found."

        lines = [f"Memories ({len(memories)}):"]
        for mem in memories:
            lines.append(f"  [{mem.id}] {mem.content[:60]}...")
        return "\n".join(lines)

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def memory(
            action: Action = "list",
            query: Annotated[Optional[str], Field(description="Search query")] = None,
            queries: Annotated[Optional[List[str]], Field(description="Multiple queries")] = None,
            content: Annotated[Optional[str], Field(description="Memory content")] = None,
            id: Annotated[Optional[str], Field(description="Memory ID")] = None,
            ids: Annotated[Optional[List[str]], Field(description="Multiple IDs")] = None,
            tags: Annotated[Optional[List[str]], Field(description="Tags")] = None,
            metadata: Annotated[Optional[Dict], Field(description="Metadata")] = None,
            scope: Annotated[str, Field(description="Scope: session, project, global")] = "session",
            limit: Annotated[int, Field(description="Max results")] = 10,
            kb: Annotated[Optional[str], Field(description="Knowledge base name")] = None,
            fact: Annotated[Optional[str], Field(description="Fact to store")] = None,
            facts: Annotated[Optional[List[str]], Field(description="Multiple facts")] = None,
            create_list: Annotated[Optional[List[Dict]], Field(description="Items to create")] = None,
            update_list: Annotated[Optional[List[Dict]], Field(description="Items to update")] = None,
            delete_ids: Annotated[Optional[List[str]], Field(description="IDs to delete")] = None,
            kb_action: Annotated[Optional[str], Field(description="KB action: list, create, delete")] = None,
            name: Annotated[Optional[str], Field(description="KB name")] = None,
            list_type: Annotated[str, Field(description="List type: memories, kb")] = "memories",
            ctx: MCPContext = None,
        ) -> str:
            """Unified memory management: recall, create, update, delete, facts, kb."""
            return await tool_instance.call(
                ctx,
                action=action,
                query=query,
                queries=queries,
                content=content,
                id=id,
                ids=ids,
                tags=tags,
                metadata=metadata,
                scope=scope,
                limit=limit,
                kb=kb,
                fact=fact,
                facts=facts,
                create_list=create_list,
                update_list=update_list,
                delete_ids=delete_ids,
                kb_action=kb_action,
                name=name,
                list_type=list_type,
            )
