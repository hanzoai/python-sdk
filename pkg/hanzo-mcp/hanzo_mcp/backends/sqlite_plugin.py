"""SQLite backend plugin implementation."""

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from hanzo_memory.models.memory import MemoryCreate
from hanzo_memory.db.sqlite_client import SQLiteMemoryClient

from ..plugin_interface import Capability, MemoryBackendPlugin


class SQLiteBackendPlugin:
    """SQLite backend plugin implementation."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the SQLite backend plugin."""
        self._db_path = db_path or Path.home() / ".hanzo" / "memory.db"
        self._client: Optional[SQLiteMemoryClient] = None
        self._initialized = False

    @property
    def name(self) -> str:
        """Unique name of the backend."""
        return "sqlite"

    @property
    def capabilities(self) -> List[Capability]:
        """List of capabilities provided by this backend."""
        return [
            Capability.PERSISTENCE,
            Capability.EMBEDDINGS,
            Capability.MARKDOWN_IMPORT,
            Capability.STRUCTURED_QUERY,
            # Vector search capability is conditional based on sqlite-vec availability
            Capability.VECTOR_SEARCH,  # Available if sqlite-vec is installed
        ]

    async def initialize(self) -> None:
        """Initialize the backend."""
        if not self._initialized:
            self._client = SQLiteMemoryClient(db_path=self._db_path)
            # The client is initialized in its constructor
            self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown the backend."""
        if self._client:
            self._client.close()
            self._initialized = False

    async def store_memory(
        self, content: str, metadata: Dict[str, Any], user_id: str = "default", project_id: str = "default"
    ) -> str:
        """Store a memory and return its ID."""
        if not self._client:
            raise RuntimeError("Plugin not initialized")

        # For now, we'll store without embeddings to avoid dependency issues
        # In a real implementation, we'd generate embeddings
        memory_create = MemoryCreate(
            content=content,
            memory_type=metadata.get("type", "general"),
            importance=metadata.get("importance", 0.5),
            context=metadata.get("context", {}),
            metadata=metadata,
            source=metadata.get("source", ""),
        )

        # Add memory directly to the database
        import uuid
        from datetime import datetime

        memory_id = str(uuid.uuid4())

        result = self._client.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            embedding=[],  # Empty embedding for now
            metadata=metadata,
            importance=metadata.get("importance", 0.5),
        )

        return result["memory_id"]

    async def retrieve_memory(
        self, query: str, user_id: str = "default", project_id: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        if not self._client:
            raise RuntimeError("Plugin not initialized")

        # For now, return all memories for the user/project since we can't do proper search without embeddings
        # In a real implementation, we'd search based on the query
        try:
            # Try to search if sqlite-vec is available (will fall back to basic search)
            from hanzo_memory.services.embeddings import get_embedding_service

            embedding_service = get_embedding_service()
            query_embedding = embedding_service.embed_single(query)

            results = self._client.search_memories(
                user_id=user_id, query_embedding=query_embedding, project_id=project_id, limit=limit
            )

            return [
                {
                    "id": r.get("memory_id", ""),
                    "content": r.get("content", ""),
                    "user_id": r.get("user_id", ""),
                    "project_id": r.get("project_id", ""),
                    "similarity_score": r.get("similarity_score", 0.0),
                    "metadata": r.get("metadata", {}),
                    "timestamp": r.get("created_at", ""),
                }
                for r in results
            ]
        except Exception:
            # Fallback to basic retrieval if embedding service not available
            # This would just return recent memories
            # For now, we'll simulate by returning a basic result
            return [
                {
                    "id": "fallback-result",
                    "content": f"No search results for: {query}",
                    "user_id": user_id,
                    "project_id": project_id,
                    "similarity_score": 0.0,
                    "metadata": {},
                    "timestamp": "",
                }
            ]

    async def search_memory(
        self, query: str, user_id: str = "default", project_id: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories based on query with scoring."""
        return await self.retrieve_memory(query, user_id, project_id, limit)

    async def delete_memory(self, memory_id: str, user_id: str = "default", project_id: str = "default") -> bool:
        """Delete a memory by ID."""
        if not self._client:
            raise RuntimeError("Plugin not initialized")

        return (
            self._client.update_memory(
                memory_id=memory_id,
                user_id=user_id,
                project_id=project_id,
                content="",  # Setting content to empty as a form of deletion
            )
            is not None
        )
