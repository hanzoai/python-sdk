"""Hybrid memory management system.

Combines:
- Plaintext markdown files for human-readable rules/context
- SQLite with FTS5 for full-text search
- sqlite-vec for vector similarity search
- Layered search across all storage types
"""

import os
import json
import sqlite3
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

from hanzo_tools.core import PermissionManager


class MemoryManager:
    """Manages hybrid memory system: markdown + SQLite + vectors."""

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.global_memory_dir = Path.home() / ".hanzo" / "memory"
        self.global_memory_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_memory_dir(self, project_path: str) -> Path:
        """Get project memory directory."""
        project_path = Path(project_path)
        memory_dir = project_path / ".hanzo" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        return memory_dir

    def _get_project_db_path(self, project_path: str) -> Path:
        """Get project database path."""
        project_path = Path(project_path)
        db_dir = project_path / ".hanzo" / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "memory.db"

    def _get_global_db_path(self) -> Path:
        """Get global database path."""
        db_dir = Path.home() / ".hanzo" / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "global_memory.db"

    def _init_memory_db(self, db_path: Path) -> sqlite3.Connection:
        """Initialize memory database with FTS5 and vector support."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Enable sqlite-vec extension if available
        try:
            conn.enable_load_extension(True)
            conn.load_extension("vec0")  # sqlite-vec extension
            has_vector = True
        except (sqlite3.Error, AttributeError):
            has_vector = False

        # Create markdown files table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS markdown_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                category TEXT,
                scope TEXT CHECK(scope IN ('global', 'project')),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create FTS5 index for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS markdown_fts USING fts5(
                path, content, category, scope,
                content='markdown_files',
                content_rowid='id'
            )
        """)

        # Create memories table for structured data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                importance INTEGER DEFAULT 5,
                metadata TEXT, -- JSON
                scope TEXT CHECK(scope IN ('global', 'project', 'session')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create FTS5 index for memories
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content, category, metadata,
                content='memories',
                content_rowid='id'
            )
        """)

        if has_vector:
            # Create vector embeddings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_table TEXT NOT NULL, -- 'markdown_files' or 'memories'
                    source_id INTEGER NOT NULL,
                    embedding BLOB, -- Vector embeddings
                    model TEXT DEFAULT 'bge-small-en-v1.5',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create vector index
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_index USING vec0(
                    embedding float[384]  -- BGE small model dimensions
                )
            """)

        # Create triggers to keep FTS in sync
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS markdown_files_ai 
            AFTER INSERT ON markdown_files BEGIN
                INSERT INTO markdown_fts(rowid, path, content, category, scope) 
                VALUES (new.id, new.path, new.content, new.category, new.scope);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS markdown_files_ad 
            AFTER DELETE ON markdown_files BEGIN
                INSERT INTO markdown_fts(markdown_fts, rowid, path, content, category, scope) 
                VALUES('delete', old.id, old.path, old.content, old.category, old.scope);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS markdown_files_au 
            AFTER UPDATE ON markdown_files BEGIN
                INSERT INTO markdown_fts(markdown_fts, rowid, path, content, category, scope) 
                VALUES('delete', old.id, old.path, old.content, old.category, old.scope);
                INSERT INTO markdown_fts(rowid, path, content, category, scope) 
                VALUES (new.id, new.path, new.content, new.category, new.scope);
            END
        """)

        # Similar triggers for memories
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai 
            AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, category, metadata) 
                VALUES (new.id, new.content, new.category, new.metadata);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad 
            AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, category, metadata) 
                VALUES('delete', old.id, old.content, old.category, old.metadata);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au 
            AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, category, metadata) 
                VALUES('delete', old.id, old.content, old.category, old.metadata);
                INSERT INTO memories_fts(rowid, content, category, metadata) 
                VALUES (new.id, new.content, new.category, new.metadata);
            END
        """)

        conn.commit()
        return conn

    # Markdown file operations
    def read_markdown_file(
        self, file_path: str, scope: str = "project", project_path: str = None
    ) -> Optional[str]:
        """Read markdown memory file."""
        if scope == "global":
            full_path = self.global_memory_dir / file_path
        else:
            if not project_path:
                project_path = os.getcwd()
            memory_dir = self._get_project_memory_dir(project_path)
            full_path = memory_dir / file_path

        if not full_path.exists():
            return None

        return full_path.read_text()

    def write_markdown_file(
        self,
        file_path: str,
        content: str,
        scope: str = "project",
        project_path: str = None,
        category: str = None,
    ) -> bool:
        """Write markdown memory file and index in database."""
        if scope == "global":
            full_path = self.global_memory_dir / file_path
            db_path = self._get_global_db_path()
        else:
            if not project_path:
                project_path = os.getcwd()
            memory_dir = self._get_project_memory_dir(project_path)
            full_path = memory_dir / file_path
            db_path = self._get_project_db_path(project_path)

        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        full_path.write_text(content)

        # Update database index
        try:
            conn = self._init_memory_db(db_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO markdown_files 
                (path, content, category, scope, modified_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (str(file_path), content, category, scope),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to index markdown file: {e}")

        return True

    def append_markdown_file(
        self,
        file_path: str,
        content: str,
        scope: str = "project",
        project_path: str = None,
        category: str = None,
    ) -> bool:
        """Append to markdown memory file."""
        existing = self.read_markdown_file(file_path, scope, project_path) or ""

        # Add timestamp and newlines
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if existing:
            new_content = f"{existing}\n\n## {timestamp}\n\n{content}"
        else:
            new_content = f"# {file_path}\n\n## {timestamp}\n\n{content}"

        return self.write_markdown_file(
            file_path, new_content, scope, project_path, category
        )

    def list_markdown_files(
        self, scope: str = "both", project_path: str = None
    ) -> List[Dict[str, Any]]:
        """List all markdown memory files."""
        files = []

        if scope in ("global", "both"):
            global_files = list(self.global_memory_dir.rglob("*.md"))
            files.extend(
                [
                    {
                        "path": str(f.relative_to(self.global_memory_dir)),
                        "full_path": str(f),
                        "scope": "global",
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                    for f in global_files
                ]
            )

        if scope in ("project", "both"):
            if not project_path:
                project_path = os.getcwd()
            memory_dir = self._get_project_memory_dir(project_path)
            project_files = list(memory_dir.rglob("*.md"))
            files.extend(
                [
                    {
                        "path": str(f.relative_to(memory_dir)),
                        "full_path": str(f),
                        "scope": "project",
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                    for f in project_files
                ]
            )

        return sorted(files, key=lambda x: x["modified"], reverse=True)

    # Structured memory operations
    def create_memory(
        self,
        content: str,
        category: str = None,
        importance: int = 5,
        metadata: Dict[str, Any] = None,
        scope: str = "project",
        project_path: str = None,
    ) -> int:
        """Create structured memory record."""
        if scope == "global":
            db_path = self._get_global_db_path()
        else:
            if not project_path:
                project_path = os.getcwd()
            db_path = self._get_project_db_path(project_path)

        conn = self._init_memory_db(db_path)
        cursor = conn.execute(
            """
            INSERT INTO memories (content, category, importance, metadata, scope)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                content,
                category,
                importance,
                json.dumps(metadata) if metadata else None,
                scope,
            ),
        )

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return memory_id

    # Search operations
    def search_memories(
        self,
        query: str,
        scope: str = "both",
        project_path: str = None,
        search_type: str = "fulltext",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search across all memory types."""
        results = []

        # Search markdown files
        markdown_results = self._search_markdown_fulltext(
            query, scope, project_path, limit
        )
        results.extend([{**r, "source": "markdown"} for r in markdown_results])

        # Search structured memories
        memory_results = self._search_structured_memories(
            query, scope, project_path, limit
        )
        results.extend([{**r, "source": "memory"} for r in memory_results])

        # Vector search available when sqlite-vec extension installed

        # Sort by relevance/recency
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:limit]

    def _search_markdown_fulltext(
        self, query: str, scope: str, project_path: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search markdown files using FTS5."""
        results = []

        dbs = []
        if scope in ("global", "both"):
            dbs.append(("global", self._get_global_db_path()))
        if scope in ("project", "both"):
            if not project_path:
                project_path = os.getcwd()
            dbs.append(("project", self._get_project_db_path(project_path)))

        for scope_name, db_path in dbs:
            if not db_path.exists():
                continue

            try:
                conn = self._init_memory_db(db_path)
                cursor = conn.execute(
                    """
                    SELECT m.*, f.rank, 
                           snippet(markdown_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
                    FROM markdown_fts f
                    JOIN markdown_files m ON m.id = f.rowid
                    WHERE markdown_fts MATCH ?
                    ORDER BY f.rank
                    LIMIT ?
                """,
                    (query, limit),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row["id"],
                            "path": row["path"],
                            "content": (
                                row["content"][:500] + "..."
                                if len(row["content"]) > 500
                                else row["content"]
                            ),
                            "snippet": row["snippet"],
                            "category": row["category"],
                            "scope": scope_name,
                            "score": -row["rank"],  # FTS5 rank is negative
                            "created_at": row["created_at"],
                            "modified_at": row["modified_at"],
                        }
                    )

                conn.close()
            except Exception as e:
                print(f"Warning: FTS search failed for {scope_name}: {e}")

        return results

    def _search_structured_memories(
        self, query: str, scope: str, project_path: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search structured memories using FTS5."""
        results = []

        dbs = []
        if scope in ("global", "both"):
            dbs.append(("global", self._get_global_db_path()))
        if scope in ("project", "both"):
            if not project_path:
                project_path = os.getcwd()
            dbs.append(("project", self._get_project_db_path(project_path)))

        for scope_name, db_path in dbs:
            if not db_path.exists():
                continue

            try:
                conn = self._init_memory_db(db_path)
                cursor = conn.execute(
                    """
                    SELECT m.*, f.rank,
                           snippet(memories_fts, 0, '<mark>', '</mark>', '...', 64) as snippet
                    FROM memories_fts f
                    JOIN memories m ON m.id = f.rowid  
                    WHERE memories_fts MATCH ?
                    ORDER BY f.rank
                    LIMIT ?
                """,
                    (query, limit),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row["id"],
                            "content": row["content"],
                            "snippet": row["snippet"],
                            "category": row["category"],
                            "importance": row["importance"],
                            "metadata": (
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            "scope": scope_name,
                            "score": -row["rank"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                        }
                    )

                conn.close()
            except Exception as e:
                print(f"Warning: Memory search failed for {scope_name}: {e}")

        return results

    # Vector operations (requires sqlite-vec extension)
    def generate_embedding(
        self, text: str, model: str = "bge-small-en-v1.5"
    ) -> Optional[List[float]]:
        """Generate embedding for text. Returns None if embedding model unavailable."""
        # Requires: pip install fastembed
        try:
            from fastembed import TextEmbedding

            embedding_model = TextEmbedding(model_name=model)
            embeddings = list(embedding_model.embed([text]))
            return embeddings[0].tolist() if embeddings else None
        except ImportError:
            return None  # fastembed not installed

    def add_embedding(
        self,
        source_table: str,
        source_id: int,
        embedding: List[float],
        model: str = "bge-small-en-v1.5",
        scope: str = "project",
        project_path: str = None,
    ) -> bool:
        """Add vector embedding to database."""
        if scope == "global":
            db_path = self._get_global_db_path()
        else:
            if not project_path:
                project_path = os.getcwd()
            db_path = self._get_project_db_path(project_path)

        try:
            conn = self._init_memory_db(db_path)

            # Check if sqlite-vec is available
            cursor = conn.execute("SELECT name FROM pragma_table_info('vec_index')")
            if not cursor.fetchall():
                conn.close()
                return False

            # Store embedding
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings 
                (source_table, source_id, embedding, model)
                VALUES (?, ?, ?, ?)
            """,
                (source_table, source_id, json.dumps(embedding), model),
            )

            # Add to vector index
            conn.execute(
                """
                INSERT INTO vec_index (embedding) VALUES (?)
            """,
                (json.dumps(embedding),),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Warning: Vector embedding failed: {e}")
            return False

    def vector_search(
        self,
        query_embedding: List[float],
        scope: str = "both",
        project_path: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search using vector similarity. Requires sqlite-vec extension."""
        results = []
        dbs = []
        if scope in ("global", "both"):
            dbs.append(("global", self._get_global_db_path()))
        if scope in ("project", "both"):
            if not project_path:
                project_path = os.getcwd()
            dbs.append(("project", self._get_project_db_path(project_path)))

        for scope_name, db_path in dbs:
            if not db_path.exists():
                continue
            try:
                conn = self._init_memory_db(db_path)
                # Check if vec_index exists (sqlite-vec installed)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_index'"
                )
                if not cursor.fetchone():
                    conn.close()
                    continue

                # Vector similarity search using sqlite-vec
                cursor = conn.execute(
                    """
                    SELECT e.source_table, e.source_id, vec_distance(v.embedding, ?) as distance
                    FROM vec_index v
                    JOIN embeddings e ON e.id = v.rowid
                    ORDER BY distance ASC
                    LIMIT ?
                """,
                    (json.dumps(query_embedding), limit),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "source_table": row["source_table"],
                            "source_id": row["source_id"],
                            "distance": row["distance"],
                            "scope": scope_name,
                        }
                    )
                conn.close()
            except Exception as e:
                print(f"Warning: Vector search failed for {scope_name}: {e}")

        return sorted(results, key=lambda x: x.get("distance", float("inf")))[:limit]

    # Utility methods
    def get_memory_stats(
        self, scope: str = "both", project_path: str = None
    ) -> Dict[str, Any]:
        """Get memory system statistics."""
        stats = {
            "markdown_files": {"global": 0, "project": 0},
            "structured_memories": {"global": 0, "project": 0},
            "vector_embeddings": {"global": 0, "project": 0},
            "total_size_bytes": 0,
        }

        # Count markdown files
        if scope in ("global", "both"):
            global_files = list(self.global_memory_dir.rglob("*.md"))
            stats["markdown_files"]["global"] = len(global_files)
            stats["total_size_bytes"] += sum(f.stat().st_size for f in global_files)

        if scope in ("project", "both") and project_path:
            memory_dir = self._get_project_memory_dir(project_path)
            if memory_dir.exists():
                project_files = list(memory_dir.rglob("*.md"))
                stats["markdown_files"]["project"] = len(project_files)
                stats["total_size_bytes"] += sum(
                    f.stat().st_size for f in project_files
                )

        # Count database records
        dbs = []
        if scope in ("global", "both"):
            dbs.append(("global", self._get_global_db_path()))
        if scope in ("project", "both") and project_path:
            dbs.append(("project", self._get_project_db_path(project_path)))

        for scope_name, db_path in dbs:
            if not db_path.exists():
                continue

            try:
                conn = self._init_memory_db(db_path)

                # Count memories
                cursor = conn.execute("SELECT COUNT(*) FROM memories")
                stats["structured_memories"][scope_name] = cursor.fetchone()[0]

                # Count embeddings
                try:
                    cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                    stats["vector_embeddings"][scope_name] = cursor.fetchone()[0]
                except sqlite3.Error:
                    stats["vector_embeddings"][scope_name] = 0

                # Add DB file size
                stats["total_size_bytes"] += db_path.stat().st_size

                conn.close()
            except Exception as e:
                print(f"Warning: Failed to get stats for {scope_name}: {e}")

        return stats
