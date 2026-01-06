"""Memory storage backends."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np

from .types import MemoryEntry, MemoryType
from ..logger import logger


class MemoryStore(ABC):
    """Abstract base class for memory stores."""
    
    @abstractmethod
    async def add(
        self,
        content: str,
        type: MemoryType,
        agent_name: str | None = None,
        importance: float = 1.0,
        metadata: Dict[str, Any] | None = None,
        embedding: List[float] | None = None,
    ) -> MemoryEntry:
        """Add a new memory."""
        pass
        
    @abstractmethod
    async def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a memory by ID."""
        pass
        
    @abstractmethod
    async def update(self, memory: MemoryEntry) -> None:
        """Update an existing memory."""
        pass
        
    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        """Delete a memory."""
        pass
        
    @abstractmethod
    async def list(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
        min_importance: float = 0.0,
        limit: int | None = None,
    ) -> List[MemoryEntry]:
        """List memories with filters."""
        pass
        
    @abstractmethod
    async def count(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
    ) -> int:
        """Count memories."""
        pass
        
    @abstractmethod
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
    ) -> List[tuple[MemoryEntry, float]]:
        """Search memories by embedding similarity."""
        pass


class InMemoryMemoryStore(MemoryStore):
    """In-memory memory store for development."""
    
    def __init__(self):
        self.memories: Dict[str, MemoryEntry] = {}
        
    async def add(
        self,
        content: str,
        type: MemoryType,
        agent_name: str | None = None,
        importance: float = 1.0,
        metadata: Dict[str, Any] | None = None,
        embedding: List[float] | None = None,
    ) -> MemoryEntry:
        """Add a new memory."""
        memory = MemoryEntry(
            id=str(uuid.uuid4()),
            type=type,
            content=content,
            agent_name=agent_name,
            importance=importance,
            metadata=metadata or {},
            embedding=embedding,
        )
        
        self.memories[memory.id] = memory
        return memory
        
    async def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a memory by ID."""
        return self.memories.get(memory_id)
        
    async def update(self, memory: MemoryEntry) -> None:
        """Update an existing memory."""
        if memory.id in self.memories:
            self.memories[memory.id] = memory
            
    async def delete(self, memory_id: str) -> None:
        """Delete a memory."""
        self.memories.pop(memory_id, None)
        
    async def list(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
        min_importance: float = 0.0,
        limit: int | None = None,
    ) -> List[MemoryEntry]:
        """List memories with filters."""
        memories = list(self.memories.values())
        
        # Apply filters
        if type:
            memories = [m for m in memories if m.type == type]
        if agent_name:
            memories = [m for m in memories if m.agent_name == agent_name]
        if min_importance > 0:
            memories = [m for m in memories if m.importance >= min_importance]
            
        # Sort by timestamp (newest first)
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            memories = memories[:limit]
            
        return memories
        
    async def count(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
    ) -> int:
        """Count memories."""
        memories = await self.list(type=type, agent_name=agent_name)
        return len(memories)
        
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
    ) -> List[tuple[MemoryEntry, float]]:
        """Search memories by embedding similarity."""
        if not embedding:
            return []
            
        results = []
        query_vec = np.array(embedding)
        
        for memory in self.memories.values():
            if not memory.embedding:
                continue
                
            # Calculate cosine similarity
            memory_vec = np.array(memory.embedding)
            similarity = np.dot(query_vec, memory_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(memory_vec)
            )
            
            if similarity >= threshold:
                results.append((memory, float(similarity)))
                
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]


class VectorMemoryStore(MemoryStore):
    """Vector database backed memory store."""
    
    def __init__(
        self,
        collection_name: str = "agent_memories",
        embedding_model: str | None = None,
        **vector_db_kwargs,
    ):
        """Initialize vector memory store.
        
        Args:
            collection_name: Name of the vector collection
            embedding_model: Model to use for embeddings
            **vector_db_kwargs: Additional arguments for vector database
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.vector_db_kwargs = vector_db_kwargs
        self._client = None
        self._collection = None
        
    async def _get_client(self):
        """Get or create vector database client."""
        if self._client is None:
            try:
                import chromadb
            except ImportError:
                raise ImportError(
                    "Vector memory store requires 'chromadb' package. "
                    "Install with: pip install chromadb"
                )
                
            self._client = chromadb.Client(**self.vector_db_kwargs)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            
        return self._client, self._collection
        
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self.embedding_model:
            # Use specified embedding model
            # This is a placeholder - implement based on your embedding service
            raise NotImplementedError("Custom embedding models not yet implemented")
        else:
            # Use ChromaDB's default embedding
            return None
            
    async def add(
        self,
        content: str,
        type: MemoryType,
        agent_name: str | None = None,
        importance: float = 1.0,
        metadata: Dict[str, Any] | None = None,
        embedding: List[float] | None = None,
    ) -> MemoryEntry:
        """Add a new memory."""
        _, collection = await self._get_client()
        
        memory = MemoryEntry(
            id=str(uuid.uuid4()),
            type=type,
            content=content,
            agent_name=agent_name,
            importance=importance,
            metadata=metadata or {},
            embedding=embedding,
        )
        
        # Prepare metadata for ChromaDB
        chroma_metadata = {
            "type": type.value,
            "agent_name": agent_name or "",
            "importance": importance,
            "timestamp": memory.timestamp,
            **memory.metadata,
        }
        
        # Add to vector database
        collection.add(
            ids=[memory.id],
            documents=[content],
            metadatas=[chroma_metadata],
            embeddings=[embedding] if embedding else None,
        )
        
        return memory
        
    async def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a memory by ID."""
        _, collection = await self._get_client()
        
        result = collection.get(ids=[memory_id])
        
        if not result["ids"]:
            return None
            
        # Reconstruct memory entry
        metadata = result["metadatas"][0]
        
        return MemoryEntry(
            id=memory_id,
            type=MemoryType(metadata["type"]),
            content=result["documents"][0],
            agent_name=metadata.get("agent_name") or None,
            importance=metadata.get("importance", 1.0),
            timestamp=metadata.get("timestamp", 0),
            metadata={k: v for k, v in metadata.items() 
                     if k not in ["type", "agent_name", "importance", "timestamp"]},
            embedding=result.get("embeddings", [None])[0],
        )
        
    async def update(self, memory: MemoryEntry) -> None:
        """Update an existing memory."""
        _, collection = await self._get_client()
        
        # Update in vector database
        chroma_metadata = {
            "type": memory.type.value,
            "agent_name": memory.agent_name or "",
            "importance": memory.importance,
            "timestamp": memory.timestamp,
            "access_count": memory.access_count,
            "last_accessed": memory.last_accessed or 0,
            **memory.metadata,
        }
        
        collection.update(
            ids=[memory.id],
            documents=[memory.content],
            metadatas=[chroma_metadata],
            embeddings=[memory.embedding] if memory.embedding else None,
        )
        
    async def delete(self, memory_id: str) -> None:
        """Delete a memory."""
        _, collection = await self._get_client()
        collection.delete(ids=[memory_id])
        
    async def list(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
        min_importance: float = 0.0,
        limit: int | None = None,
    ) -> List[MemoryEntry]:
        """List memories with filters."""
        _, collection = await self._get_client()
        
        # Build where clause
        where = {}
        if type:
            where["type"] = type.value
        if agent_name:
            where["agent_name"] = agent_name
        if min_importance > 0:
            where["importance"] = {"$gte": min_importance}
            
        # Query collection
        result = collection.get(
            where=where if where else None,
            limit=limit,
        )
        
        # Convert to memory entries
        memories = []
        for i in range(len(result["ids"])):
            metadata = result["metadatas"][i]
            
            memory = MemoryEntry(
                id=result["ids"][i],
                type=MemoryType(metadata["type"]),
                content=result["documents"][i],
                agent_name=metadata.get("agent_name") or None,
                importance=metadata.get("importance", 1.0),
                timestamp=metadata.get("timestamp", 0),
                access_count=metadata.get("access_count", 0),
                last_accessed=metadata.get("last_accessed"),
                metadata={k: v for k, v in metadata.items() 
                         if k not in ["type", "agent_name", "importance", "timestamp", 
                                     "access_count", "last_accessed"]},
                embedding=result.get("embeddings", [None] * len(result["ids"]))[i],
            )
            memories.append(memory)
            
        # Sort by timestamp
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        return memories
        
    async def count(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
    ) -> int:
        """Count memories."""
        memories = await self.list(type=type, agent_name=agent_name)
        return len(memories)
        
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
    ) -> List[tuple[MemoryEntry, float]]:
        """Search memories by embedding similarity."""
        _, collection = await self._get_client()
        
        # Query by embedding
        result = collection.query(
            query_embeddings=[embedding],
            n_results=limit,
        )
        
        if not result["ids"][0]:
            return []
            
        # Convert to memory entries with scores
        memories_with_scores = []
        
        for i in range(len(result["ids"][0])):
            metadata = result["metadatas"][0][i]
            distance = result["distances"][0][i]
            
            # Convert distance to similarity (1 - normalized distance)
            similarity = 1.0 - (distance / 2.0)  # Cosine distance is [0, 2]
            
            if similarity >= threshold:
                memory = MemoryEntry(
                    id=result["ids"][0][i],
                    type=MemoryType(metadata["type"]),
                    content=result["documents"][0][i],
                    agent_name=metadata.get("agent_name") or None,
                    importance=metadata.get("importance", 1.0),
                    timestamp=metadata.get("timestamp", 0),
                    access_count=metadata.get("access_count", 0),
                    last_accessed=metadata.get("last_accessed"),
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ["type", "agent_name", "importance", "timestamp",
                                         "access_count", "last_accessed"]},
                )
                
                memories_with_scores.append((memory, similarity))
                
        return memories_with_scores