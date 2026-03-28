"""SQLite backend plugin implementation with namespace, key, tags, and TTL support."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..plugin_interface import Capability


class SQLiteBackendPlugin:
    """SQLite backend plugin implementation.

    Supports:
    - Namespace-scoped memory storage
    - Key-based exact retrieval and wildcard matching
    - Tags for filtering and categorization
    - TTL (time-to-live) with ISO date expiry
    - Append mode for key-based content concatenation
    - Version history per key
    - Export/import
    """

    # Sentinel for in-memory database (useful for testing)
    IN_MEMORY = ":memory:"

    def __init__(self, db_path=None):
        """Initialize the SQLite backend plugin.

        Args:
            db_path: Path to SQLite DB file, or ":memory:" for in-memory.
                     Defaults to ~/.hanzo/memory.db.
        """
        if db_path == self.IN_MEMORY:
            self._db_path = self.IN_MEMORY
        else:
            self._db_path = db_path or Path.home() / ".hanzo" / "memory.db"
        self._client = None
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def capabilities(self) -> List[Capability]:
        return [
            Capability.PERSISTENCE,
            Capability.EMBEDDINGS,
            Capability.MARKDOWN_IMPORT,
            Capability.STRUCTURED_QUERY,
            Capability.VECTOR_SEARCH,
        ]

    async def initialize(self) -> None:
        """Initialize the backend."""
        if not self._initialized:
            if self._db_path == self.IN_MEMORY:
                # Pure in-memory — skip hanzo_memory client, use direct sqlite3
                self._conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
            else:
                # Use hanzo_memory SQLiteMemoryClient if available
                try:
                    from hanzo_memory.db.sqlite_client import SQLiteMemoryClient

                    self._client = SQLiteMemoryClient(db_path=self._db_path)
                    self._conn = self._client.conn
                except Exception:
                    db_str = str(self._db_path)
                    self._conn = sqlite3.connect(db_str, check_same_thread=False)
                    self._conn.row_factory = sqlite3.Row

            self._ensure_schema()
            self._initialized = True

    def _ensure_schema(self):
        """Ensure the memories table has all required columns."""
        conn = self._conn
        if not conn:
            return

        # Create the memories table if it doesn't exist (standalone mode)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                memory_id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL DEFAULT 'default',
                user_id TEXT NOT NULL DEFAULT 'default',
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'general',
                importance REAL DEFAULT 0.5,
                context TEXT,
                metadata TEXT,
                source TEXT,
                embedding BLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Add namespace column if missing
        self._add_column_if_missing("memories", "namespace", "TEXT DEFAULT 'default'")
        # Add key column if missing
        self._add_column_if_missing("memories", "key", "TEXT")
        # Add tags column (JSON array as TEXT)
        self._add_column_if_missing("memories", "tags", "TEXT")
        # Add ttl column (ISO date string)
        self._add_column_if_missing("memories", "ttl", "TEXT")

        # Create indexes for new columns
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace);"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_ns_key ON memories(namespace, key);"
        )
        conn.commit()

    def _add_column_if_missing(self, table: str, column: str, col_type: str):
        """Add a column to a table if it doesn't already exist."""
        conn = self._conn
        if not conn:
            return
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

    async def shutdown(self) -> None:
        """Shutdown the backend."""
        if self._client:
            self._client.close()
            self._client = None
        elif self._conn:
            self._conn.close()
        self._conn = None
        self._initialized = False

    # ------------------------------------------------------------------ #
    # Core CRUD (backward-compatible signatures + new params)
    # ------------------------------------------------------------------ #

    async def store_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        user_id: str = "default",
        project_id: str = "default",
        namespace: str = "default",
        key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ttl: Optional[str] = None,
        append: bool = False,
    ) -> str:
        """Store a memory and return its ID."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        # Inject namespace/key/tags into metadata for backward compat
        metadata = dict(metadata)
        metadata["namespace"] = namespace
        if key:
            metadata["key"] = key
        if tags:
            metadata["tags"] = tags
        if ttl:
            metadata["ttl"] = ttl

        # Handle append mode: find existing entry with same key+namespace and concatenate
        if append and key:
            existing = self._find_by_key(key, namespace)
            if existing:
                new_content = existing["content"] + content
                self._conn.execute(
                    "UPDATE memories SET content = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE memory_id = ?",
                    (new_content, json.dumps(metadata), existing["memory_id"]),
                )
                self._conn.commit()
                return existing["memory_id"]

        memory_id = str(uuid.uuid4())
        tags_json = json.dumps(tags or [])
        metadata_json = json.dumps(metadata)

        self._conn.execute(
            """
            INSERT INTO memories
            (id, memory_id, user_id, project_id, content, importance, context,
             metadata, source, embedding, namespace, key, tags, ttl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                memory_id,
                user_id,
                project_id,
                content,
                metadata.get("importance", 0.5),
                json.dumps({}),
                metadata_json,
                metadata.get("source", ""),
                None,  # embedding
                namespace,
                key,
                tags_json,
                ttl,
            ),
        )
        self._conn.commit()
        return memory_id

    async def retrieve_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        where_parts = ["user_id = ?", "project_id = ?"]
        params: list = [user_id, project_id]

        if namespace:
            where_parts.append("namespace = ?")
            params.append(namespace)

        if metadata_filter:
            ns = metadata_filter.get("namespace")
            if ns:
                where_parts.append("namespace = ?")
                params.append(ns)
            agent = metadata_filter.get("agent")
            if agent:
                where_parts.append("json_extract(metadata, '$.agent') = ?")
                params.append(agent)
            mtype = metadata_filter.get("type")
            if mtype:
                where_parts.append("json_extract(metadata, '$.type') = ?")
                params.append(mtype)

        # Content search via LIKE if query provided
        if query:
            where_parts.append("content LIKE ?")
            params.append(f"%{query}%")

        # Filter out expired TTL entries
        where_parts.append("(ttl IS NULL OR ttl = '' OR ttl > ?)")
        params.append(datetime.now(timezone.utc).isoformat())

        where_clause = " AND ".join(where_parts)
        params.append(limit)

        cursor = self._conn.execute(
            f"SELECT * FROM memories WHERE {where_clause} ORDER BY created_at DESC LIMIT ?",
            params,
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    async def search_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search memories based on query with scoring."""
        return await self.retrieve_memory(
            query, user_id, project_id, limit, namespace, metadata_filter
        )

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str = "default",
        project_id: str = "default",
    ) -> bool:
        """Delete a memory by ID."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        cursor = self._conn.execute(
            "DELETE FROM memories WHERE memory_id = ?",
            (memory_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # New operations for TypeScript parity
    # ------------------------------------------------------------------ #

    async def get_by_key(
        self,
        key: str,
        namespace: str = "default",
    ):
        """Get memory by exact key or wildcard within namespace.

        If key contains '*', returns a list of matches.
        Otherwise returns a single dict or None.
        """
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        now = datetime.now(timezone.utc).isoformat()

        if "*" in key:
            # Wildcard: convert glob to SQL LIKE
            like_pattern = key.replace("*", "%")
            cursor = self._conn.execute(
                """SELECT * FROM memories
                   WHERE key LIKE ? AND namespace = ?
                   AND (ttl IS NULL OR ttl = '' OR ttl > ?)
                   ORDER BY created_at DESC""",
                (like_pattern, namespace, now),
            )
            rows = cursor.fetchall()
            return [self._row_to_dict(r) for r in rows] if rows else []
        else:
            row_dict = self._find_by_key(key, namespace)
            if row_dict and self._is_expired(row_dict):
                return None
            return row_dict

    async def list_memories(
        self,
        namespace: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List all memories with optional filters."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        where_parts: list = []
        params: list = []

        if namespace:
            where_parts.append("namespace = ?")
            params.append(namespace)

        if tag:
            # tags is a JSON array stored as TEXT; use json_each to filter
            where_parts.append(
                "EXISTS (SELECT 1 FROM json_each(tags) WHERE json_each.value = ?)"
            )
            params.append(tag)

        # Filter expired
        now = datetime.now(timezone.utc).isoformat()
        where_parts.append("(ttl IS NULL OR ttl = '' OR ttl > ?)")
        params.append(now)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        params.append(limit)

        cursor = self._conn.execute(
            f"SELECT * FROM memories WHERE {where_clause} ORDER BY created_at DESC LIMIT ?",
            params,
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    async def namespaces(self) -> Dict[str, int]:
        """Return all namespaces with their memory counts (excludes expired)."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        now = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.execute(
            """SELECT namespace, COUNT(*) as cnt FROM memories
               WHERE (ttl IS NULL OR ttl = '' OR ttl > ?)
               GROUP BY namespace""",
            (now,),
        )
        return {row[0] or "default": row[1] for row in cursor.fetchall()}

    async def stats(self) -> Dict[str, Any]:
        """Return count, namespaces, size info."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        ns = await self.namespaces()
        total = sum(ns.values())
        return {
            "count": total,
            "namespaces": ns,
        }

    async def clear(self, namespace: Optional[str] = None) -> int:
        """Clear all or namespace-specific memories. Returns count deleted."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        if namespace:
            cursor = self._conn.execute(
                "DELETE FROM memories WHERE namespace = ?", (namespace,)
            )
        else:
            cursor = self._conn.execute("DELETE FROM memories")

        self._conn.commit()
        return cursor.rowcount

    async def tag_memory(self, memory_id: str, tag: str) -> bool:
        """Add a tag to a memory."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        cursor = self._conn.execute(
            "SELECT tags, metadata FROM memories WHERE memory_id = ?", (memory_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False

        tags = json.loads(row[0]) if row[0] else []
        if tag not in tags:
            tags.append(tag)

        # Also update tags in metadata
        metadata = json.loads(row[1]) if row[1] else {}
        metadata["tags"] = tags

        self._conn.execute(
            "UPDATE memories SET tags = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE memory_id = ?",
            (json.dumps(tags), json.dumps(metadata), memory_id),
        )
        self._conn.commit()
        return True

    async def untag_memory(self, memory_id: str, tag: str) -> bool:
        """Remove a tag from a memory."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        cursor = self._conn.execute(
            "SELECT tags, metadata FROM memories WHERE memory_id = ?", (memory_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False

        tags = json.loads(row[0]) if row[0] else []
        if tag in tags:
            tags.remove(tag)
        else:
            return False

        metadata = json.loads(row[1]) if row[1] else {}
        metadata["tags"] = tags

        self._conn.execute(
            "UPDATE memories SET tags = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE memory_id = ?",
            (json.dumps(tags), json.dumps(metadata), memory_id),
        )
        self._conn.commit()
        return True

    async def history(
        self, key: str, namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """Show all versions/entries for a key within a namespace, ordered by creation time."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        cursor = self._conn.execute(
            "SELECT * FROM memories WHERE key = ? AND namespace = ? ORDER BY created_at ASC",
            (key, namespace),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    async def export_memories(
        self, namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Export memories as a list of dicts."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        if namespace:
            cursor = self._conn.execute(
                "SELECT * FROM memories WHERE namespace = ? ORDER BY created_at ASC",
                (namespace,),
            )
        else:
            cursor = self._conn.execute(
                "SELECT * FROM memories ORDER BY created_at ASC"
            )

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    async def import_memories(self, data: List[Dict[str, Any]]) -> int:
        """Import memories from exported data. Returns count imported."""
        if not self._conn:
            raise RuntimeError("Plugin not initialized")

        count = 0
        for entry in data:
            memory_id = entry.get("memory_id") or entry.get("id") or str(uuid.uuid4())
            metadata = entry.get("metadata", {})
            namespace = metadata.get("namespace", entry.get("namespace", "default"))
            key = metadata.get("key", entry.get("key"))
            tags = metadata.get("tags", entry.get("tags", []))
            ttl = metadata.get("ttl", entry.get("ttl"))

            self._conn.execute(
                """
                INSERT INTO memories
                (id, memory_id, user_id, project_id, content, importance, context,
                 metadata, source, embedding, namespace, key, tags, ttl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    memory_id,
                    entry.get("user_id", "default"),
                    entry.get("project_id", "default"),
                    entry.get("content", ""),
                    entry.get("importance", 0.5),
                    json.dumps(entry.get("context", {})),
                    json.dumps(metadata),
                    entry.get("source", ""),
                    None,
                    namespace,
                    key,
                    json.dumps(tags if isinstance(tags, list) else []),
                    ttl,
                ),
            )
            count += 1

        self._conn.commit()
        return count

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _find_by_key(self, key: str, namespace: str) -> Optional[Dict[str, Any]]:
        """Find a single memory by exact key + namespace."""
        if not self._conn:
            return None
        cursor = self._conn.execute(
            "SELECT * FROM memories WHERE key = ? AND namespace = ? ORDER BY created_at DESC LIMIT 1",
            (key, namespace),
        )
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def _is_expired(self, memory: Dict[str, Any]) -> bool:
        """Check if a memory's TTL has expired."""
        ttl = memory.get("ttl") or (memory.get("metadata", {}).get("ttl"))
        if not ttl:
            return False
        try:
            expiry = datetime.fromisoformat(ttl)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > expiry
        except (ValueError, TypeError):
            return False

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a dict with parsed JSON fields."""
        if row is None:
            return {}

        # sqlite3.Row supports both index and key access
        d = dict(row) if hasattr(row, "keys") else {}
        if not d:
            # Fallback for tuple rows
            return {}

        # Parse JSON fields
        for field in ("metadata", "context"):
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    d[field] = {}

        if "tags" in d and isinstance(d["tags"], str):
            try:
                d["tags"] = json.loads(d["tags"])
            except (json.JSONDecodeError, TypeError):
                d["tags"] = []

        return d
