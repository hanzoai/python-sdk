"""LanceDB client for vector storage and search."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import Field
from structlog import get_logger

from ..config import settings

logger = get_logger()


# Define data models for LanceDB tables
class MemoryModel(LanceModel):
    """Memory data model for LanceDB."""

    memory_id: str = Field(description="Unique memory ID")
    user_id: str = Field(description="User ID")
    project_id: str = Field(description="Project ID")
    content: str = Field(description="Memory content")
    metadata: str = Field(description="JSON metadata")
    importance: float = Field(description="Importance score")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Update timestamp")
    embedding: Vector(settings.embedding_dimensions) = Field(
        description="Embedding vector"
    )


class KnowledgeModel(LanceModel):
    """Knowledge fact data model for LanceDB."""

    fact_id: str = Field(description="Unique fact ID")
    knowledge_base_id: str = Field(description="Knowledge base ID")
    content: str = Field(description="Fact content")
    metadata: str = Field(description="JSON metadata")
    confidence: float = Field(description="Confidence score")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Update timestamp")
    embedding: Vector(settings.embedding_dimensions) = Field(
        description="Embedding vector"
    )


class ProjectModel(LanceModel):
    """Project data model for LanceDB."""

    project_id: str = Field(description="Unique project ID")
    user_id: str = Field(description="User ID")
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    metadata: str = Field(description="JSON metadata")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Update timestamp")


class KnowledgeBaseModel(LanceModel):
    """Knowledge base data model for LanceDB."""

    knowledge_base_id: str = Field(description="Unique knowledge base ID")
    project_id: str = Field(description="Project ID")
    name: str = Field(description="Knowledge base name")
    description: str = Field(description="Knowledge base description")
    metadata: str = Field(description="JSON metadata")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Update timestamp")


class ChatSessionModel(LanceModel):
    """Chat session data model for LanceDB."""

    session_id: str = Field(description="Unique session ID")
    user_id: str = Field(description="User ID")
    project_id: str = Field(description="Project ID")
    metadata: str = Field(description="JSON metadata")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Update timestamp")


class ChatMessageModel(LanceModel):
    """Chat message data model for LanceDB."""

    message_id: str = Field(description="Unique message ID")
    session_id: str = Field(description="Session ID")
    role: str = Field(description="Message role")
    content: str = Field(description="Message content")
    metadata: str = Field(description="JSON metadata")
    created_at: str = Field(description="Creation timestamp")
    embedding: Vector(settings.embedding_dimensions) = Field(
        description="Embedding vector"
    )


class LanceDBClient:
    """Client for LanceDB operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize LanceDB client."""
        self.db_path = db_path or str(settings.lancedb_path.absolute())
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(self.db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        # Create tables if they don't exist
        table_configs = {
            "projects": ProjectModel,
            "knowledge_bases": KnowledgeBaseModel,
            "chat_sessions": ChatSessionModel,
        }

        for table_name, model in table_configs.items():
            if table_name not in self.db.table_names():
                self.db.create_table(table_name, schema=model)
                logger.info(f"Created table: {table_name}")

    def _get_memory_table(self, user_id: str) -> Any:
        """Get or create a user's memory table."""
        table_name = f"memories_{user_id}"
        if table_name not in self.db.table_names():
            self.db.create_table(table_name, schema=MemoryModel)
            logger.info(f"Created memory table: {table_name}")
        return self.db.open_table(table_name)

    def _get_knowledge_table(self, knowledge_base_id: str) -> Any:
        """Get or create a knowledge base facts table."""
        table_name = f"facts_{knowledge_base_id}"
        if table_name not in self.db.table_names():
            self.db.create_table(table_name, schema=KnowledgeModel)
            logger.info(f"Created knowledge table: {table_name}")
        return self.db.open_table(table_name)

    def _get_chat_messages_table(self, session_id: str) -> Any:
        """Get or create a chat session messages table."""
        table_name = f"messages_{session_id}"
        if table_name not in self.db.table_names():
            self.db.create_table(table_name, schema=ChatMessageModel)
            logger.info(f"Created chat messages table: {table_name}")
        return self.db.open_table(table_name)

    # Project operations
    def create_project(
        self,
        project_id: str,
        user_id: str,
        name: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new project."""
        table = self.db.open_table("projects")

        now = datetime.now(timezone.utc).isoformat()
        project_data = {
            "project_id": project_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }

        table.add([project_data])
        logger.info(f"Created project: {project_id}")

        return project_data

    def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """Get all projects for a user."""
        table = self.db.open_table("projects")

        results = (
            table.search()
            .where(f"user_id = '{user_id}'")
            .select(
                [
                    "project_id",
                    "name",
                    "description",
                    "metadata",
                    "created_at",
                    "updated_at",
                ]
            )
            .to_list()
        )

        # Parse JSON metadata
        for result in results:
            result["metadata"] = json.loads(result["metadata"])

        return results

    # Memory operations
    def create_memories_table(self, user_id: str) -> None:
        """Create a memories table for a user (if not exists)."""
        self._get_memory_table(user_id)

    def add_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
        importance: float = 0.5,
    ) -> dict[str, Any]:
        """Add a memory to the database."""
        table = self._get_memory_table(user_id)

        now = datetime.now(timezone.utc).isoformat()
        memory_data = {
            "memory_id": memory_id,
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "importance": importance,
            "created_at": now,
            "updated_at": now,
            "embedding": embedding,
        }

        table.add([memory_data])
        logger.info(f"Added memory: {memory_id} for user: {user_id}")

        return memory_data

    def search_memories(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search memories by similarity."""
        table = self._get_memory_table(user_id)

        # Build the search query - LanceDB v0.24+ API
        search_query = table.search(query_embedding).limit(limit)

        # Add project filter if specified
        if project_id:
            search_query = search_query.where(f"project_id = '{project_id}'")

        # Execute search
        results = search_query.to_list()

        # Parse JSON metadata and add similarity scores
        for _i, result in enumerate(results):
            result["metadata"] = json.loads(result["metadata"])
            # LanceDB returns results ordered by similarity, but doesn't include the score
            # We'll calculate it manually if needed
            result["_distance"] = result.get("_distance", 0.0)

        return results

    # Knowledge base operations
    def create_knowledge_base(
        self,
        knowledge_base_id: str,
        project_id: str,
        name: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new knowledge base."""
        table = self.db.open_table("knowledge_bases")

        now = datetime.now(timezone.utc).isoformat()
        kb_data = {
            "knowledge_base_id": knowledge_base_id,
            "project_id": project_id,
            "name": name,
            "description": description,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }

        table.add([kb_data])
        logger.info(f"Created knowledge base: {knowledge_base_id}")

        return kb_data

    def get_knowledge_bases(self, project_id: str) -> list[dict[str, Any]]:
        """Get all knowledge bases for a project."""
        table = self.db.open_table("knowledge_bases")

        results = (
            table.search()
            .where(f"project_id = '{project_id}'")
            .select(
                [
                    "knowledge_base_id",
                    "name",
                    "description",
                    "metadata",
                    "created_at",
                    "updated_at",
                ]
            )
            .to_list()
        )

        # Parse JSON metadata
        for result in results:
            result["metadata"] = json.loads(result["metadata"])

        return results

    def add_fact(
        self,
        fact_id: str,
        knowledge_base_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Add a fact to a knowledge base."""
        table = self._get_knowledge_table(knowledge_base_id)

        now = datetime.now(timezone.utc).isoformat()
        fact_data = {
            "fact_id": fact_id,
            "knowledge_base_id": knowledge_base_id,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "confidence": confidence,
            "created_at": now,
            "updated_at": now,
            "embedding": embedding,
        }

        table.add([fact_data])
        logger.info(f"Added fact: {fact_id} to knowledge base: {knowledge_base_id}")

        return fact_data

    def search_facts(
        self,
        knowledge_base_id: str,
        query_embedding: Optional[list[float]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search facts in a knowledge base."""
        table = self._get_knowledge_table(knowledge_base_id)

        if query_embedding:
            # Vector search
            results = table.search(query_embedding).limit(limit).to_list()
        else:
            # Return all facts (up to limit)
            results = (
                table.search()
                .limit(limit)
                .select(
                    [
                        "fact_id",
                        "content",
                        "metadata",
                        "confidence",
                        "created_at",
                        "updated_at",
                        "embedding",
                    ]
                )
                .to_list()
            )

        # Parse JSON metadata
        for result in results:
            result["metadata"] = json.loads(result["metadata"])

        return results

    def delete_fact(self, fact_id: str, knowledge_base_id: str) -> bool:
        """Delete a fact from a knowledge base."""
        table = self._get_knowledge_table(knowledge_base_id)

        # LanceDB doesn't have a direct delete by condition yet
        # We need to filter and recreate the table without the fact
        # This is a limitation that might be improved in future versions

        # Get all facts except the one to delete
        remaining_facts = table.search().where(f"fact_id != '{fact_id}'").to_list()

        # Recreate the table with remaining facts
        table_name = f"facts_{knowledge_base_id}"
        self.db.drop_table(table_name)
        self.db.create_table(table_name, schema=KnowledgeModel)

        if remaining_facts:
            table = self.db.open_table(table_name)
            table.add(remaining_facts)

        logger.info(f"Deleted fact: {fact_id} from knowledge base: {knowledge_base_id}")
        return True

    # Chat operations
    def create_chat_session(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new chat session."""
        table = self.db.open_table("chat_sessions")

        now = datetime.now(timezone.utc).isoformat()
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }

        table.add([session_data])
        logger.info(f"Created chat session: {session_id}")

        return session_data

    def add_chat_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Add a message to a chat session."""
        table = self._get_chat_messages_table(session_id)

        now = datetime.now(timezone.utc).isoformat()
        message_data = {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "embedding": embedding,
        }

        table.add([message_data])
        logger.info(f"Added message: {message_id} to session: {session_id}")

        return message_data

    def get_chat_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get messages from a chat session."""
        table = self._get_chat_messages_table(session_id)

        query = table.search()
        if limit:
            query = query.limit(limit)

        results = query.select(
            ["message_id", "role", "content", "metadata", "created_at"]
        ).to_list()

        # Parse JSON metadata and sort by creation time
        for result in results:
            result["metadata"] = json.loads(result["metadata"])

        # Sort by created_at to maintain order
        results.sort(key=lambda x: x["created_at"])

        return results

    def search_chat_messages(
        self,
        session_id: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search messages in a chat session by similarity."""
        table = self._get_chat_messages_table(session_id)

        results = table.search(query_embedding).limit(limit).to_list()

        # Parse JSON metadata
        for result in results:
            result["metadata"] = json.loads(result["metadata"])

        return results

    def close(self) -> None:
        """Close the database connection."""
        # LanceDB doesn't require explicit closing, but we keep this for interface compatibility
        logger.info("Closing LanceDB connection")

    def create_projects_table(self) -> None:
        """Create projects table if not exists."""
        # Already handled in _ensure_tables
        pass

    def create_knowledge_bases_table(self) -> None:
        """Create knowledge bases table if not exists."""
        # Already handled in _ensure_tables
        pass


# Singleton instance
_lancedb_client: Optional[LanceDBClient] = None


def get_lancedb_client() -> LanceDBClient:
    """Get or create the global LanceDB client."""
    global _lancedb_client
    if _lancedb_client is None:
        _lancedb_client = LanceDBClient()
    return _lancedb_client
