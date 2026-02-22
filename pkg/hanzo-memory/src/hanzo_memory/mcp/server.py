"""MCP server for Hanzo Memory service."""

import json
import asyncio
from typing import Any, Literal
from uuid import uuid4

from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.types import (
    TextContent,
    Tool,
)
from structlog import get_logger

from ..config import settings
from ..db.sqlite_client import SQLiteMemoryClient, get_sqlite_client
from ..models.knowledge import Fact, FactCreate, KnowledgeBase
from ..models.memory import Memory, MemoryCreate
from ..services.embeddings import EmbeddingService, get_embedding_service
from ..services.llm import LLMService, get_llm_service

# Constants
ServiceName = "hanzo-memory"

logger = get_logger()


def get_db_client() -> SQLiteMemoryClient:
    """Get the database client."""
    return get_sqlite_client()


class MCPMemoryServer:
    """MCP server for memory operations."""

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.server: Server = Server(settings.mcp_server_name)
        self.db_client = get_db_client()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up server handlers."""

        @self.server.list_tools()  # type: ignore[misc]
        async def handle_list_tools() -> list[Tool]:
            """Return available tools."""
            return [
                Tool(
                    name="memory",
                    description="""Unified memory tool for storing, retrieving, and managing information.
Supports the following actions:
- remember: Store a new memory
- recall: Search for memories
- delete: Delete a memory
- create_project: Create a new project container
- create_kb: Create a structured knowledge base
- add_fact: Add a fact to a knowledge base
- search_facts: Search within a knowledge base
- delete_fact: Remove a fact from a knowledge base
- summarize: Analyze content and generate knowledge entries""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "remember",
                                    "recall",
                                    "delete",
                                    "create_project",
                                    "create_kb",
                                    "add_fact",
                                    "search_facts",
                                    "delete_fact",
                                    "summarize",
                                ],
                                "description": "The action to perform",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID (required for all actions)",
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Project ID (optional for some actions)",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content for storage or analysis",
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query for recall/search purposes",
                            },
                            "id": {
                                "type": "string",
                                "description": "ID of item to delete (memory_id or fact_id)",
                            },
                            "kb_id": {
                                "type": "string",
                                "description": "Knowledge base ID for fact operations",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name for new project or knowledge base",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description for new project or KB",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Limit results",
                                "default": 10,
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance score (0-10)",
                                "default": 1.0,
                            },
                            "parent_id": {
                                "type": "string",
                                "description": "Parent fact ID",
                            },
                            "context": {
                                "type": "string",
                                "description": "Context for summarization",
                            },
                        },
                        "required": ["action", "user_id"],
                    },
                ),
            ]

        @self.server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name != "memory":
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({"error": f"Unknown tool: {name}"}),
                        )
                    ]

                args = arguments or {}
                action = args.get("action")

                if action == "remember":
                    result = await self._handle_remember(args)
                elif action == "recall":
                    result = await self._handle_recall(args)
                elif action == "delete":
                    result = await self._handle_delete_memory(args)
                elif action == "create_project":
                    result = await self._handle_create_project(args)
                elif action == "create_kb":
                    result = await self._handle_create_knowledge_base(args)
                elif action == "add_fact":
                    result = await self._handle_add_fact(args)
                elif action == "search_facts":
                    result = await self._handle_search_facts(args)
                elif action == "delete_fact":
                    result = await self._handle_delete_fact(args)
                elif action == "summarize":
                    result = await self._handle_summarize_for_knowledge(args)
                else:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({"error": f"Unknown action: {action}"}),
                        )
                    ]

                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.error(
                    f"Error handling memory action {arguments.get('action')}: {e}"
                )
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def _handle_remember(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle remember action."""
        user_id = args["user_id"]
        project_id = args.get("project_id", "default")
        content = args.get("content")
        if not content:
            raise ValueError("content is required for remember action")

        metadata = args.get("metadata", {})
        importance = args.get("importance", 1.0)

        # Run embedding generation in thread pool
        embedding = (
            await asyncio.to_thread(self.embedding_service.embed_text, content)
        )[0]
        memory_id = str(uuid4())

        # Run DB operations in thread pool
        def _store():
            self.db_client.create_memories_table(user_id)
            self.db_client.add_memory(
                memory_id=memory_id,
                user_id=user_id,
                project_id=project_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                importance=importance,
            )

        await asyncio.to_thread(_store)

        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully",
        }

    async def _handle_recall(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle recall action."""
        user_id = args["user_id"]
        project_id = args.get("project_id")
        query = args.get("query")
        if not query:
            raise ValueError("query is required for recall action")

        limit = args.get("limit", 10)

        # Generate query embedding
        query_embedding = (
            await asyncio.to_thread(self.embedding_service.embed_text, query)
        )[0]

        # Search memories
        results_df = await asyncio.to_thread(
            self.db_client.search_memories,
            user_id=user_id,
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
        )

        # Convert results
        memories = []
        if isinstance(results_df, list):
            memories = results_df  # It's a list of dicts from sqlite client fallback or non-polars return
        elif not results_df.is_empty():
            for row in results_df.to_dicts():
                memories.append(
                    {
                        "memory_id": row.get("memory_id"),
                        "content": row.get("content"),
                        "metadata": (
                            json.loads(row.get("metadata", "{}"))
                            if isinstance(row.get("metadata"), str)
                            else row.get("metadata", {})
                        ),
                        "importance": row.get("importance", 1.0),
                        "similarity_score": row.get(
                            "_similarity", row.get("similarity_score", 0.0)
                        ),
                    }
                )

        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
        }

    async def _handle_delete_memory(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle delete memory action."""
        user_id = args["user_id"]
        project_id = args.get("project_id", "default")
        memory_id = args.get("id")

        if not memory_id:
            raise ValueError("id is required for delete action")

        success = await asyncio.to_thread(
            self.db_client.delete_memory,
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
        )

        return {
            "success": success,
            "message": "Memory deleted" if success else "Memory not found",
        }

    async def _handle_create_project(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle create project action."""
        user_id = args["user_id"]
        name = args.get("name")
        if not name:
            raise ValueError("name is required for create_project action")

        description = args.get("description", "")
        metadata = args.get("metadata", {})

        project_id = str(uuid4())

        await asyncio.to_thread(
            self.db_client.create_project,
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            metadata=metadata,
        )

        return {
            "success": True,
            "project_id": project_id,
            "message": "Project created successfully",
        }

    async def _handle_create_knowledge_base(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle create knowledge base action."""
        user_id = args["user_id"]
        project_id = args.get("project_id", "default")
        name = args.get("name")
        if not name:
            raise ValueError("name is required for create_kb action")

        description = args.get("description", "")

        kb_id = str(uuid4())

        await asyncio.to_thread(
            self.db_client.create_knowledge_base,
            kb_id=kb_id,
            user_id=user_id,
            project_id=project_id,
            name=name,
            description=description,
        )

        return {
            "success": True,
            "kb_id": kb_id,
            "message": "Knowledge base created successfully",
        }

    async def _handle_add_fact(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle add fact action."""
        kb_id = args.get("kb_id")
        if not kb_id:
            raise ValueError("kb_id is required for add_fact action")

        content = args.get("content")
        if not content:
            raise ValueError("content is required for add_fact action")

        parent_id = args.get("parent_id")
        metadata = args.get("metadata", {})

        embedding = (
            await asyncio.to_thread(self.embedding_service.embed_text, content)
        )[0]
        fact_id = str(uuid4())

        await asyncio.to_thread(
            self.db_client.add_fact,
            fact_id=fact_id,
            kb_id=kb_id,
            content=content,
            embedding=embedding,
            parent_id=parent_id,
            metadata=metadata,
        )

        return {
            "success": True,
            "fact_id": fact_id,
            "message": "Fact added successfully",
        }

    async def _handle_search_facts(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle search facts action."""
        kb_id = args.get("kb_id")
        if not kb_id:
            raise ValueError("kb_id is required for search_facts action")

        query = args.get("query")
        if not query:
            raise ValueError("query is required for search_facts action")

        limit = args.get("limit", 10)

        query_embedding = (
            await asyncio.to_thread(self.embedding_service.embed_text, query)
        )[0]

        results_df = await asyncio.to_thread(
            self.db_client.search_facts,
            kb_id=kb_id,
            query_embedding=query_embedding,
            limit=limit,
        )

        facts = []
        if isinstance(results_df, list):
            facts = results_df
        elif not results_df.is_empty():
            for row in results_df.to_dicts():
                facts.append(
                    {
                        "fact_id": row.get("fact_id"),
                        "content": row.get("content"),
                        "parent_id": row.get("parent_id"),
                        "metadata": (
                            json.loads(row.get("metadata", "{}"))
                            if isinstance(row.get("metadata"), str)
                            else row.get("metadata", {})
                        ),
                        "similarity_score": row.get(
                            "_similarity", row.get("similarity_score", 0.0)
                        ),
                    }
                )

        return {
            "success": True,
            "facts": facts,
            "count": len(facts),
        }

    async def _handle_delete_fact(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle delete fact action."""
        kb_id = args.get("kb_id")
        fact_id = args.get("id")
        if not kb_id or not fact_id:
            raise ValueError("kb_id and id are required for delete_fact action")

        success = await asyncio.to_thread(
            self.db_client.delete_fact, fact_id=fact_id, knowledge_base_id=kb_id
        )

        return {
            "success": success,
            "message": "Fact deleted" if success else "Fact not found",
        }

    async def _handle_summarize_for_knowledge(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle summarize for knowledge action."""
        content = args.get("content")
        if not content:
            raise ValueError("content is required for summarize action")

        context = args.get("context")
        skip_summarization = args.get("skip_summarization", False)
        provided_summary = args.get("provided_summary")

        # LLM service might be IO bound depending on implementation, assume safe to verify async later or wrap now
        # Wrapping just in case
        result = await asyncio.to_thread(
            self.llm_service.summarize_for_knowledge,
            content=content,
            context=context,
            skip_summarization=skip_summarization,
            provided_summary=provided_summary,
        )

        return result

    async def run(self) -> None:
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=settings.mcp_server_name,
                    server_version=settings.mcp_server_version,
                    capabilities=ServerCapabilities(),
                ),
            )


def main() -> None:
    """Run the MCP memory server."""
    server = MCPMemoryServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
