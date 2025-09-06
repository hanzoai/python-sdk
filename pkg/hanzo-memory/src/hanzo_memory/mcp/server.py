"""MCP server for Hanzo Memory service."""

import json
from typing import Any
from uuid import uuid4

from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.types import (
    TextContent,
    Tool,
)
from structlog import get_logger

from ..config import settings
from ..db import get_db_client
from ..services.embeddings import EmbeddingService
from ..services.llm import LLMService

logger = get_logger()


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
                    name="remember",
                    description="Store a memory for a user in a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "project_id": {
                                "type": "string",
                                "description": "Project ID",
                            },
                            "content": {
                                "type": "string",
                                "description": "Memory content",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata",
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance score (0-10)",
                                "default": 1.0,
                            },
                        },
                        "required": ["user_id", "project_id", "content"],
                    },
                ),
                Tool(
                    name="recall",
                    description="Search for relevant memories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "project_id": {
                                "type": "string",
                                "description": "Project ID (optional)",
                            },
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {
                                "type": "integer",
                                "description": "Number of results",
                                "default": 10,
                            },
                        },
                        "required": ["user_id", "query"],
                    },
                ),
                Tool(
                    name="create_project",
                    description="Create a new project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "name": {"type": "string", "description": "Project name"},
                            "description": {
                                "type": "string",
                                "description": "Project description",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata",
                            },
                        },
                        "required": ["user_id", "name"],
                    },
                ),
                Tool(
                    name="create_knowledge_base",
                    description="Create a knowledge base in a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "project_id": {
                                "type": "string",
                                "description": "Project ID",
                            },
                            "name": {
                                "type": "string",
                                "description": "Knowledge base name",
                            },
                            "description": {
                                "type": "string",
                                "description": "Knowledge base description",
                            },
                        },
                        "required": ["user_id", "project_id", "name"],
                    },
                ),
                Tool(
                    name="add_fact",
                    description="Add a fact to a knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "kb_id": {
                                "type": "string",
                                "description": "Knowledge base ID",
                            },
                            "content": {
                                "type": "string",
                                "description": "Fact content",
                            },
                            "parent_id": {
                                "type": "string",
                                "description": "Parent fact ID (optional)",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata",
                            },
                        },
                        "required": ["user_id", "kb_id", "content"],
                    },
                ),
                Tool(
                    name="search_facts",
                    description="Search facts in a knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "kb_id": {
                                "type": "string",
                                "description": "Knowledge base ID",
                            },
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {
                                "type": "integer",
                                "description": "Number of results",
                                "default": 10,
                            },
                        },
                        "required": ["user_id", "kb_id", "query"],
                    },
                ),
                Tool(
                    name="summarize_for_knowledge",
                    description="Analyze content and generate knowledge update instructions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Content to analyze",
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context",
                            },
                            "skip_summarization": {
                                "type": "boolean",
                                "description": "Skip summarization",
                                "default": False,
                            },
                            "provided_summary": {
                                "type": "string",
                                "description": "Pre-made summary",
                            },
                        },
                        "required": ["content"],
                    },
                ),
            ]

        @self.server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "remember":
                    result = await self._handle_remember(arguments or {})
                elif name == "recall":
                    result = await self._handle_recall(arguments or {})
                elif name == "create_project":
                    result = await self._handle_create_project(arguments or {})
                elif name == "create_knowledge_base":
                    result = await self._handle_create_knowledge_base(arguments or {})
                elif name == "add_fact":
                    result = await self._handle_add_fact(arguments or {})
                elif name == "search_facts":
                    result = await self._handle_search_facts(arguments or {})
                elif name == "summarize_for_knowledge":
                    result = await self._handle_summarize_for_knowledge(arguments or {})
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def _handle_remember(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle remember tool."""
        user_id = args["user_id"]
        project_id = args["project_id"]
        content = args["content"]
        metadata = args.get("metadata", {})
        importance = args.get("importance", 1.0)

        # Ensure user's memory table exists
        self.db_client.create_memories_table(user_id)

        # Generate embedding
        embedding = self.embedding_service.embed_text(content)[0]

        # Store memory
        memory_id = str(uuid4())
        self.db_client.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            importance=importance,
        )

        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully",
        }

    async def _handle_recall(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle recall tool."""
        user_id = args["user_id"]
        project_id = args.get("project_id")
        query = args["query"]
        limit = args.get("limit", 10)

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)[0]

        # Search memories
        results_df = self.db_client.search_memories(
            user_id=user_id,
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
        )

        # Convert results
        memories = []
        if not results_df.is_empty():
            for row in results_df.to_dicts():
                memories.append(
                    {
                        "memory_id": row["memory_id"],
                        "content": row["content"],
                        "metadata": json.loads(row.get("metadata", "{}")),
                        "importance": row.get("importance", 1.0),
                        "similarity_score": row.get("_similarity", 0.0),
                    }
                )

        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
        }

    async def _handle_create_project(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle create project tool."""
        user_id = args["user_id"]
        name = args["name"]
        description = args.get("description", "")
        metadata = args.get("metadata", {})

        # Create project
        project_id = str(uuid4())
        self.db_client.create_project(
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
        """Handle create knowledge base tool."""
        user_id = args["user_id"]
        project_id = args["project_id"]
        name = args["name"]
        description = args.get("description", "")

        # Create knowledge base
        kb_id = str(uuid4())
        self.db_client.create_knowledge_base(
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
        """Handle add fact tool."""
        kb_id = args["kb_id"]
        content = args["content"]
        parent_id = args.get("parent_id")
        metadata = args.get("metadata", {})

        # Generate embedding
        embedding = self.embedding_service.embed_text(content)[0]

        # Add fact
        fact_id = str(uuid4())
        self.db_client.add_fact(
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
        """Handle search facts tool."""
        kb_id = args["kb_id"]
        query = args["query"]
        limit = args.get("limit", 10)

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)[0]

        # Search facts
        results_df = self.db_client.search_facts(
            kb_id=kb_id,
            query_embedding=query_embedding,
            limit=limit,
        )

        # Convert results
        facts = []
        if not results_df.is_empty():
            for row in results_df.to_dicts():
                facts.append(
                    {
                        "fact_id": row["fact_id"],
                        "content": row["content"],
                        "parent_id": row.get("parent_id"),
                        "metadata": json.loads(row.get("metadata", "{}")),
                        "similarity_score": row.get("_similarity", 0.0),
                    }
                )

        return {
            "success": True,
            "facts": facts,
            "count": len(facts),
        }

    async def _handle_summarize_for_knowledge(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle summarize for knowledge tool."""
        content = args["content"]
        context = args.get("context")
        skip_summarization = args.get("skip_summarization", False)
        provided_summary = args.get("provided_summary")

        # Use LLM service to generate knowledge instructions
        result = self.llm_service.summarize_for_knowledge(
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
    """Main entry point for MCP server."""
    import asyncio

    server = MCPMemoryServer()
    asyncio.run(server.run())
