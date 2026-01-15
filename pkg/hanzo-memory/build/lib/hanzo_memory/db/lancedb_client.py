"""LanceDB client for vector storage and search."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import Field
from structlog import get_logger

from ..config import settings
from ..models.knowledge import Fact, FactCreate, KnowledgeBase
from ..models.memory import Memory, MemoryCreate, MemoryResponse
from ..models.project import Project, ProjectCreate
from .base import BaseVectorDB
from .markdown_reader import MarkdownMemoryReader

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
    memory_type: str = Field(default="knowledge", description="Type of memory")
    context: str = Field(default="{}", description="JSON context")
    source: str = Field(default="", description="Source of memory")
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


class LanceDBClient(BaseVectorDB):
    """Client for LanceDB operations with markdown support."""

    def __init__(self, db_path: str | None = None, enable_markdown: bool = True):
        """Initialize LanceDB client with optional markdown support.

        Args:
            db_path: Path to LanceDB directory
            enable_markdown: Whether to enable markdown file integration
        """
        self.db_path = db_path or str(settings.lancedb_path.absolute())
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(self.db_path)
        self._ensure_tables()

        # Initialize markdown reader if enabled
        self.enable_markdown = enable_markdown
        self.markdown_reader = MarkdownMemoryReader() if enable_markdown else None

        # Import markdown memories on initialization
        if self.enable_markdown:
            self._import_markdown_memories()

        logger.info(f"Initialized LanceDB storage at {self.db_path}")

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
        metadata: dict | None = None,
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

    def get_user_projects_sync(self, user_id: str) -> list[dict[str, Any]]:
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

    def add_memory_sync(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
        importance: float = 0.5,
        memory_type: str = "knowledge",
        context: dict | None = None,
        source: str = "",
    ) -> dict[str, Any]:
        """Add a memory to the database (sync version)."""
        table = self._get_memory_table(user_id)

        now = datetime.now(timezone.utc).isoformat()
        memory_data = {
            "memory_id": memory_id,
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "importance": importance,
            "memory_type": memory_type,
            "context": json.dumps(context or {}),
            "source": source,
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
        project_id: str | None = None,
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
        metadata: dict | None = None,
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

    def add_fact_sync(
        self,
        fact_id: str,
        knowledge_base_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
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

    def search_facts_sync(
        self,
        knowledge_base_id: str,
        query_embedding: list[float] | None = None,
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
    def create_chat_session_sync(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new chat session (sync version)."""
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

    def add_chat_message_sync(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Add a message to a chat session (sync version)."""
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

    def get_chat_messages_sync(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get messages from a chat session (sync version)."""
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

    async def close(self) -> None:
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

    # Async wrappers for BaseVectorDB interface
    async def initialize(self) -> None:
        """Initialize the database (already done in __init__)."""
        logger.info("LanceDB initialized")

    async def create_memory(
        self, memory: MemoryCreate, project_id: str, user_id: Optional[str] = None
    ) -> Memory:
        """Create a new memory."""
        memory_id = str(uuid.uuid4())
        user_id = user_id or "default"

        # Add memory to LanceDB
        memory_data = self.add_memory_sync(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=memory.content,
            embedding=memory.embedding or [0.0] * settings.embedding_dimensions,
            metadata=memory.metadata or {},
            importance=memory.importance,
            memory_type=memory.memory_type or "knowledge",
            context=memory.context or {},
            source=memory.source or "",
        )

        # Convert to Memory model
        return Memory(
            id=memory_id,
            memory_id=memory_id,
            project_id=project_id,
            user_id=user_id,
            content=memory.content,
            memory_type=memory.memory_type or "knowledge",
            importance=memory.importance,
            context=memory.context or {},
            metadata=memory.metadata or {},
            source=memory.source or "",
            timestamp=memory_data["created_at"],
            created_at=memory_data["created_at"],
            updated_at=memory_data["updated_at"],
        )

    async def search_memories(
        self,
        query_embedding: List[float],
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[MemoryResponse]:
        """Search for similar memories."""
        user_id = user_id or "default"

        # Search in LanceDB
        results = self.search_memories_wrapper(
            user_id=user_id,
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            min_similarity=min_importance,
        )

        # Convert to MemoryResponse
        responses = []
        for result in results:
            # Parse context if it's a string
            context = result.get("context", {})
            if isinstance(context, str):
                context = json.loads(context)

            # Parse metadata if it's a string
            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            memory = Memory(
                id=result["memory_id"],
                memory_id=result["memory_id"],
                project_id=result["project_id"],
                user_id=result["user_id"],
                content=result["content"],
                memory_type=result.get("memory_type", "knowledge"),
                importance=result["importance"],
                context=context,
                metadata=metadata,
                source=result.get("source", ""),
                timestamp=result["created_at"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
            responses.append(
                MemoryResponse(
                    memory=memory,
                    similarity=result.get("_distance", 0.0),
                    relevance_score=result.get("_distance", 0.0),
                )
            )

        return responses

    async def get_recent_memories(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[Memory]:
        """Get recent memories."""
        user_id = user_id or "default"

        # Get memories from the user's table
        table = self._get_memory_table(user_id)

        # Query for recent memories
        query = table.search().limit(limit * 2)  # Get more to filter later
        if project_id:
            query = query.where(f"project_id = '{project_id}'")
        if memory_type:
            query = query.where(f"memory_type = '{memory_type}'")

        results = query.to_list()

        # Filter by project and type
        memories = []
        for result in results:
            if result["project_id"] != project_id:
                continue
            if memory_type and result.get("memory_type") != memory_type:
                continue

            # Parse context if it's a string
            context = result.get("context", {})
            if isinstance(context, str):
                context = json.loads(context)

            # Parse metadata if it's a string
            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            memory = Memory(
                id=result["memory_id"],
                memory_id=result["memory_id"],
                project_id=result["project_id"],
                user_id=result["user_id"],
                content=result["content"],
                memory_type=result.get("memory_type", "knowledge"),
                importance=result["importance"],
                context=context,
                metadata=metadata,
                source=result.get("source", ""),
                timestamp=result["created_at"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
            memories.append(memory)

        return memories[:limit]

    async def delete_memory(self, memory_id: str, project_id: str) -> bool:
        """Delete a memory."""
        # LanceDB doesn't have direct delete by ID, so we need to rebuild the table
        # This is a limitation we'll need to work around
        logger.warning("Memory deletion not fully implemented for LanceDB")
        return False

    async def create_fact(
        self, fact: FactCreate, project_id: str, user_id: Optional[str] = None
    ) -> Fact:
        """Create a new fact."""
        fact_id = str(uuid.uuid4())
        knowledge_base_id = project_id  # Use project_id as knowledge base ID

        fact_data = self.add_fact_sync(
            fact_id=fact_id,
            knowledge_base_id=knowledge_base_id,
            content=f"{fact.subject} {fact.predicate} {fact.object}",
            embedding=fact.embedding or [0.0] * settings.embedding_dimensions,
            metadata=fact.metadata or {},
            confidence=fact.confidence,
        )

        return Fact(
            id=fact_id,
            project_id=project_id,
            user_id=user_id or "default",
            subject=fact.subject,
            predicate=fact.predicate,
            object=fact.object,
            confidence=fact.confidence,
            source=fact.source,
            metadata=fact.metadata or {},
            created_at=fact_data["created_at"],
            updated_at=fact_data["updated_at"],
        )

    async def search_facts(
        self,
        query_embedding: List[float],
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.0,
    ) -> List[Fact]:
        """Search for similar facts."""
        knowledge_base_id = project_id
        results = self.search_facts_wrapper(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            limit=limit,
            min_similarity=min_confidence,
        )

        facts = []
        for result in results:
            # Parse fact content back into triple
            parts = result["content"].split(" ", 2)
            subject = parts[0] if len(parts) > 0 else ""
            predicate = parts[1] if len(parts) > 1 else ""
            obj = parts[2] if len(parts) > 2 else ""

            fact = Fact(
                id=result["fact_id"],
                project_id=project_id,
                user_id=user_id or "default",
                subject=subject,
                predicate=predicate,
                object=obj,
                confidence=result["confidence"],
                source="",
                metadata=result["metadata"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
            facts.append(fact)

        return facts

    async def get_knowledge_graph(
        self, project_id: str, user_id: Optional[str] = None
    ) -> KnowledgeBase:
        """Get the knowledge graph."""
        facts = await self.search_facts(
            query_embedding=[0.0] * settings.embedding_dimensions,
            project_id=project_id,
            user_id=user_id,
            limit=1000,
        )

        entities = set()
        relations = set()

        for fact in facts:
            entities.add(fact.subject)
            entities.add(fact.object)
            relations.add(fact.predicate)

        return KnowledgeBase(
            facts=facts,
            entities=list(entities),
            relations=list(relations),
            metadata={
                "fact_count": len(facts),
                "entity_count": len(entities),
                "relation_count": len(relations),
            },
        )

    async def create_project(
        self, project: ProjectCreate, user_id: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        user_id = user_id or "default"

        project_data = self.create_project_sync(
            project_id=project_id,
            user_id=user_id,
            name=project.name,
            description=project.description,
            metadata=project.metadata or {},
        )

        return Project(
            project_id=project_id,
            name=project.name,
            description=project.description,
            user_id=user_id,
            metadata=project.metadata or {},
            created_at=project_data["created_at"],
            updated_at=project_data["updated_at"],
        )

    async def get_project(
        self, project_id: str, user_id: Optional[str] = None
    ) -> Optional[Project]:
        """Get a project by ID."""
        user_id = user_id or "default"
        projects = self.get_user_projects(user_id)

        for p in projects:
            if p["project_id"] == project_id:
                return Project(
                    project_id=p["project_id"],
                    name=p["name"],
                    description=p["description"],
                    user_id=user_id,
                    metadata=p["metadata"],
                    created_at=p["created_at"],
                    updated_at=p["updated_at"],
                )
        return None

    async def list_projects(self, user_id: Optional[str] = None) -> List[Project]:
        """List all projects."""
        user_id = user_id or "default"
        projects_data = self.get_user_projects_sync(user_id)

        projects = []
        for p in projects_data:
            projects.append(
                Project(
                    project_id=p["project_id"],
                    name=p["name"],
                    description=p["description"],
                    user_id=user_id,
                    metadata=p["metadata"],
                    created_at=p["created_at"],
                    updated_at=p["updated_at"],
                )
            )

        # Add markdown project if it exists
        if self.enable_markdown:
            projects.append(
                Project(
                    project_id="markdown_import",
                    name="Markdown Import",
                    description="Automatically imported memories from markdown files",
                    user_id="system",
                    metadata={"auto_created": True},
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
            )

        return projects

    async def delete_project(
        self, project_id: str, user_id: Optional[str] = None
    ) -> bool:
        """Delete a project and all associated data."""
        # Not fully implemented for LanceDB
        logger.warning("Project deletion not fully implemented for LanceDB")
        return False

    # Sync method wrappers (these call the original non-async versions)
    def search_memories_wrapper(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: str | None = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Wrapper for the original search_memories method."""
        # This is the original sync method from line 261
        table = self._get_memory_table(user_id)

        # Build the search query
        search_query = table.search(query_embedding).limit(limit)

        # Add project filter if specified
        if project_id:
            search_query = search_query.where(f"project_id = '{project_id}'")

        # Execute search
        results = search_query.to_list()

        # Parse JSON metadata
        for result in results:
            result["metadata"] = json.loads(result["metadata"])
            result["context"] = json.loads(result.get("context", "{}"))

        return results

    def search_facts_wrapper(
        self,
        knowledge_base_id: str,
        query_embedding: list[float],
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Wrapper for search_facts_sync."""
        # Call the sync version
        return self.search_facts_sync(knowledge_base_id, query_embedding, limit, min_similarity)

    def create_project_sync(
        self,
        project_id: str,
        user_id: str,
        name: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Synchronous version of create_project (the original non-async version)."""
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

    def _import_markdown_memories(self):
        """Import memories from markdown files."""
        if not self.markdown_reader:
            return

        try:
            # Read markdown memories
            markdown_memories = self.markdown_reader.read_markdown_memories()

            # Create markdown table if not exists
            table_name = "memories_markdown"
            if table_name not in self.db.table_names():
                self.db.create_table(table_name, schema=MemoryModel)

            table = self.db.open_table(table_name)

            # Import each memory
            imported_count = 0
            for memory_create in markdown_memories:
                memory_id = str(uuid.uuid4())

                memory_data = {
                    "memory_id": memory_id,
                    "user_id": "system",
                    "project_id": "markdown_import",
                    "content": memory_create.content,
                    "metadata": json.dumps(memory_create.metadata or {}),
                    "importance": memory_create.importance,
                    "memory_type": memory_create.memory_type or "knowledge",
                    "context": json.dumps(memory_create.context or {}),
                    "source": memory_create.source or "",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "embedding": [0.0] * settings.embedding_dimensions,  # Placeholder
                }

                table.add([memory_data])
                imported_count += 1

            if imported_count > 0:
                logger.info(f"Imported {imported_count} memories from markdown files")

        except Exception as e:
            logger.error(f"Error importing markdown memories: {e}")

    # Additional abstract methods
    async def add_memory(self, memory: MemoryCreate, project_id: str) -> Memory:
        """Add a memory (alias for create_memory)."""
        return await self.create_memory(memory, project_id)

    async def add_fact(self, fact: FactCreate, project_id: str) -> Fact:
        """Add a fact (alias for create_fact)."""
        return await self.create_fact(fact, project_id)

    async def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact by ID."""
        logger.warning("Fact deletion not fully implemented for LanceDB")
        return False

    async def create_knowledge_base(self, name: str, description: str, project_id: str) -> KnowledgeBase:
        """Create a knowledge base."""
        return await self.get_knowledge_graph(project_id)

    async def get_knowledge_bases(self, project_id: str) -> List[KnowledgeBase]:
        """Get all knowledge bases for a project."""
        return [await self.get_knowledge_graph(project_id)]

    async def create_chat_session(self, project_id: str, user_id: Optional[str] = None) -> str:
        """Create a new chat session (async wrapper)."""
        session_id = str(uuid.uuid4())
        # Call the sync version with different signature
        self.create_chat_session_sync(
            session_id=session_id,
            user_id=user_id or "default",
            project_id=project_id,
            metadata={},
        )
        return session_id

    async def add_chat_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a chat session (async wrapper)."""
        message_id = str(uuid.uuid4())
        # Call the sync version with different signature
        self.add_chat_message_sync(
            message_id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            embedding=[0.0] * settings.embedding_dimensions,
            metadata={},
        )

    async def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get messages from a chat session (async wrapper)."""
        # Call the sync version
        return self.get_chat_messages_sync(session_id)

    async def search_chat_messages(self, query: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search chat messages."""
        # Simple text search - not implemented for LanceDB yet
        return []

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
        table = self._get_memory_table(user_id)

        # Find the memory to update
        results = table.search().where(f"memory_id = '{memory_id}' AND project_id = '{project_id}'").to_list()

        if not results:
            return None

        # Get the existing memory
        existing_memory = results[0]

        # Prepare update values
        update_values = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        if content is not None:
            update_values["content"] = content
        if metadata is not None:
            update_values["metadata"] = json.dumps(metadata)
        if importance is not None:
            update_values["importance"] = importance

        # For LanceDB, we need to delete the old record and insert the updated one
        # This is because LanceDB doesn't have a direct update mechanism in older versions
        # In newer versions, we can use merge_insert
        try:
            # Get all records except the one to update
            all_records = table.search().to_list()
            updated_records = []

            for record in all_records:
                if record["memory_id"] == memory_id:
                    # Update this record
                    updated_record = record.copy()
                    updated_record.update(update_values)
                    updated_records.append(updated_record)
                else:
                    updated_records.append(record)

            # Drop and recreate the table with updated records
            table_name = f"memories_{user_id}"
            self.db.drop_table(table_name)
            self.db.create_table(table_name, schema=MemoryModel)

            if updated_records:
                table = self.db.open_table(table_name)
                table.add(updated_records)

            return updated_records[0]  # Return the updated memory
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return None

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user."""
        return await self.list_projects(user_id)



# Singleton instance
_lancedb_client: LanceDBClient | None = None


def get_lancedb_client() -> LanceDBClient:
    """Get or create the global LanceDB client."""
    global _lancedb_client
    if _lancedb_client is None:
        _lancedb_client = LanceDBClient(enable_markdown=True)
    return _lancedb_client
