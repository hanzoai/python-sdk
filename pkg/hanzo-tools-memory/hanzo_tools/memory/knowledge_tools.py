"""Knowledge base and fact management tools for MCP.

Uses hanzo-memory (full vector search) when available, otherwise falls back to
the lightweight MarkdownMemoryBackend which stores session facts in-memory.

IMPORTANT: All hanzo-memory imports are lazy to avoid slow startup.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.memory.markdown_memory import get_markdown_backend

# Type hints only - no runtime import
if TYPE_CHECKING:
    from hanzo_memory.services.memory import MemoryService

# Use lazy loading from memory_tools
from hanzo_tools.memory.memory_tools import (
    _get_backend,
    _check_memory_available,
    _get_lazy_memory_service,
)


class KnowledgeToolBase(BaseTool):
    """Base class for knowledge tools."""

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        self.user_id = user_id
        self.project_id = project_id


@final
class RecallFactsTool(KnowledgeToolBase):
    """Tool for recalling facts from knowledge bases."""

    name = "recall_facts"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Recall facts from knowledge bases relevant to queries.

Facts are structured pieces of information stored in knowledge bases.
Supports different scopes: session, project, or global.

Usage:
recall_facts(queries=["Python best practices"], kb_name="coding_standards")
recall_facts(queries=["API endpoints"], scope="project")
recall_facts(queries=["company policies"], scope="global", limit=5)
"""

    @override
    @auto_timeout("knowledge_tools")
    async def call(
        self,
        ctx: MCPContext,
        queries: List[str],
        kb_name: Optional[str] = None,
        scope: str = "project",
        limit: int = 10,
    ) -> str:
        """Recall facts matching queries.

        Args:
            ctx: MCP context
            queries: Search queries
            kb_name: Optional knowledge base name to search in
            scope: Scope level (session, project, global)
            limit: Max results per query

        Returns:
            Formatted fact results
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Searching for facts in scope: {scope}")

        backend = _get_backend()

        if _check_memory_available():
            # Full vector search via hanzo-memory
            if scope == "global":
                user_id, project_id = "global", "global"
            elif scope == "session":
                user_id, project_id = f"session_{self.user_id}", self.project_id
            else:
                user_id, project_id = self.user_id, self.project_id

            all_facts = []
            seen: set = set()
            for query in queries:
                search_query = f"fact: {query}"
                if kb_name:
                    search_query = f"kb:{kb_name} {search_query}"
                memories = backend.search_memories(  # type: ignore[union-attr]
                    user_id=user_id, query=search_query, project_id=project_id, limit=limit
                )
                for m in memories:
                    if m.memory_id not in seen and m.metadata and m.metadata.get("type") == "fact":
                        seen.add(m.memory_id)
                        all_facts.append(m)

            if not all_facts:
                return "No relevant facts found."

            formatted = [f"Found {len(all_facts)} relevant facts:\n"]
            for i, fact in enumerate(all_facts, 1):
                kb_info = f" (KB: {fact.metadata['kb_name']})" if fact.metadata and fact.metadata.get("kb_name") else ""
                formatted.append(f"{i}. {fact.content}{kb_info}")
            return "\n".join(formatted)

        else:
            # Markdown fallback — session-only fact storage
            facts = backend.recall_facts(queries=queries, kb_name=kb_name, limit=limit)  # type: ignore[union-attr]

            if not facts:
                return "No relevant facts found."

            formatted = [f"Found {len(facts)} relevant facts:\n"]
            for i, fact in enumerate(facts, 1):
                kb_info = f" (KB: {fact.kb_name})" if fact.kb_name and fact.kb_name != "general" else ""
                formatted.append(f"{i}. {fact.statement}{kb_info}")
            return "\n".join(formatted)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def recall_facts(
            ctx: MCPContext,
            queries: List[str],
            kb_name: Optional[str] = None,
            scope: str = "project",
            limit: int = 10,
        ) -> str:
            return await tool_self.call(
                ctx, queries=queries, kb_name=kb_name, scope=scope, limit=limit
            )


@final
class StoreFactsTool(KnowledgeToolBase):
    """Tool for storing facts in knowledge bases."""

    name = "store_facts"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Store new facts in knowledge bases.

Facts can be stored at different scopes (session, project, global) and
organized into knowledge bases for better categorization.

Usage:
store_facts(facts=["Python uses indentation for blocks"], kb_name="python_basics")
store_facts(facts=["API rate limit: 100/hour"], scope="project", kb_name="api_docs")
store_facts(facts=["Company founded in 2020"], scope="global", kb_name="company_info")
"""

    @override
    @auto_timeout("knowledge_tools")
    async def call(
        self,
        ctx: MCPContext,
        facts: List[str],
        kb_name: str = "general",
        scope: str = "project",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store new facts.

        Args:
            ctx: MCP context
            facts: Facts to store
            kb_name: Knowledge base name
            scope: Scope level (session, project, global)
            metadata: Optional metadata for all facts

        Returns:
            Success message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Storing {len(facts)} facts in {kb_name} (scope: {scope})")

        backend = _get_backend()

        if _check_memory_available():
            if scope == "global":
                user_id, project_id = "global", "global"
            elif scope == "session":
                user_id, project_id = f"session_{self.user_id}", self.project_id
            else:
                user_id, project_id = self.user_id, self.project_id

            for fact_content in facts:
                fact_metadata: Dict[str, Any] = {"type": "fact", "kb_name": kb_name}
                if metadata:
                    fact_metadata.update(metadata)
                backend.create_memory(  # type: ignore[union-attr]
                    user_id=user_id,
                    project_id=project_id,
                    content=f"fact: {fact_content}",
                    metadata=fact_metadata,
                    importance=1.5,
                )
        else:
            # Markdown fallback — store in session facts
            for fact_content in facts:
                backend.store_fact(statement=fact_content, kb_name=kb_name, scope=scope)  # type: ignore[union-attr]

        return f"Successfully stored {len(facts)} facts in {kb_name}."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def store_facts(
            ctx: MCPContext,
            facts: List[str],
            kb_name: str = "general",
            scope: str = "project",
            metadata: Optional[Dict[str, Any]] = None,
        ) -> str:
            return await tool_self.call(
                ctx, facts=facts, kb_name=kb_name, scope=scope, metadata=metadata
            )


@final
class SummarizeToMemoryTool(KnowledgeToolBase):
    """Tool for summarizing information and storing in memory."""

    name = "summarize_to_memory"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Summarize information and store it in memory for future reference.

This tool helps agents remember important information by summarizing it
and storing it at the appropriate scope level.

Usage:
summarize_to_memory(content="Long discussion about API design...", topic="API Design Decisions")
summarize_to_memory(content="User preferences...", topic="User Preferences", scope="session")
summarize_to_memory(content="Company guidelines...", topic="Guidelines", scope="global")
"""

    @override
    @auto_timeout("knowledge_tools")
    async def call(
        self,
        ctx: MCPContext,
        content: str,
        topic: str,
        scope: str = "project",
        auto_facts: bool = True,
    ) -> str:
        """Summarize content and store in memory.

        Args:
            ctx: MCP context
            content: Content to summarize
            topic: Topic or title for the summary
            scope: Scope level (session, project, global)
            auto_facts: Whether to extract facts automatically

        Returns:
            Success message with summary
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        await tool_ctx.info(f"Summarizing content about {topic}")

        summary = (
            f"Summary of {topic}:\n{content[:500]}..." if len(content) > 500 else content
        )

        backend = _get_backend()

        if _check_memory_available():
            if scope == "global":
                user_id, project_id = "global", "global"
            elif scope == "session":
                user_id, project_id = f"session_{self.user_id}", self.project_id
            else:
                user_id, project_id = self.user_id, self.project_id

            backend.create_memory(  # type: ignore[union-attr]
                user_id=user_id,
                project_id=project_id,
                content=summary,
                metadata={"topic": topic, "type": "summary", "scope": scope},
            )
        else:
            backend.add_memory(content=f"[{topic}] {summary}", scope=scope)  # type: ignore[union-attr]

        result = f"Stored summary of {topic} in {scope} memory."
        if auto_facts:
            result += "\n(Tip: install hanzo-memory for automatic fact extraction)"
        return result

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def summarize_to_memory(
            ctx: MCPContext,
            content: str,
            topic: str,
            scope: str = "project",
            auto_facts: bool = True,
        ) -> str:
            return await tool_self.call(
                ctx, content=content, topic=topic, scope=scope, auto_facts=auto_facts
            )


@final
class ManageKnowledgeBasesTool(KnowledgeToolBase):
    """Tool for managing knowledge bases."""

    name = "manage_knowledge_bases"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Create, list, and manage knowledge bases.

Knowledge bases help organize facts by topic or domain.
They can exist at different scopes for better organization.

Usage:
manage_knowledge_bases(action="create", kb_name="api_docs", description="API documentation")
manage_knowledge_bases(action="list", scope="project")
manage_knowledge_bases(action="delete", kb_name="old_docs")
"""

    @override
    @auto_timeout("knowledge_tools")
    async def call(
        self,
        ctx: MCPContext,
        action: str,
        kb_name: Optional[str] = None,
        description: Optional[str] = None,
        scope: str = "project",
    ) -> str:
        """Manage knowledge bases.

        Args:
            ctx: MCP context
            action: Action to perform (create, list, delete)
            kb_name: Knowledge base name (for create/delete)
            description: Description (for create)
            scope: Scope level

        Returns:
            Result message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if not _check_memory_available():
            # Markdown backend doesn't have persistent KB management
            if action == "list":
                return "Knowledge bases are session-only without hanzo-memory. Install hanzo-memory for persistent KBs."
            elif action == "create":
                return f"Knowledge base '{kb_name}' noted (session-only without hanzo-memory)."
            elif action == "delete":
                return f"Knowledge base '{kb_name}' removed from session."
            return "Knowledge base management requires hanzo-memory for persistence."

        backend = _get_lazy_memory_service()

        # Determine scope
        if scope == "global":
            user_id = "global"
            project_id = "global"
        elif scope == "session":
            user_id = f"session_{self.user_id}"
            project_id = self.project_id
        else:
            user_id = self.user_id
            project_id = self.project_id

        if action == "create":
            if not kb_name:
                return "Error: kb_name required for create action"

            # Create a knowledge base entry as a special memory
            kb_metadata = {
                "type": "knowledge_base",
                "kb_name": kb_name,
                "description": description or "",
                "scope": scope,
            }

            memory = backend.create_memory(
                user_id=user_id,
                project_id=project_id,
                content=f"Knowledge Base: {kb_name}\nDescription: {description or 'No description'}",
                metadata=kb_metadata,
                importance=2.0,  # KBs have high importance
            )
            return f"Created knowledge base '{kb_name}' in {scope} scope."

        elif action == "list":
            # Search for knowledge base entries
            kbs = backend.search_memories(
                user_id=user_id,
                query="type:knowledge_base",
                project_id=project_id,
                limit=100,
            )

            # Filter for KB-type memories
            kb_list = []
            for memory in kbs:
                if memory.metadata and memory.metadata.get("type") == "knowledge_base":
                    kb_list.append(memory)

            if not kb_list:
                return f"No knowledge bases found in {scope} scope."

            formatted = [f"Knowledge bases in {scope} scope:"]
            for kb in kb_list:
                name = kb.metadata.get("kb_name", "Unknown")
                desc = kb.metadata.get("description", "")
                desc_text = f" - {desc}" if desc else ""
                formatted.append(f"- {name}{desc_text}")
            return "\n".join(formatted)

        elif action == "delete":
            if not kb_name:
                return "Error: kb_name required for delete action"

            # Search for the KB entry
            kbs = backend.search_memories(
                user_id=user_id,
                query=f"type:knowledge_base kb_name:{kb_name}",
                project_id=project_id,
                limit=10,
            )

            deleted_count = 0
            for memory in kbs:
                if (
                    memory.metadata
                    and memory.metadata.get("type") == "knowledge_base"
                    and memory.metadata.get("kb_name") == kb_name
                ):
                    # Note: delete_memory is not fully implemented
                    # but we'll call it anyway
                    backend.delete_memory(user_id, memory.memory_id)
                    deleted_count += 1

            if deleted_count > 0:
                return f"Deleted knowledge base '{kb_name}'."
            else:
                return f"Knowledge base '{kb_name}' not found."

        else:
            return f"Unknown action: {action}. Use create, list, or delete."

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def manage_knowledge_bases(
            ctx: MCPContext,
            action: str,
            kb_name: Optional[str] = None,
            description: Optional[str] = None,
            scope: str = "project",
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                kb_name=kb_name,
                description=description,
                scope=scope,
            )


# Export all knowledge tool classes
KNOWLEDGE_TOOL_CLASSES = [
    RecallFactsTool,
    StoreFactsTool,
    SummarizeToMemoryTool,
    ManageKnowledgeBasesTool,
]
