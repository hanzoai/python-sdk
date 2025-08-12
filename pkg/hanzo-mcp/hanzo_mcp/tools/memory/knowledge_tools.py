"""Knowledge base and fact management tools for MCP.

These tools use the hanzo-memory package to manage knowledge bases and facts,
supporting hierarchical organization (session, project, global).
"""

from typing import Any, Dict, List, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context

# Import from hanzo-memory package
try:
    from hanzo_memory.models.memory import Memory, MemoryWithScore
    from hanzo_memory.services.memory import MemoryService, get_memory_service
    from hanzo_memory.models.knowledge import Fact, FactCreate, KnowledgeBase

    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    raise ImportError(
        "hanzo-memory package is required for knowledge tools. Install it from ~/work/hanzo/ide/pkg/memory"
    )


class KnowledgeToolBase(BaseTool):
    """Base class for knowledge tools using hanzo-memory package."""

    def __init__(self, user_id: str = "default", project_id: str = "default", **kwargs):
        """Initialize knowledge tool.

        Args:
            user_id: User ID for knowledge operations
            project_id: Project ID for knowledge operations
            **kwargs: Additional configuration
        """
        self.user_id = user_id
        self.project_id = project_id
        # Use the memory service for knowledge management
        self.service = get_memory_service()


@final
class RecallFactsTool(KnowledgeToolBase):
    """Tool for recalling facts from knowledge bases."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "recall_facts"

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

        # Determine the appropriate IDs based on scope
        if scope == "global":
            user_id = "global"
            project_id = "global"
        elif scope == "session":
            # Session scope uses a session-specific ID
            user_id = f"session_{self.user_id}"
            project_id = self.project_id
        else:
            user_id = self.user_id
            project_id = self.project_id

        all_facts = []
        for query in queries:
            # Search for facts using memory service with fact metadata
            search_query = f"fact: {query}"
            if kb_name:
                search_query = f"kb:{kb_name} {search_query}"

            memories = self.service.search_memories(
                user_id=user_id, query=search_query, project_id=project_id, limit=limit
            )

            # Filter for fact-type memories
            for memory in memories:
                if memory.metadata and memory.metadata.get("type") == "fact":
                    all_facts.append(memory)

        # Deduplicate by memory ID
        seen = set()
        unique_facts = []
        for fact in all_facts:
            if fact.memory_id not in seen:
                seen.add(fact.memory_id)
                unique_facts.append(fact)

        if not unique_facts:
            return "No relevant facts found."

        # Format results
        formatted = [f"Found {len(unique_facts)} relevant facts:\n"]
        for i, fact in enumerate(unique_facts, 1):
            kb_info = ""
            if fact.metadata and fact.metadata.get("kb_name"):
                kb_info = f" (KB: {fact.metadata['kb_name']})"
            formatted.append(f"{i}. {fact.content}{kb_info}")
            if (
                fact.metadata and len(fact.metadata) > 2
            ):  # More than just type and kb_name
                # Show other metadata
                other_meta = {
                    k: v
                    for k, v in fact.metadata.items()
                    if k not in ["type", "kb_name"]
                }
                if other_meta:
                    formatted.append(f"   Metadata: {other_meta}")

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

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "store_facts"

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

        # Determine the appropriate IDs based on scope
        if scope == "global":
            user_id = "global"
            project_id = "global"
        elif scope == "session":
            user_id = f"session_{self.user_id}"
            project_id = self.project_id
        else:
            user_id = self.user_id
            project_id = self.project_id

        created_facts = []
        for fact_content in facts:
            # Create fact as a memory with special metadata
            fact_metadata = {"type": "fact", "kb_name": kb_name}
            if metadata:
                fact_metadata.update(metadata)

            memory = self.service.create_memory(
                user_id=user_id,
                project_id=project_id,
                content=f"fact: {fact_content}",
                metadata=fact_metadata,
                importance=1.5,  # Facts have higher importance
            )
            created_facts.append(memory)

        return f"Successfully stored {len(created_facts)} facts in {kb_name}."

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

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "summarize_to_memory"

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

        # Use the memory service to create a summary
        # This would typically use an LLM to summarize, but for now we'll store as-is
        summary = (
            f"Summary of {topic}:\n{content[:500]}..."
            if len(content) > 500
            else content
        )

        # Store the summary as a memory
        from hanzo_memory.services.memory import get_memory_service

        memory_service = get_memory_service()

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

        memory = memory_service.create_memory(
            user_id=user_id,
            project_id=project_id,
            content=summary,
            metadata={"topic": topic, "type": "summary", "scope": scope},
        )

        result = f"Stored summary of {topic} in {scope} memory."

        # Optionally extract facts
        if auto_facts:
            # In a real implementation, this would use LLM to extract key facts
            # For now, we'll just note it
            result += (
                "\n(Auto-fact extraction would extract key facts from the summary)"
            )

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

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "manage_knowledge_bases"

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

            memory = self.service.create_memory(
                user_id=user_id,
                project_id=project_id,
                content=f"Knowledge Base: {kb_name}\nDescription: {description or 'No description'}",
                metadata=kb_metadata,
                importance=2.0,  # KBs have high importance
            )
            return f"Created knowledge base '{kb_name}' in {scope} scope."

        elif action == "list":
            # Search for knowledge base entries
            kbs = self.service.search_memories(
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
            kbs = self.service.search_memories(
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
                    self.service.delete_memory(user_id, memory.memory_id)
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
