"""Local file-based memory storage implementation."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from structlog import get_logger

from ..models.knowledge import Fact, FactCreate, KnowledgeBase
from ..models.memory import Memory, MemoryCreate, MemoryResponse
from ..models.project import Project, ProjectCreate
from .base import BaseVectorDB
from .markdown_reader import MarkdownMemoryReader

logger = get_logger()


class LocalMemoryClient(BaseVectorDB):
    """Local file-based implementation of the vector database."""

    def __init__(self, storage_dir: Optional[Path] = None, enable_markdown: bool = True):
        """Initialize local memory storage.

        Args:
            storage_dir: Directory to store memory files
            enable_markdown: Whether to enable markdown file integration
        """
        self.storage_dir = storage_dir or Path.home() / ".hanzo" / "memory"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # File paths for different collections
        self.memories_file = self.storage_dir / "memories.json"
        self.facts_file = self.storage_dir / "facts.json"
        self.projects_file = self.storage_dir / "projects.json"
        self.embeddings_file = self.storage_dir / "embeddings.npz"
        self.markdown_index_file = self.storage_dir / "markdown_index.json"

        # Load existing data
        self.memories = self._load_json(self.memories_file)
        self.facts = self._load_json(self.facts_file)
        self.projects = self._load_json(self.projects_file)
        self.embeddings = self._load_embeddings()
        self.markdown_index = self._load_json(self.markdown_index_file)

        # Initialize markdown reader if enabled
        self.enable_markdown = enable_markdown
        self.markdown_reader = MarkdownMemoryReader() if enable_markdown else None

        # Import markdown memories on initialization
        if self.enable_markdown:
            self._import_markdown_memories()

        logger.info(f"Initialized local memory storage at {self.storage_dir}")

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file."""
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        return {}

    def _save_json(self, data: Dict[str, Any], file_path: Path):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    def _load_embeddings(self) -> Dict[str, np.ndarray]:
        """Load embeddings from file."""
        if self.embeddings_file.exists():
            try:
                data = np.load(self.embeddings_file, allow_pickle=True)
                return {k: v for k, v in data.items()}
            except Exception as e:
                logger.error(f"Error loading embeddings: {e}")
        return {}

    def _save_embeddings(self):
        """Save embeddings to file."""
        try:
            np.savez_compressed(self.embeddings_file, **self.embeddings)
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    async def initialize(self) -> None:
        """Initialize the database (no-op for local storage)."""
        logger.info("Local memory storage initialized")

    async def close(self) -> None:
        """Close the database connection (save all data)."""
        self._save_json(self.memories, self.memories_file)
        self._save_json(self.facts, self.facts_file)
        self._save_json(self.projects, self.projects_file)
        self._save_embeddings()
        logger.info("Local memory storage closed")

    # Memory operations
    async def create_memory(
        self, memory: MemoryCreate, project_id: str, user_id: Optional[str] = None
    ) -> Memory:
        """Create a new memory."""
        memory_id = str(uuid.uuid4())

        # Create memory object
        memory_data = {
            "id": memory_id,
            "project_id": project_id,
            "user_id": user_id or "default",
            "content": memory.content,
            "memory_type": memory.memory_type,
            "importance": memory.importance,
            "context": memory.context,
            "metadata": memory.metadata or {},
            "source": memory.source,
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store memory
        self.memories[memory_id] = memory_data

        # Store embedding if provided
        if memory.embedding:
            self.embeddings[f"memory_{memory_id}"] = np.array(memory.embedding)

        # Save to disk
        self._save_json(self.memories, self.memories_file)
        if memory.embedding:
            self._save_embeddings()

        # Return with proper memory_id field
        memory_data["memory_id"] = memory_id  # Ensure memory_id is set
        return Memory(**memory_data)

    def search_memories(
        self,
        query_embedding: List[float],
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> Any:
        """Search for similar memories synchronously."""
        query_vec = np.array(query_embedding)
        results = []

        for mem_id, memory in self.memories.items():
            # Filter by project and user
            if project_id and memory.get("project_id") != project_id:
                continue
            if user_id and memory.get("user_id") != user_id:
                continue
            if memory_type and memory.get("memory_type") != memory_type:
                continue

            # Calculate similarity if embedding exists
            embedding_key = f"memory_{mem_id}"
            if embedding_key in self.embeddings:
                similarity = self._compute_similarity(query_vec, self.embeddings[embedding_key])
                results.append({
                    "memory": memory,
                    "similarity": similarity
                })

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        # Convert to dataframe-like structure for compatibility
        import pandas as pd
        if not results:
            return pd.DataFrame()

        # Extract memory data for dataframe
        data = []
        for r in results:
            mem = r["memory"]
            data.append({
                "memory_id": mem.get("id", mem.get("memory_id")),
                "project_id": mem.get("project_id"),
                "user_id": mem.get("user_id"),
                "content": mem.get("content"),
                "memory_type": mem.get("memory_type"),
                "importance": mem.get("importance"),
                "context": mem.get("context"),
                "metadata": mem.get("metadata"),
                "source": mem.get("source"),
                "created_at": mem.get("created_at"),
                "updated_at": mem.get("updated_at"),
                "similarity_score": r["similarity"]
            })

        return pd.DataFrame(data)


    async def search_memories_async(
        self,
        query_embedding: List[float],
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[MemoryResponse]:
        """Search for similar memories."""
        query_vec = np.array(query_embedding)
        results = []

        for mem_id, memory in self.memories.items():
            # Filter by project and user
            if memory["project_id"] != project_id:
                continue
            if user_id and memory.get("user_id") != user_id:
                continue
            if memory_type and memory.get("memory_type") != memory_type:
                continue
            if memory.get("importance", 0) < min_importance:
                continue

            # Calculate similarity if embedding exists
            embedding_key = f"memory_{mem_id}"
            if embedding_key in self.embeddings:
                similarity = self._compute_similarity(query_vec, self.embeddings[embedding_key])
                results.append({
                    "memory": Memory(**memory),
                    "similarity": similarity
                })

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        return [
            MemoryResponse(
                memory=r["memory"],
                similarity=r["similarity"],
                relevance_score=r["similarity"]
            )
            for r in results
        ]

    async def get_recent_memories(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[Memory]:
        """Get recent memories."""
        results = []

        for memory in self.memories.values():
            # Filter
            if memory["project_id"] != project_id:
                continue
            if user_id and memory.get("user_id") != user_id:
                continue
            if memory_type and memory.get("memory_type") != memory_type:
                continue

            results.append(memory)

        # Sort by timestamp
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        results = results[:limit]

        return [Memory(**r) for r in results]

    async def delete_memory(self, memory_id: str, project_id: str) -> bool:
        """Delete a memory."""
        if memory_id in self.memories:
            if self.memories[memory_id]["project_id"] == project_id:
                del self.memories[memory_id]

                # Remove embedding
                embedding_key = f"memory_{memory_id}"
                if embedding_key in self.embeddings:
                    del self.embeddings[embedding_key]

                # Save changes
                self._save_json(self.memories, self.memories_file)
                self._save_embeddings()
                return True
        return False

    # Knowledge operations
    async def create_fact(
        self, fact: FactCreate, project_id: str, user_id: Optional[str] = None
    ) -> Fact:
        """Create a new fact."""
        fact_id = str(uuid.uuid4())

        fact_data = {
            "id": fact_id,
            "project_id": project_id,
            "user_id": user_id or "default",
            "subject": fact.subject,
            "predicate": fact.predicate,
            "object": fact.object,
            "confidence": fact.confidence,
            "source": fact.source,
            "metadata": fact.metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.facts[fact_id] = fact_data

        # Store embedding if provided
        if fact.embedding:
            self.embeddings[f"fact_{fact_id}"] = np.array(fact.embedding)

        # Save to disk
        self._save_json(self.facts, self.facts_file)
        if fact.embedding:
            self._save_embeddings()

        return Fact(**fact_data)

    async def search_facts(
        self,
        query_embedding: List[float],
        project_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.0,
    ) -> List[Fact]:
        """Search for similar facts."""
        query_vec = np.array(query_embedding)
        results = []

        for fact_id, fact in self.facts.items():
            # Filter
            if fact["project_id"] != project_id:
                continue
            if user_id and fact.get("user_id") != user_id:
                continue
            if fact.get("confidence", 0) < min_confidence:
                continue

            # Calculate similarity
            embedding_key = f"fact_{fact_id}"
            if embedding_key in self.embeddings:
                similarity = self._compute_similarity(query_vec, self.embeddings[embedding_key])
                results.append({
                    "fact": fact,
                    "similarity": similarity
                })

        # Sort and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        return [Fact(**r["fact"]) for r in results]

    async def get_knowledge_graph(
        self, project_id: str, user_id: Optional[str] = None
    ) -> KnowledgeBase:
        """Get the knowledge graph."""
        project_facts = []

        for fact in self.facts.values():
            if fact["project_id"] != project_id:
                continue
            if user_id and fact.get("user_id") != user_id:
                continue
            project_facts.append(Fact(**fact))

        # Build entity and relation lists
        entities = set()
        relations = set()

        for fact in project_facts:
            entities.add(fact.subject)
            entities.add(fact.object)
            relations.add(fact.predicate)

        return KnowledgeBase(
            facts=project_facts,
            entities=list(entities),
            relations=list(relations),
            metadata={
                "fact_count": len(project_facts),
                "entity_count": len(entities),
                "relation_count": len(relations)
            }
        )

    # Project operations
    async def create_project(
        self, project: ProjectCreate, user_id: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project_id = str(uuid.uuid4())

        project_data = {
            "id": project_id,
            "project_id": project_id,  # Add project_id field
            "name": project.name,
            "description": project.description,
            "user_id": user_id or "default",
            "metadata": project.metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.projects[project_id] = project_data
        self._save_json(self.projects, self.projects_file)

        return Project(**project_data)

    async def get_project(
        self, project_id: str, user_id: Optional[str] = None
    ) -> Optional[Project]:
        """Get a project by ID."""
        if project_id in self.projects:
            project = self.projects[project_id]
            if not user_id or project.get("user_id") == user_id:
                return Project(**project)
        return None

    async def list_projects(self, user_id: Optional[str] = None) -> List[Project]:
        """List all projects."""
        results = []

        for project in self.projects.values():
            if not user_id or project.get("user_id") == user_id:
                # Ensure project_id exists for backward compatibility
                if "project_id" not in project:
                    project["project_id"] = project.get("id", str(uuid.uuid4()))
                results.append(Project(**project))

        return results

    async def delete_project(
        self, project_id: str, user_id: Optional[str] = None
    ) -> bool:
        """Delete a project and all associated data."""
        if project_id in self.projects:
            project = self.projects[project_id]
            if not user_id or project.get("user_id") == user_id:
                # Delete project
                del self.projects[project_id]

                # Delete associated memories
                memory_ids_to_delete = [
                    mid for mid, m in self.memories.items()
                    if m["project_id"] == project_id
                ]
                for mid in memory_ids_to_delete:
                    del self.memories[mid]
                    embedding_key = f"memory_{mid}"
                    if embedding_key in self.embeddings:
                        del self.embeddings[embedding_key]

                # Delete associated facts
                fact_ids_to_delete = [
                    fid for fid, f in self.facts.items()
                    if f["project_id"] == project_id
                ]
                for fid in fact_ids_to_delete:
                    del self.facts[fid]
                    embedding_key = f"fact_{fid}"
                    if embedding_key in self.embeddings:
                        del self.embeddings[embedding_key]

                # Save all changes
                self._save_json(self.projects, self.projects_file)
                self._save_json(self.memories, self.memories_file)
                self._save_json(self.facts, self.facts_file)
                self._save_embeddings()

                return True
        return False
    # Additional abstract methods implementation
    async def create_memories_table(self, user_id: str = None) -> None:
        """Create memories table (no-op for local storage)."""
        pass

    def create_memories_table(self, user_id: str) -> None:
        """Create memories table for a user (no-op for local storage)."""
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
        """Add a memory synchronously."""
        memory_data = {
            "id": memory_id,
            "memory_id": memory_id,
            "project_id": project_id,
            "user_id": user_id,
            "content": content,
            "memory_type": metadata.get("memory_type", "general") if metadata else "general",
            "importance": importance,
            "context": metadata.get("context", {}) if metadata else {},
            "metadata": metadata or {},
            "source": metadata.get("source", "") if metadata else "",
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store memory
        self.memories[memory_id] = memory_data

        # Store embedding
        if embedding:
            self.embeddings[f"memory_{memory_id}"] = np.array(embedding)

        # Save to disk
        self._save_json(self.memories, self.memories_file)
        if embedding:
            self._save_embeddings()

        return memory_data

    async def add_memory_async(self, memory: MemoryCreate, project_id: str) -> Memory:
        """Add a memory (alias for create_memory)."""
        return await self.create_memory(memory, project_id)

    async def add_fact(self, fact: FactCreate, project_id: str) -> Fact:
        """Add a fact (alias for create_fact)."""
        return await self.create_fact(fact, project_id)

    async def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact by ID."""
        if fact_id in self.facts:
            del self.facts[fact_id]
            embedding_key = f"fact_{fact_id}"
            if embedding_key in self.embeddings:
                del self.embeddings[embedding_key]
            self._save_json(self.facts, self.facts_file)
            self._save_embeddings()
            return True
        return False

    async def create_knowledge_base(self, name: str, description: str, project_id: str) -> KnowledgeBase:
        """Create a knowledge base."""
        return await self.get_knowledge_graph(project_id)

    async def get_knowledge_bases(self, project_id: str) -> List[KnowledgeBase]:
        """Get all knowledge bases for a project."""
        return [await self.get_knowledge_graph(project_id)]

    async def create_chat_session(self, project_id: str, user_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        if not hasattr(self, "chat_sessions"):
            self.chat_sessions = {}
        self.chat_sessions[session_id] = {
            "id": session_id,
            "project_id": project_id,
            "user_id": user_id or "default",
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
        return session_id

    async def add_chat_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a chat session."""
        if not hasattr(self, "chat_sessions"):
            self.chat_sessions = {}
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get messages from a chat session."""
        if not hasattr(self, "chat_sessions"):
            self.chat_sessions = {}
        if session_id in self.chat_sessions:
            return self.chat_sessions[session_id]["messages"]
        return []

    async def search_chat_messages(self, query: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search chat messages."""
        if not hasattr(self, "chat_sessions"):
            return []
        results = []
        sessions_to_search = [session_id] if session_id else self.chat_sessions.keys()
        for sid in sessions_to_search:
            if sid in self.chat_sessions:
                for msg in self.chat_sessions[sid]["messages"]:
                    if query.lower() in msg["content"].lower():
                        results.append(msg)
        return results

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user."""
        return await self.list_projects(user_id)

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
        if memory_id not in self.memories:
            return None

        memory = self.memories[memory_id]

        # Verify user and project match
        if memory.get("user_id") != user_id or memory.get("project_id") != project_id:
            return None

        # Update fields if provided
        if content is not None:
            memory["content"] = content
        if metadata is not None:
            memory["metadata"] = metadata
        if importance is not None:
            memory["importance"] = importance

        # Update timestamp
        memory["updated_at"] = datetime.utcnow().isoformat()

        # Save changes
        self._save_json(self.memories, self.memories_file)

        return memory

    def _import_markdown_memories(self):
        """Import memories from markdown files."""
        if not self.markdown_reader:
            return

        try:
            # Read markdown memories
            markdown_memories = self.markdown_reader.read_markdown_memories()

            # Create a default project for markdown memories
            project_id = "markdown_import"
            if project_id not in self.projects:
                project_data = {
                    "id": project_id,
                    "project_id": project_id,
                    "name": "Markdown Import",
                    "description": "Automatically imported memories from markdown files",
                    "user_id": "system",
                    "metadata": {"auto_created": True},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                self.projects[project_id] = project_data
                self._save_json(self.projects, self.projects_file)

            # Import each memory
            imported_count = 0
            for memory_create in markdown_memories:
                # Check if this memory already exists (by source)
                source = memory_create.source
                existing = any(
                    m.get("source") == source
                    for m in self.memories.values()
                )

                if not existing:
                    memory_id = str(uuid.uuid4())
                    memory_data = {
                        "id": memory_id,
                        "project_id": project_id,
                        "user_id": "system",
                        "content": memory_create.content,
                        "memory_type": memory_create.memory_type,
                        "importance": memory_create.importance,
                        "context": memory_create.context,
                        "metadata": memory_create.metadata or {},
                        "source": source,
                        "timestamp": datetime.utcnow().isoformat(),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    self.memories[memory_id] = memory_data
                    imported_count += 1

            if imported_count > 0:
                self._save_json(self.memories, self.memories_file)
                logger.info(f"Imported {imported_count} new memories from markdown files")

        except Exception as e:
            logger.error(f"Error importing markdown memories: {e}")

