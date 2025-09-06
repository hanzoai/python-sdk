"""InfinityDB client for vector storage and search."""

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from structlog import get_logger

from ..config import settings
from .base import BaseVectorDB

logger = get_logger()

# Try to import InfinityDB, fall back to mock for unsupported platforms
try:
    import infinity_embedded

    logger.info("Using InfinityDB")
except ImportError:
    logger.warning(
        f"InfinityDB not available on {platform.system()} {platform.machine()}, using mock implementation"
    )
    from . import mock_infinity as infinity_embedded


class InfinityClient(BaseVectorDB):
    """Client for InfinityDB operations."""

    def __init__(self, db_path: str | None = None):
        """Initialize InfinityDB client."""
        self.db_path = db_path or settings.infinity_db_str
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.infinity = infinity_embedded.connect(self.db_path)
        self._ensure_databases()

    def _ensure_databases(self) -> None:
        """Ensure required databases exist."""
        # Create main databases
        for db_name in ["projects", "memories", "knowledge", "chats"]:
            try:
                self.infinity.create_database(db_name)
                logger.info(f"Created database: {db_name}")
            except Exception:
                # Database already exists
                pass

    def _get_db(self, db_name: str) -> Any:
        """Get a database object."""
        return self.infinity.get_database(db_name)

    # Project Management
    def create_projects_table(self) -> None:
        """Create projects table if not exists."""
        db = self._get_db("projects")
        try:
            db.create_table(
                "projects",
                {
                    "project_id": {"type": "varchar"},
                    "user_id": {"type": "varchar"},
                    "name": {"type": "varchar"},
                    "description": {"type": "varchar"},
                    "metadata": {"type": "varchar"},  # JSON string
                    "created_at": {"type": "varchar"},
                    "updated_at": {"type": "varchar"},
                },
            )
            logger.info("Created projects table")
        except Exception as e:
            logger.debug(f"Projects table may already exist: {e}")

    def create_project(
        self,
        project_id: str,
        user_id: str,
        name: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new project."""
        db = self._get_db("projects")
        table = db.get_table("projects")

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

        table.insert([project_data])
        return project_data

    # Memory Management
    def create_memories_table(self, user_id: str) -> None:
        """Create memories table for a user if not exists."""
        db = self._get_db("memories")
        table_name = f"memories_{user_id}"

        try:
            db.create_table(
                table_name,
                {
                    "memory_id": {"type": "varchar"},
                    "user_id": {"type": "varchar"},
                    "project_id": {"type": "varchar"},
                    "content": {"type": "varchar"},
                    "embedding": {
                        "type": f"vector,{settings.embedding_dimensions},float"
                    },
                    "metadata": {"type": "varchar"},  # JSON string
                    "importance": {"type": "float"},
                    "created_at": {"type": "varchar"},
                    "updated_at": {"type": "varchar"},
                },
            )
            logger.info(f"Created memories table for user: {user_id}")
        except Exception:
            pass

    def add_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        importance: float = 1.0,
    ) -> dict[str, Any]:
        """Add a memory to the database."""
        db = self._get_db("memories")
        table_name = f"memories_{user_id}"
        table = db.get_table(table_name)

        now = datetime.now(timezone.utc).isoformat()
        memory_data = {
            "memory_id": memory_id,
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "embedding": embedding,
            "metadata": json.dumps(metadata or {}),
            "importance": importance,
            "created_at": now,
            "updated_at": now,
        }

        table.insert([memory_data])
        return memory_data

    def search_memories(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: str | None = None,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> pl.DataFrame:
        """Search memories using vector similarity."""
        db = self._get_db("memories")
        table_name = f"memories_{user_id}"

        try:
            table = db.get_table(table_name)

            # Build query
            query = table.output(["*"]).match_dense(
                "embedding",
                query_embedding,
                "float",
                "cosine",  # Using cosine similarity
                limit,
            )

            # Apply project filter if specified
            if project_id:
                query = query.filter(f"project_id = '{project_id}'")

            # Execute query and return as polars DataFrame
            return query.to_pl()
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return pl.DataFrame()

    # Knowledge Base Management
    def create_knowledge_bases_table(self) -> None:
        """Create knowledge bases table if not exists."""
        db = self._get_db("knowledge")
        try:
            db.create_table(
                "knowledge_bases",
                {
                    "kb_id": {"type": "varchar"},
                    "user_id": {"type": "varchar"},
                    "project_id": {"type": "varchar"},
                    "name": {"type": "varchar"},
                    "description": {"type": "varchar"},
                    "metadata": {"type": "varchar"},  # JSON string
                    "created_at": {"type": "varchar"},
                    "updated_at": {"type": "varchar"},
                },
            )
            logger.info("Created knowledge_bases table")
        except Exception as e:
            logger.debug(f"Knowledge bases table may already exist: {e}")

    def create_knowledge_base(
        self,
        kb_id: str,
        user_id: str,
        project_id: str,
        name: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new knowledge base."""
        db = self._get_db("knowledge")
        table = db.get_table("knowledge_bases")

        now = datetime.now(timezone.utc).isoformat()
        kb_data = {
            "kb_id": kb_id,
            "user_id": user_id,
            "project_id": project_id,
            "name": name,
            "description": description,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }

        table.insert([kb_data])

        # Create facts table for this knowledge base
        self._create_facts_table(kb_id)

        return kb_data

    def _create_facts_table(self, kb_id: str) -> None:
        """Create facts table for a knowledge base."""
        db = self._get_db("knowledge")
        table_name = f"facts_{kb_id}"

        try:
            db.create_table(
                table_name,
                {
                    "fact_id": {"type": "varchar"},
                    "kb_id": {"type": "varchar"},
                    "content": {"type": "varchar"},
                    "embedding": {
                        "type": f"vector,{settings.embedding_dimensions},float"
                    },
                    "parent_id": {"type": "varchar"},
                    "metadata": {"type": "varchar"},  # JSON string
                    "created_at": {"type": "varchar"},
                    "updated_at": {"type": "varchar"},
                },
            )
            logger.info(f"Created facts table for kb: {kb_id}")
        except Exception:
            pass

    def add_fact(
        self,
        fact_id: str,
        kb_id: str,
        content: str,
        embedding: list[float],
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a fact to a knowledge base."""
        db = self._get_db("knowledge")
        table_name = f"facts_{kb_id}"
        table = db.get_table(table_name)

        now = datetime.now(timezone.utc).isoformat()
        fact_data = {
            "fact_id": fact_id,
            "kb_id": kb_id,
            "content": content,
            "embedding": embedding,
            "parent_id": parent_id or "",
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }

        table.insert([fact_data])
        return fact_data

    def search_facts(
        self,
        kb_id: str,
        query_embedding: list[float],
        limit: int = 10,
        parent_id: str | None = None,
    ) -> pl.DataFrame:
        """Search facts in a knowledge base."""
        db = self._get_db("knowledge")
        table_name = f"facts_{kb_id}"

        try:
            table = db.get_table(table_name)

            # Build query
            query = table.output(["*"]).match_dense(
                "embedding", query_embedding, "float", "cosine", limit
            )

            # Apply parent filter if specified
            if parent_id:
                query = query.filter(f"parent_id = '{parent_id}'")

            return query.to_pl()
        except Exception as e:
            logger.error(f"Error searching facts: {e}")
            return pl.DataFrame()

    # Chat Management
    def create_chats_table(self, user_id: str) -> None:
        """Create chats table for a user."""
        db = self._get_db("chats")
        table_name = f"chats_{user_id}"

        try:
            db.create_table(
                table_name,
                {
                    "chat_id": {"type": "varchar"},
                    "user_id": {"type": "varchar"},
                    "project_id": {"type": "varchar"},
                    "session_id": {"type": "varchar"},
                    "role": {"type": "varchar"},  # user, assistant, system
                    "content": {"type": "varchar"},
                    "embedding": {
                        "type": f"vector,{settings.embedding_dimensions},float"
                    },
                    "metadata": {"type": "varchar"},  # JSON string
                    "created_at": {"type": "varchar"},
                },
            )
            logger.info(f"Created chats table for user: {user_id}")
        except Exception:
            pass

    def add_chat_message(
        self,
        chat_id: str,
        user_id: str,
        project_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a chat message."""
        db = self._get_db("chats")
        table_name = f"chats_{user_id}"
        table = db.get_table(table_name)

        chat_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "embedding": embedding,
            "metadata": json.dumps(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        table.insert([chat_data])
        return chat_data

    def get_chat_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 100,
    ) -> pl.DataFrame:
        """Get chat history for a session."""
        db = self._get_db("chats")
        table_name = f"chats_{user_id}"

        try:
            table = db.get_table(table_name)

            # Get messages for session ordered by created_at
            query = table.output(["*"]).filter(f"session_id = '{session_id}'")

            # TODO: Add proper ordering once InfinityDB supports it
            return query.to_pl()
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return pl.DataFrame()

    def search_chats(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: str | None = None,
        session_id: str | None = None,
        limit: int = 10,
    ) -> pl.DataFrame:
        """Search chat messages."""
        db = self._get_db("chats")
        table_name = f"chats_{user_id}"

        try:
            table = db.get_table(table_name)

            # Build query
            query = table.output(["*"]).match_dense(
                "embedding", query_embedding, "float", "cosine", limit
            )

            # Apply filters
            if project_id:
                query = query.filter(f"project_id = '{project_id}'")
            if session_id:
                query = query.filter(f"session_id = '{session_id}'")

            return query.to_pl()
        except Exception as e:
            logger.error(f"Error searching chats: {e}")
            return pl.DataFrame()

    def close(self) -> None:
        """Close the InfinityDB connection."""
        if hasattr(self, "infinity"):
            # InfinityDB embedded doesn't have explicit close method
            pass


# Global client instance
_client: InfinityClient | None = None


def get_client() -> InfinityClient:
    """Get or create the global InfinityDB client."""
    global _client
    if _client is None:
        _client = InfinityClient()
    return _client
