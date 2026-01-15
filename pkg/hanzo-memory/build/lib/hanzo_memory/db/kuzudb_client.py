"""KuzuDB client for graph-based memory storage."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from structlog import get_logger

from ..config import settings
from ..models.memory import Memory, MemoryCreate, MemoryResponse
from ..models.project import Project, ProjectCreate
from ..models.fact import Fact, FactCreate
from .base import BaseVectorDB

logger = get_logger()

try:
    import kuzu
    KUZU_AVAILABLE = True
except ImportError:
    KUZU_AVAILABLE = False
    logger.warning("KuzuDB not available. Install with: pip install kuzu")


class KuzuDBClient(BaseVectorDB):
    """KuzuDB implementation for graph-based memory storage."""

    def __init__(self, db_path: Optional[str] = None, enable_markdown: bool = True):
        """Initialize KuzuDB client.

        Args:
            db_path: Path to KuzuDB database directory
            enable_markdown: Whether to import markdown files
        """
        if not KUZU_AVAILABLE:
            raise ImportError("KuzuDB not installed. Install with: pip install kuzu")

        self.db_path = Path(db_path or settings.db_path) / "kuzudb"
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize KuzuDB database
        self.db = kuzu.Database(str(self.db_path))
        self.conn = kuzu.Connection(self.db)

        # Initialize schema
        self._init_schema()

        # Import markdown if enabled
        self.enable_markdown = enable_markdown
        if enable_markdown:
            from ..markdown_memory import MarkdownMemoryReader
            self.markdown_reader = MarkdownMemoryReader()
            self._import_markdown_memories()

        logger.info(f"Initialized KuzuDB storage at {self.db_path}")

    def _init_schema(self):
        """Initialize KuzuDB schema with nodes and relationships."""
        # Create node tables
        queries = [
            # User node
            """CREATE NODE TABLE IF NOT EXISTS User(
                user_id STRING PRIMARY KEY,
                name STRING,
                created_at TIMESTAMP
            )""",

            # Project node
            """CREATE NODE TABLE IF NOT EXISTS Project(
                project_id STRING PRIMARY KEY,
                name STRING,
                description STRING,
                metadata STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )""",

            # Memory node
            """CREATE NODE TABLE IF NOT EXISTS Memory(
                memory_id STRING PRIMARY KEY,
                content STRING,
                memory_type STRING,
                importance DOUBLE,
                context STRING,
                metadata STRING,
                source STRING,
                embedding DOUBLE[],
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )""",

            # Fact node
            """CREATE NODE TABLE IF NOT EXISTS Fact(
                fact_id STRING PRIMARY KEY,
                statement STRING,
                confidence DOUBLE,
                source STRING,
                metadata STRING,
                embedding DOUBLE[],
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )""",

            # KnowledgeBase node
            """CREATE NODE TABLE IF NOT EXISTS KnowledgeBase(
                kb_id STRING PRIMARY KEY,
                name STRING,
                description STRING,
                metadata STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )""",

            # Create relationship tables
            """CREATE REL TABLE IF NOT EXISTS OWNS(
                FROM User TO Project
            )""",

            """CREATE REL TABLE IF NOT EXISTS HAS_MEMORY(
                FROM Project TO Memory,
                user_id STRING
            )""",

            """CREATE REL TABLE IF NOT EXISTS HAS_FACT(
                FROM Project TO Fact,
                user_id STRING
            )""",

            """CREATE REL TABLE IF NOT EXISTS IN_KB(
                FROM Memory TO KnowledgeBase
            )""",

            """CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                FROM Memory TO Memory,
                relationship_type STRING,
                strength DOUBLE
            )""",

            """CREATE REL TABLE IF NOT EXISTS DERIVED_FROM(
                FROM Fact TO Memory
            )""",
        ]

        for query in queries:
            try:
                self.conn.execute(query)
            except Exception as e:
                # Table might already exist
                logger.debug(f"Schema creation note: {e}")

    async def initialize(self) -> None:
        """Initialize the database."""
        logger.info("KuzuDB initialized")

    async def close(self) -> None:
        """Close database connection."""
        if hasattr(self, 'conn'):
            # KuzuDB doesn't have explicit close, but we can clean up
            self.conn = None
        logger.info("Closing KuzuDB connection")

    def create_project_sync(self, project: ProjectCreate, user_id: str) -> dict:
        """Create a project synchronously."""
        project_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Create project node
        self.conn.execute(
            """MERGE (p:Project {project_id: $pid})
            SET p.name = $name,
                p.description = $desc,
                p.metadata = $metadata,
                p.created_at = $created,
                p.updated_at = $updated
            """,
            {
                "pid": project_id,
                "name": project.name,
                "desc": project.description,
                "metadata": json.dumps(project.metadata or {}),
                "created": now,
                "updated": now,
            }
        )

        # Create or connect user
        self.conn.execute(
            """MERGE (u:User {user_id: $uid})
            ON CREATE SET u.created_at = $created
            """,
            {"uid": user_id, "created": now}
        )

        # Create ownership relationship
        self.conn.execute(
            """MATCH (u:User {user_id: $uid}), (p:Project {project_id: $pid})
            MERGE (u)-[:OWNS]->(p)
            """,
            {"uid": user_id, "pid": project_id}
        )

        return {
            "project_id": project_id,
            "name": project.name,
            "description": project.description,
            "user_id": user_id,
            "metadata": project.metadata or {},
            "created_at": now,
            "updated_at": now,
        }

    async def create_project(self, project: ProjectCreate, user_id: str) -> Project:
        """Create a project."""
        project_data = self.create_project_sync(project, user_id)
        return Project(**project_data)

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
        """Add a memory to the graph."""
        now = datetime.now(timezone.utc).isoformat()

        # Create memory node
        self.conn.execute(
            """MERGE (m:Memory {memory_id: $mid})
            SET m.content = $content,
                m.memory_type = $mtype,
                m.importance = $importance,
                m.context = $context,
                m.metadata = $metadata,
                m.source = $source,
                m.embedding = $embedding,
                m.created_at = $created,
                m.updated_at = $updated
            """,
            {
                "mid": memory_id,
                "content": content,
                "mtype": metadata.get("memory_type", "general") if metadata else "general",
                "importance": importance,
                "context": json.dumps(metadata.get("context", {}) if metadata else {}),
                "metadata": json.dumps(metadata or {}),
                "source": metadata.get("source", "") if metadata else "",
                "embedding": embedding,
                "created": now,
                "updated": now,
            }
        )

        # Connect to project
        self.conn.execute(
            """MATCH (p:Project {project_id: $pid}), (m:Memory {memory_id: $mid})
            MERGE (p)-[:HAS_MEMORY {user_id: $uid}]->(m)
            """,
            {"pid": project_id, "mid": memory_id, "uid": user_id}
        )

        # Find and create relationships to related memories
        if embedding:
            self._create_memory_relationships(memory_id, embedding, project_id)

        return {
            "memory_id": memory_id,
            "project_id": project_id,
            "user_id": user_id,
            "content": content,
            "metadata": metadata or {},
            "importance": importance,
            "created_at": now,
            "updated_at": now,
        }

    def _create_memory_relationships(self, memory_id: str, embedding: list[float], project_id: str):
        """Create relationships between related memories based on similarity."""
        # Find similar memories in the same project
        results = self.conn.execute(
            """MATCH (p:Project {project_id: $pid})-[:HAS_MEMORY]->(m:Memory)
            WHERE m.memory_id <> $mid AND m.embedding IS NOT NULL
            RETURN m.memory_id, m.embedding
            LIMIT 10
            """,
            {"pid": project_id, "mid": memory_id}
        )

        query_vec = np.array(embedding)
        for row in results:
            other_id = row[0]
            other_embedding = row[1]
            if other_embedding:
                similarity = self._compute_similarity(query_vec, np.array(other_embedding))
                if similarity > 0.7:  # Only create strong relationships
                    self.conn.execute(
                        """MATCH (m1:Memory {memory_id: $mid1}), (m2:Memory {memory_id: $mid2})
                        MERGE (m1)-[:RELATES_TO {relationship_type: 'similar', strength: $strength}]->(m2)
                        """,
                        {"mid1": memory_id, "mid2": other_id, "strength": similarity}
                    )

    def _compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def search_memories(
        self,
        query_embedding: List[float],
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> Any:
        """Search memories using graph traversal and vector similarity."""
        import pandas as pd

        # Build the query
        where_clause = []
        params = {"uid": user_id, "limit": limit}

        if project_id:
            where_clause.append("p.project_id = $pid")
            params["pid"] = project_id

        if memory_type:
            where_clause.append("m.memory_type = $mtype")
            params["mtype"] = memory_type

        where = " AND ".join(where_clause) if where_clause else "1=1"

        # Query memories
        query = f"""
            MATCH (u:User {{user_id: $uid}})-[:OWNS]->(p:Project)-[:HAS_MEMORY]->(m:Memory)
            WHERE {where}
            RETURN m.memory_id, m.content, m.memory_type, m.importance,
                   m.context, m.metadata, m.source, m.embedding,
                   m.created_at, m.updated_at, p.project_id, $uid as user_id
            LIMIT $limit
        """

        results = self.conn.execute(query, params)

        # Calculate similarities and build dataframe
        data = []
        query_vec = np.array(query_embedding) if query_embedding else None

        for row in results:
            similarity = 0.0
            if query_vec is not None and row[7]:  # embedding
                similarity = self._compute_similarity(query_vec, np.array(row[7]))

            data.append({
                "memory_id": row[0],
                "content": row[1],
                "memory_type": row[2],
                "importance": row[3],
                "context": row[4],
                "metadata": row[5],
                "source": row[6],
                "created_at": row[8],
                "updated_at": row[9],
                "project_id": row[10],
                "user_id": row[11],
                "similarity_score": similarity,
            })

        # Sort by similarity if we have embeddings
        if query_embedding:
            data.sort(key=lambda x: x["similarity_score"], reverse=True)

        return pd.DataFrame(data[:limit])

    async def search_memories_async(
        self,
        query_embedding: List[float],
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[Memory]:
        """Async wrapper for search_memories."""
        df = self.search_memories(query_embedding, user_id or "default", project_id, limit, memory_type)

        memories = []
        for _, row in df.iterrows():
            memories.append(Memory(
                memory_id=row.get("memory_id"),
                project_id=row.get("project_id"),
                user_id=row.get("user_id"),
                content=row.get("content"),
                memory_type=row.get("memory_type"),
                importance=row.get("importance", 0.5),
                context=json.loads(row.get("context", "{}")) if isinstance(row.get("context"), str) else row.get("context", {}),
                metadata=json.loads(row.get("metadata", "{}")) if isinstance(row.get("metadata"), str) else row.get("metadata", {}),
                source=row.get("source"),
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            ))
        return memories

    async def create_memory(
        self, memory: MemoryCreate, project_id: str, user_id: Optional[str] = None
    ) -> Memory:
        """Create a memory."""
        memory_id = str(uuid.uuid4())
        user_id = user_id or "default"

        memory_data = self.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=memory.content,
            embedding=memory.embedding or [0.0] * settings.embedding_dimensions,
            metadata={
                "memory_type": memory.memory_type,
                "context": memory.context or {},
                "source": memory.source,
                **(memory.metadata or {})
            },
            importance=memory.importance,
        )

        return Memory(**memory_data)

    async def get_recent_memories(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[Memory]:
        """Get recent memories from the graph."""
        user_id = user_id or "default"

        where_clause = ["p.project_id = $pid"]
        params = {"pid": project_id, "uid": user_id, "limit": limit}

        if memory_type:
            where_clause.append("m.memory_type = $mtype")
            params["mtype"] = memory_type

        where = " AND ".join(where_clause)

        query = f"""
            MATCH (u:User {{user_id: $uid}})-[:OWNS]->(p:Project)-[:HAS_MEMORY]->(m:Memory)
            WHERE {where}
            RETURN m.memory_id, m.content, m.memory_type, m.importance,
                   m.context, m.metadata, m.source,
                   m.created_at, m.updated_at
            ORDER BY m.created_at DESC
            LIMIT $limit
        """

        results = self.conn.execute(query, params)

        memories = []
        for row in results:
            memories.append(Memory(
                memory_id=row[0],
                project_id=project_id,
                user_id=user_id,
                content=row[1],
                memory_type=row[2],
                importance=row[3],
                context=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                metadata=json.loads(row[5]) if isinstance(row[5], str) else row[5],
                source=row[6],
                created_at=row[7],
                updated_at=row[8],
            ))

        return memories

    async def list_projects(self, user_id: Optional[str] = None) -> List[Project]:
        """List all projects for a user."""
        user_id = user_id or "default"

        results = self.conn.execute(
            """MATCH (u:User {user_id: $uid})-[:OWNS]->(p:Project)
            RETURN p.project_id, p.name, p.description, p.metadata,
                   p.created_at, p.updated_at
            """,
            {"uid": user_id}
        )

        projects = []
        for row in results:
            projects.append(Project(
                project_id=row[0],
                name=row[1],
                description=row[2],
                user_id=user_id,
                metadata=json.loads(row[3]) if isinstance(row[3], str) else row[3],
                created_at=row[4],
                updated_at=row[5],
            ))

        return projects

    def create_memories_table(self, user_id: str) -> None:
        """Create memories table (no-op for KuzuDB as schema is predefined)."""
        pass

    def _import_markdown_memories(self):
        """Import memories from markdown files."""
        if not self.markdown_reader:
            return

        memories = self.markdown_reader.read_all_memories()
        imported_count = 0

        # Create a special project for markdown imports
        project_id = "markdown_import"
        self.conn.execute(
            """MERGE (p:Project {project_id: $pid})
            SET p.name = $name,
                p.description = $desc,
                p.created_at = $created,
                p.updated_at = $updated
            """,
            {
                "pid": project_id,
                "name": "Markdown Import",
                "desc": "Memories imported from markdown files",
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        )

        for memory_create in memories:
            memory_id = str(uuid.uuid4())
            self.add_memory(
                memory_id=memory_id,
                user_id="system",
                project_id=project_id,
                content=memory_create.content,
                embedding=[0.0] * settings.embedding_dimensions,
                metadata={
                    "memory_type": memory_create.memory_type or "knowledge",
                    "context": memory_create.context or {},
                    "source": memory_create.source,
                    **(memory_create.metadata or {})
                },
                importance=memory_create.importance,
            )
            imported_count += 1

        if imported_count > 0:
            logger.info(f"Imported {imported_count} memories from markdown files to KuzuDB")

    # Additional methods for graph-specific operations
    def get_related_memories(self, memory_id: str, relationship_type: Optional[str] = None) -> List[Dict]:
        """Get memories related to a specific memory through graph relationships."""
        where = ""
        params = {"mid": memory_id}

        if relationship_type:
            where = "{relationship_type: $rtype}"
            params["rtype"] = relationship_type

        query = f"""
            MATCH (m1:Memory {{memory_id: $mid}})-[r:RELATES_TO {where}]->(m2:Memory)
            RETURN m2.memory_id, m2.content, r.relationship_type, r.strength
            ORDER BY r.strength DESC
        """

        results = self.conn.execute(query, params)

        related = []
        for row in results:
            related.append({
                "memory_id": row[0],
                "content": row[1],
                "relationship_type": row[2],
                "strength": row[3],
            })

        return related

    def get_memory_graph(self, project_id: str, depth: int = 2) -> Dict:
        """Get a subgraph of memories and their relationships."""
        # Get nodes
        nodes_query = """
            MATCH (p:Project {project_id: $pid})-[:HAS_MEMORY]->(m:Memory)
            RETURN m.memory_id, m.content, m.memory_type, m.importance
            LIMIT 100
        """

        nodes_results = self.conn.execute(nodes_query, {"pid": project_id})

        nodes = []
        node_ids = set()
        for row in nodes_results:
            nodes.append({
                "id": row[0],
                "content": row[1],
                "type": row[2],
                "importance": row[3],
            })
            node_ids.add(row[0])

        # Get edges
        edges_query = """
            MATCH (m1:Memory)-[r:RELATES_TO]->(m2:Memory)
            WHERE m1.memory_id IN $ids AND m2.memory_id IN $ids
            RETURN m1.memory_id, m2.memory_id, r.relationship_type, r.strength
        """

        edges_results = self.conn.execute(edges_query, {"ids": list(node_ids)})

        edges = []
        for row in edges_results:
            edges.append({
                "source": row[0],
                "target": row[1],
                "type": row[2],
                "strength": row[3],
            })

        return {
            "nodes": nodes,
            "edges": edges,
        }