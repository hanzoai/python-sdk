"""Memory tool for Hanzo MCP.

Single `memory` tool with action parameter for all memory operations.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Annotated,
    final,
    override,
)

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
    """Get memory service lazily. Returns None if hanzo-memory is not available."""
    global _memory_service
    if _memory_service is None:
        if not _check_memory_available():
            return None  # type: ignore[return-value]
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

BackendMode = Annotated[
    Literal["auto", "local", "cloud", "hybrid"],
    Field(
        description=(
            "Backend mode: auto/local-first (default), local-only, "
            "cloud-only, or hybrid(local+cloud)"
        )
    ),
]


@final
class MemoryTool(BaseTool):
    """Memory tool for all memory operations.

    Consolidates legacy memory/facts/knowledge tool variants behind one surface.
    """

    name = "memory"

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        """Initialize memory tool."""
        self.user_id = user_id
        self.project_id = project_id

    @property
    @override
    def description(self) -> str:
        return """Memory management tool.

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
- backend: Defaults to local-first markdown (`auto`), with optional cloud/vector backend

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
        backend: str = "auto",
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
                return await self._recall(
                    queries or ([query] if query else []), scope, limit, backend
                )
            elif action == "create":
                return await self._create(content, tags, metadata, scope, backend)
            elif action == "update":
                return await self._update(id, content, tags, metadata)
            elif action == "delete":
                return await self._delete(ids or ([id] if id else []))
            elif action == "manage":
                return await self._manage(create_list, update_list, delete_ids)
            elif action == "facts":
                return await self._facts_lookup(
                    queries or ([query] if query else []), kb, limit
                )
            elif action == "store":
                return await self._facts_store(
                    facts or ([fact] if fact else []), kb, metadata
                )
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

    async def _recall(
        self,
        queries: List[str],
        scope: str,
        limit: int,
        backend_mode: str,
    ) -> str:
        """Search and retrieve memories."""
        if not queries:
            return "Error: query or queries required for recall"

        from hanzo_tools.memory.markdown_memory import get_markdown_backend

        mode = (backend_mode or "auto").lower()
        use_local = mode in ("auto", "local", "hybrid")
        use_cloud = mode in ("auto", "cloud", "hybrid") and _check_memory_available()

        combined: List[tuple[str, str, str, str]] = []
        seen_ids: set[str] = set()
        seen_content: set[str] = set()

        if use_local:
            local_backend = get_markdown_backend()
            local_results = local_backend.search_memories(
                queries=queries, limit=limit, scope=scope
            )
            for mem in local_results:
                mem_id = str(getattr(mem, "memory_id", ""))
                content = str(getattr(mem, "content", ""))
                source = str(getattr(mem, "source", "local"))
                if mem_id and mem_id in seen_ids:
                    continue
                if content and content in seen_content:
                    continue
                if mem_id:
                    seen_ids.add(mem_id)
                if content:
                    seen_content.add(content)
                combined.append(("local", mem_id, content, source))

        if use_cloud:
            cloud_backend = _get_lazy_memory_service()
            if cloud_backend is not None:
                for q in queries:
                    cloud_results = cloud_backend.search_memories(
                        user_id=self.user_id,
                        query=q,
                        project_id=self.project_id,
                        limit=limit,
                    )
                    for mem in cloud_results:
                        mem_id = str(getattr(mem, "memory_id", ""))
                        content = str(getattr(mem, "content", ""))
                        if mem_id and mem_id in seen_ids:
                            continue
                        if content and content in seen_content:
                            continue
                        if mem_id:
                            seen_ids.add(mem_id)
                        if content:
                            seen_content.add(content)
                        score = getattr(mem, "similarity_score", None)
                        score_text = f" score={score:.3f}" if isinstance(score, (int, float)) else ""
                        combined.append(("cloud", mem_id, content, f"vector{score_text}"))

        if not combined:
            if mode in ("cloud", "hybrid") and not _check_memory_available():
                return "No memories found. Cloud backend unavailable; using local markdown only."
            return "No memories found matching the query."

        lines = [f"Found {min(len(combined), limit)} memories (mode={mode}):"]
        for source_kind, mem_id, content, source in combined[:limit]:
            tag = f"{source_kind}:{source}" if source else source_kind
            id_text = mem_id[:8] if mem_id else "no-id"
            preview = content[:100] if content else "(empty)"
            lines.append(f"  [{id_text}] {preview} [{tag}]")
        return "\n".join(lines)

    async def _create(
        self,
        content: Optional[str],
        tags: Optional[List[str]],
        metadata: Optional[Dict],
        scope: str,
        backend_mode: str,
    ) -> str:
        """Store new memory."""
        if not content:
            return "Error: content required for create"

        mode = (backend_mode or "auto").lower()
        use_local = mode in ("auto", "local", "hybrid")
        use_cloud = mode in ("auto", "cloud", "hybrid") and _check_memory_available()

        results: List[str] = []

        from hanzo_tools.memory.markdown_memory import get_markdown_backend

        if use_local:
            local_backend = get_markdown_backend()
            mem = local_backend.add_memory(content=content, scope=scope)
            results.append(f"local:{mem.memory_id}")

        if use_cloud:
            cloud_backend = _get_lazy_memory_service()
            if cloud_backend is not None:
                cloud_memory = cloud_backend.create_memory(
                    user_id=self.user_id,
                    project_id=self.project_id,
                    content=content,
                    metadata=metadata or {"scope": scope, "source": "memory_tool"},
                )
                results.append(f"cloud:{cloud_memory.memory_id}")

        if not results:
            if mode in ("cloud", "hybrid"):
                return "Memory not created: cloud backend unavailable."
            return "Memory not created."

        return f"Created memory ({mode}): " + ", ".join(results)

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

        from hanzo_tools.memory.markdown_memory import get_markdown_backend
        result = get_markdown_backend().update_memory(id, content or "")
        return f"Updated memory: {id}" if result else f"Memory {id} not found"

    async def _delete(self, ids: List[str]) -> str:
        """Delete memories."""
        if not ids:
            return "Error: id or ids required for delete"

        from hanzo_tools.memory.markdown_memory import get_markdown_backend
        backend = get_markdown_backend()
        count = sum(1 for mid in ids if backend.delete_memory(mid))
        return f"Deleted {count} of {len(ids)} memories"

    async def _manage(
        self,
        create_list: Optional[List[Dict]],
        update_list: Optional[List[Dict]],
        delete_ids: Optional[List[str]],
    ) -> str:
        """Atomic memory operations."""
        from hanzo_tools.memory.markdown_memory import get_markdown_backend
        backend = get_markdown_backend()
        results = []

        if create_list:
            for item in create_list:
                mem = backend.add_memory(content=item["content"], scope="project")
                results.append(f"Created: {mem.memory_id}")

        if update_list:
            for item in update_list:
                result = backend.update_memory(item["id"], item.get("statement", item.get("content", "")))
                results.append(f"Updated: {item['id']}" if result else f"Not found: {item['id']}")

        if delete_ids:
            for mid in delete_ids:
                backend.delete_memory(mid)
                results.append(f"Deleted: {mid}")

        if not results:
            return "No operations specified. Provide create_list, update_list, or delete_ids."
        return "\n".join(results)

    async def _facts_lookup(
        self, queries: List[str], kb: Optional[str], limit: int
    ) -> str:
        """Search knowledge bases (falls back to local markdown)."""
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
            # Fall back to local markdown backend
            from hanzo_tools.memory.markdown_memory import get_markdown_backend

            backend = get_markdown_backend()
            results = backend.search_memories(
                queries=queries, limit=limit, scope="project"
            )
            if not results:
                return "No facts found."

            lines = [f"Found {len(results)} facts:"]
            for mem in results[:limit]:
                lines.append(f"  • {mem.content[:100]}...")
            return "\n".join(lines)

    async def _facts_store(
        self,
        facts: List[str],
        kb: Optional[str],
        metadata: Optional[Dict],
    ) -> str:
        """Store facts in knowledge base (falls back to local markdown)."""
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
            # Fall back to local markdown backend
            from hanzo_tools.memory.markdown_memory import get_markdown_backend

            backend = get_markdown_backend()
            stored = []
            for fact in facts:
                mem = backend.add_memory(content=fact, scope="session")
                stored.append(mem.memory_id)
            return f"Stored {len(stored)} fact(s) locally"

    async def _summarize(
        self,
        content: Optional[str],
        tags: Optional[List[str]],
        scope: str,
    ) -> str:
        """Summarize and store."""
        if not content:
            return "Error: content required for summarize"

        from hanzo_tools.memory.markdown_memory import get_markdown_backend
        mem = get_markdown_backend().add_memory(content=f"[Summary] {content}", scope=scope)
        return f"Stored summary: {mem.memory_id}"

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

        from hanzo_tools.memory.markdown_memory import get_markdown_backend
        backend = get_markdown_backend()
        backend._ensure_loaded()
        memories = list(backend._file_memories) + list(backend._session_memories)
        if scope != "global":
            memories = [m for m in memories if getattr(m, "scope", "global") == scope]

        if not memories:
            return "No memories found."

        lines = [f"Memories ({min(len(memories), limit)} of {len(memories)}):"]
        for mem in memories[:limit]:
            lines.append(f"  [{mem.memory_id[:8]}] {mem.content[:60]}...")
        return "\n".join(lines)

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def memory(
            action: Action = "list",
            backend: BackendMode = "auto",
            query: Annotated[Optional[str], Field(description="Search query")] = None,
            queries: Annotated[
                Optional[List[str]], Field(description="Multiple queries")
            ] = None,
            content: Annotated[
                Optional[str], Field(description="Memory content")
            ] = None,
            id: Annotated[Optional[str], Field(description="Memory ID")] = None,
            ids: Annotated[
                Optional[List[str]], Field(description="Multiple IDs")
            ] = None,
            tags: Annotated[Optional[List[str]], Field(description="Tags")] = None,
            metadata: Annotated[Optional[Dict], Field(description="Metadata")] = None,
            scope: Annotated[
                str, Field(description="Scope: session, project, global")
            ] = "session",
            limit: Annotated[int, Field(description="Max results")] = 10,
            kb: Annotated[
                Optional[str], Field(description="Knowledge base name")
            ] = None,
            fact: Annotated[Optional[str], Field(description="Fact to store")] = None,
            facts: Annotated[
                Optional[List[str]], Field(description="Multiple facts")
            ] = None,
            create_list: Annotated[
                Optional[List[Dict]], Field(description="Items to create")
            ] = None,
            update_list: Annotated[
                Optional[List[Dict]], Field(description="Items to update")
            ] = None,
            delete_ids: Annotated[
                Optional[List[str]], Field(description="IDs to delete")
            ] = None,
            kb_action: Annotated[
                Optional[str], Field(description="KB action: list, create, delete")
            ] = None,
            name: Annotated[Optional[str], Field(description="KB name")] = None,
            list_type: Annotated[
                str, Field(description="List type: memories, kb")
            ] = "memories",
            ctx: MCPContext = None,
        ) -> str:
            """Memory management: recall, create, update, delete, facts, kb."""
            return await tool_instance.call(
                ctx,
                action=action,
                backend=backend,
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
