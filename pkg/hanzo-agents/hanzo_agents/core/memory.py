"""Memory backends for long-term agent storage."""

import json
import asyncio
import sqlite3
from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime


class MemoryKV(Protocol):
    """Key-value store protocol for long-term memory."""

    async def save(self, key: str, value: Dict[str, Any]) -> None:
        """Save value with key."""
        ...

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load value by key."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        ...

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by prefix."""
        ...


class MemoryVector(Protocol):
    """Vector store protocol for semantic search."""

    async def add(
        self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add text with metadata to vector store."""
        ...

    async def query(self, text: str, k: int = 5) -> List[str]:
        """Query for similar texts."""
        ...

    async def delete(self, id: str) -> bool:
        """Delete by ID."""
        ...


# Default implementations


class SQLiteKV(MemoryKV):
    """SQLite-based key-value store."""

    def __init__(self, db_path: str = "memory.db"):
        """Initialize SQLite store."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()

    async def save(self, key: str, value: Dict[str, Any]) -> None:
        """Save value."""

        def _save():
            conn = sqlite3.connect(self.db_path)
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO kv_store (key, value, metadata, created_at, updated_at)
                VALUES (?, ?, ?, 
                        COALESCE((SELECT created_at FROM kv_store WHERE key = ?), ?),
                        ?)
            """,
                (key, json.dumps(value), "{}", key, now, now),
            )
            conn.commit()
            conn.close()

        await asyncio.get_event_loop().run_in_executor(None, _save)

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load value."""

        def _load():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])
            return None

        return await asyncio.get_event_loop().run_in_executor(None, _load)

    async def delete(self, key: str) -> bool:
        """Delete value."""

        def _delete():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys."""

        def _list():
            conn = sqlite3.connect(self.db_path)
            if prefix:
                cursor = conn.execute(
                    "SELECT key FROM kv_store WHERE key LIKE ?", (f"{prefix}%",)
                )
            else:
                cursor = conn.execute("SELECT key FROM kv_store")

            keys = [row[0] for row in cursor.fetchall()]
            conn.close()
            return keys

        return await asyncio.get_event_loop().run_in_executor(None, _list)


class InMemoryKV(MemoryKV):
    """Simple in-memory key-value store."""

    def __init__(self):
        """Initialize in-memory store."""
        self._store: Dict[str, Dict[str, Any]] = {}

    async def save(self, key: str, value: Dict[str, Any]) -> None:
        """Save value."""
        self._store[key] = value.copy()

    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load value."""
        return self._store.get(key, {}).copy() if key in self._store else None

    async def delete(self, key: str) -> bool:
        """Delete value."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys."""
        if prefix:
            return [k for k in self._store.keys() if k.startswith(prefix)]
        return list(self._store.keys())


class SimpleVectorMemory(MemoryVector):
    """Simple vector memory using basic similarity."""

    def __init__(self):
        """Initialize vector store."""
        self._store: Dict[str, Dict[str, Any]] = {}

    async def add(
        self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add text."""
        self._store[id] = {
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def query(self, text: str, k: int = 5) -> List[str]:
        """Simple keyword-based search."""
        # Very basic - just find texts containing query words
        query_words = set(text.lower().split())
        scores = []

        for id, item in self._store.items():
            item_words = set(item["text"].lower().split())
            # Jaccard similarity
            score = (
                len(query_words & item_words) / len(query_words | item_words)
                if query_words | item_words
                else 0
            )
            scores.append((score, id, item["text"]))

        # Sort by score and return top k
        scores.sort(reverse=True, key=lambda x: x[0])
        return [text for _, _, text in scores[:k]]

    async def delete(self, id: str) -> bool:
        """Delete by ID."""
        if id in self._store:
            del self._store[id]
            return True
        return False


# Factory functions


def create_memory_kv(backend: str = "sqlite", **kwargs) -> MemoryKV:
    """Create memory KV store."""
    if backend == "sqlite":
        return SQLiteKV(**kwargs)
    elif backend == "memory":
        return InMemoryKV(**kwargs)
    else:
        raise ValueError(f"Unknown KV backend: {backend}")


def create_memory_vector(backend: str = "simple", **kwargs) -> MemoryVector:
    """Create vector memory store."""
    if backend == "simple":
        return SimpleVectorMemory(**kwargs)
    # Add more backends as needed (faiss, chromadb, etc.)
    else:
        raise ValueError(f"Unknown vector backend: {backend}")
