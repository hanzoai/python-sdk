"""SQLite-based memory storage implementation with vector search using sqlite-vec."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from structlog import get_logger

from .base import BaseVectorDB

logger = get_logger()


class SQLiteMemoryClient(BaseVectorDB):
    """SQLite-based implementation of the vector database with sqlite-vec for vector search."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize SQLite memory storage.

        Args:
            db_path: Path to SQLite database file. Defaults to in-memory if None.
        """
        if db_path is None:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path)

        # Connect to database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

        # Enable extension loading for sqlite-vec
        self.conn.enable_load_extension(True)

        # Initialize tables
        self._init_tables()

        logger.info(f"Initialized SQLite memory storage at {self.db_path}")

    async def initialize(self) -> None:
        """Initialize the database (no-op for local storage)."""
        logger.info("SQLite memory storage initialized")

    def _init_tables(self):
        """Initialize required tables."""
        # Enable sqlite-vec extension
        try:
            self.conn.execute("SELECT load_extension('vec');")
        except sqlite3.Error as e:
            logger.warning(f"Could not load sqlite-vec extension: {e}")
            logger.warning("Vector search functionality will be limited")

        # Create projects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                project_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                user_id TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create memories table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                memory_id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'general',
                importance REAL DEFAULT 0.5,
                context TEXT,
                metadata TEXT,
                source TEXT,
                embedding BLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            );
        """)

        # Create facts table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                fact_id TEXT UNIQUE NOT NULL,
                knowledge_base_id TEXT NOT NULL,
                content TEXT NOT NULL,
                subject TEXT,
                predicate TEXT,
                object TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create knowledge bases table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id TEXT PRIMARY KEY,
                kb_id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            );
        """)

        # Create chat sessions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create chat messages table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                message_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            );
        """)

        # Create indexes
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_user_project ON memories(user_id, project_id);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_facts_kb ON facts(knowledge_base_id);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_project ON chat_sessions(user_id, project_id);"
        )

        # Create vector index for embeddings if sqlite-vec is available
        try:
            # Create vector index for memories
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_embedding 
                ON memories (vec_to_json16(embedding)) 
                WHERE embedding IS NOT NULL;
            """)

            # Create vector index for facts
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_embedding 
                ON facts (vec_to_json16(embedding)) 
                WHERE embedding IS NOT NULL;
            """)

            # Create vector index for chat messages
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_embedding 
                ON chat_messages (vec_to_json16(embedding)) 
                WHERE embedding IS NOT NULL;
            """)
        except sqlite3.Error:
            # If sqlite-vec is not available, skip vector indexes
            pass

        self.conn.commit()

    def create_project(
        self,
        project_id: str,
        user_id: str,
        name: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new project."""
        project_id = project_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        self.conn.execute(
            """
            INSERT INTO projects (id, project_id, user_id, name, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), project_id, user_id, name, description, metadata_json),
        )
        self.conn.commit()

        return {
            "id": project_id,
            "project_id": project_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """Get all projects for a user."""
        cursor = self.conn.execute(
            "SELECT * FROM projects WHERE user_id = ?", (user_id,)
        )
        rows = cursor.fetchall()

        projects = []
        for row in rows:
            projects.append(
                {
                    "id": row["id"],
                    "project_id": row["project_id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        return projects

    def create_memories_table(self, user_id: str) -> None:
        """Create a memories table for a user (already handled in initialization)."""
        # Table is created during initialization
        pass

    def add_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
        importance: float = 0.5,
    ) -> dict[str, Any]:
        """Add a memory to the database."""
        memory_id = memory_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})
        context_json = json.dumps({})
        embedding_blob = (
            np.array(embedding, dtype=np.float32).tobytes() if embedding else None
        )

        self.conn.execute(
            """
            INSERT INTO memories 
            (id, memory_id, user_id, project_id, content, importance, context, metadata, source, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                memory_id,
                user_id,
                project_id,
                content,
                importance,
                context_json,
                metadata_json,
                "",  # source
                embedding_blob,
            ),
        )
        self.conn.commit()

        return {
            "id": memory_id,
            "memory_id": memory_id,
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "importance": importance,
            "context": {},
            "metadata": metadata or {},
            "source": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def search_memories(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: str | None = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search memories by similarity."""
        query_array = np.array(query_embedding, dtype=np.float32)
        query_blob = query_array.tobytes()

        # Build query
        where_conditions = ["user_id = ?"]
        params = [user_id]

        if project_id:
            where_conditions.append("project_id = ?")
            params.append(project_id)

        where_clause = " AND ".join(where_conditions)

        # If sqlite-vec is available, use vector similarity search
        try:
            # Use sqlite-vec for similarity search
            cursor = self.conn.execute(
                f"""
                SELECT *, vec_distance_L2(embedding, ?) as distance
                FROM memories
                WHERE {where_clause} AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT ?
            """,
                [query_blob] + params + [limit],
            )

            rows = cursor.fetchall()

            results = []
            for row in rows:
                # Calculate similarity from distance (convert L2 distance to similarity)
                distance = row["distance"]
                similarity = 1 / (1 + distance)  # Convert distance to similarity score

                if similarity >= min_similarity:
                    results.append(
                        {
                            "memory_id": row["memory_id"],
                            "user_id": row["user_id"],
                            "project_id": row["project_id"],
                            "content": row["content"],
                            "importance": row["importance"],
                            "context": (
                                json.loads(row["context"]) if row["context"] else {}
                            ),
                            "metadata": (
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            "source": row["source"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "similarity_score": similarity,
                        }
                    )

            return results

        except sqlite3.Error:
            # Fallback to basic search without vector similarity
            cursor = self.conn.execute(
                f"""
                SELECT *
                FROM memories
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                params + [limit],
            )

            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "memory_id": row["memory_id"],
                        "user_id": row["user_id"],
                        "project_id": row["project_id"],
                        "content": row["content"],
                        "importance": row["importance"],
                        "context": json.loads(row["context"]) if row["context"] else {},
                        "metadata": (
                            json.loads(row["metadata"]) if row["metadata"] else {}
                        ),
                        "source": row["source"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "similarity_score": 0.0,  # No similarity calculation without sqlite-vec
                    }
                )

            return results

    def create_knowledge_base(
        self,
        knowledge_base_id: str,
        project_id: str,
        name: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new knowledge base."""
        knowledge_base_id = knowledge_base_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        self.conn.execute(
            """
            INSERT INTO knowledge_bases (id, kb_id, project_id, name, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                knowledge_base_id,
                project_id,
                name,
                description,
                metadata_json,
            ),
        )
        self.conn.commit()

        return {
            "id": knowledge_base_id,
            "kb_id": knowledge_base_id,
            "project_id": project_id,
            "name": name,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_knowledge_bases(self, project_id: str) -> list[dict[str, Any]]:
        """Get all knowledge bases for a project."""
        cursor = self.conn.execute(
            "SELECT * FROM knowledge_bases WHERE project_id = ?", (project_id,)
        )
        rows = cursor.fetchall()

        kbs = []
        for row in rows:
            kbs.append(
                {
                    "id": row["id"],
                    "kb_id": row["kb_id"],
                    "project_id": row["project_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        return kbs

    def add_fact(
        self,
        fact_id: str,
        knowledge_base_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Add a fact to a knowledge base."""
        fact_id = fact_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})
        embedding_blob = (
            np.array(embedding, dtype=np.float32).tobytes() if embedding else None
        )

        self.conn.execute(
            """
            INSERT INTO facts 
            (id, fact_id, knowledge_base_id, content, embedding, metadata, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                fact_id,
                knowledge_base_id,
                content,
                embedding_blob,
                metadata_json,
                confidence,
            ),
        )
        self.conn.commit()

        return {
            "id": fact_id,
            "fact_id": fact_id,
            "knowledge_base_id": knowledge_base_id,
            "content": content,
            "confidence": confidence,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def search_facts(
        self,
        knowledge_base_id: str,
        query_embedding: list[float] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search facts in a knowledge base."""
        if query_embedding is not None:
            # If sqlite-vec is available and we have an embedding, use vector search
            query_array = np.array(query_embedding, dtype=np.float32)
            query_blob = query_array.tobytes()

            try:
                cursor = self.conn.execute(
                    """
                    SELECT *, vec_distance_L2(embedding, ?) as distance
                    FROM facts
                    WHERE knowledge_base_id = ? AND embedding IS NOT NULL
                    ORDER BY distance ASC
                    LIMIT ?
                """,
                    [query_blob, knowledge_base_id, limit],
                )

                rows = cursor.fetchall()

                results = []
                for row in rows:
                    distance = row["distance"]
                    similarity = 1 / (
                        1 + distance
                    )  # Convert distance to similarity score

                    results.append(
                        {
                            "fact_id": row["fact_id"],
                            "knowledge_base_id": row["knowledge_base_id"],
                            "content": row["content"],
                            "confidence": row["confidence"],
                            "metadata": (
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "similarity_score": similarity,
                        }
                    )

                return results
            except sqlite3.Error:
                # Fallback to basic search
                pass

        # Basic search without vector similarity
        cursor = self.conn.execute(
            "SELECT * FROM facts WHERE knowledge_base_id = ? ORDER BY created_at DESC LIMIT ?",
            (knowledge_base_id, limit),
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "fact_id": row["fact_id"],
                    "knowledge_base_id": row["knowledge_base_id"],
                    "content": row["content"],
                    "confidence": row["confidence"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "similarity_score": 0.0,  # No similarity without embedding
                }
            )

        return results

    def delete_fact(self, fact_id: str, knowledge_base_id: str) -> bool:
        """Delete a fact from a knowledge base."""
        cursor = self.conn.execute(
            "DELETE FROM facts WHERE fact_id = ? AND knowledge_base_id = ?",
            (fact_id, knowledge_base_id),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def update_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str | None = None,
        metadata: dict | None = None,
        importance: float | None = None,
    ) -> dict[str, Any] | None:
        """Update a memory in the database."""
        # Check if memory exists and belongs to user/project
        cursor = self.conn.execute(
            "SELECT * FROM memories WHERE memory_id = ? AND user_id = ? AND project_id = ?",
            (memory_id, user_id, project_id),
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Build update query
        updates = []
        params = []

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if importance is not None:
            updates.append("importance = ?")
            params.append(importance)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE memories SET {', '.join(updates)} WHERE memory_id = ?"
            params.append(memory_id)

            self.conn.execute(query, params)
            self.conn.commit()

        # Return updated memory
        cursor = self.conn.execute(
            "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
        )
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "memory_id": row["memory_id"],
                "user_id": row["user_id"],
                "project_id": row["project_id"],
                "content": row["content"],
                "importance": row["importance"],
                "context": json.loads(row["context"]) if row["context"] else {},
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "source": row["source"],
                "timestamp": row["timestamp"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

        return None

    def delete_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
    ) -> bool:
        """Delete a memory from the database."""
        cursor = self.conn.execute(
            "DELETE FROM memories WHERE memory_id = ? AND user_id = ? AND project_id = ?",
            (memory_id, user_id, project_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def create_chat_session(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new chat session."""
        session_id = session_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        self.conn.execute(
            """
            INSERT INTO chat_sessions (id, session_id, user_id, project_id, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), session_id, user_id, project_id, metadata_json),
        )
        self.conn.commit()

        return {
            "id": session_id,
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def add_chat_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Add a message to a chat session."""
        message_id = message_id or str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})
        embedding_blob = (
            np.array(embedding, dtype=np.float32).tobytes() if embedding else None
        )

        self.conn.execute(
            """
            INSERT INTO chat_messages 
            (id, message_id, session_id, role, content, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                message_id,
                session_id,
                role,
                content,
                embedding_blob,
                metadata_json,
            ),
        )
        self.conn.commit()

        return {
            "id": message_id,
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_chat_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get messages from a chat session."""
        query = (
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC"
        )
        params = [session_id]

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        messages = []
        for row in rows:
            messages.append(
                {
                    "id": row["id"],
                    "message_id": row["message_id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "timestamp": row["timestamp"],
                }
            )

        return messages

    def search_chat_messages(
        self,
        session_id: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search messages in a chat session by similarity."""
        query_array = np.array(query_embedding, dtype=np.float32)
        query_blob = query_array.tobytes()

        # If sqlite-vec is available, use vector similarity search
        try:
            cursor = self.conn.execute(
                """
                SELECT *, vec_distance_L2(embedding, ?) as distance
                FROM chat_messages
                WHERE session_id = ? AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT ?
            """,
                [query_blob, session_id, limit],
            )

            rows = cursor.fetchall()

            results = []
            for row in rows:
                distance = row["distance"]
                similarity = 1 / (1 + distance)  # Convert distance to similarity score

                results.append(
                    {
                        "id": row["id"],
                        "message_id": row["message_id"],
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "metadata": (
                            json.loads(row["metadata"]) if row["metadata"] else {}
                        ),
                        "timestamp": row["timestamp"],
                        "similarity_score": similarity,
                    }
                )

            return results
        except sqlite3.Error:
            # Fallback to basic search without vector similarity
            cursor = self.conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit),
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "id": row["id"],
                        "message_id": row["message_id"],
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "metadata": (
                            json.loads(row["metadata"]) if row["metadata"] else {}
                        ),
                        "timestamp": row["timestamp"],
                        "similarity_score": 0.0,  # No similarity calculation without sqlite-vec
                    }
                )

            return results

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()


# Singleton instance
_sqlite_client: Optional[SQLiteMemoryClient] = None


def get_sqlite_client() -> SQLiteMemoryClient:
    """Get or create the singleton SQLite client."""
    global _sqlite_client
    if _sqlite_client is None:
        _sqlite_client = SQLiteMemoryClient()
    return _sqlite_client
