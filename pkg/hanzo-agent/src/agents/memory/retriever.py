"""Memory retrieval strategies."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List, Optional

from .types import MemoryEntry
from ..logger import logger


class MemoryRetriever(ABC):
    """Abstract base class for memory retrieval strategies."""
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        memories: List[MemoryEntry],
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories.
        
        Args:
            query: The query to match against
            memories: Pool of memories to search
            limit: Maximum number of results
            
        Returns:
            List of relevant memories
        """
        pass


class SemanticRetriever(MemoryRetriever):
    """Retrieves memories based on semantic similarity."""
    
    def __init__(self, embedding_model: str | None = None):
        self.embedding_model = embedding_model
        
    async def retrieve(
        self,
        query: str,
        memories: List[MemoryEntry],
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Retrieve semantically similar memories."""
        if not memories:
            return []
            
        # If memories have embeddings, use vector similarity
        if any(m.embedding for m in memories):
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            if query_embedding:
                # Calculate similarities
                scores = []
                for memory in memories:
                    if memory.embedding:
                        similarity = self._cosine_similarity(
                            query_embedding,
                            memory.embedding,
                        )
                        scores.append((memory, similarity))
                        
                # Sort by similarity
                scores.sort(key=lambda x: x[1], reverse=True)
                
                return [memory for memory, _ in scores[:limit]]
                
        # Fallback to keyword matching
        return self._keyword_search(query, memories, limit)
        
    async def _get_embedding(self, text: str) -> List[float] | None:
        """Get embedding for text."""
        # This is a placeholder - implement based on your embedding service
        return None
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        
    def _keyword_search(
        self,
        query: str,
        memories: List[MemoryEntry],
        limit: int,
    ) -> List[MemoryEntry]:
        """Simple keyword-based search."""
        query_words = set(query.lower().split())
        
        scores = []
        for memory in memories:
            content_words = set(memory.content.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            
            if union > 0:
                similarity = intersection / union
                scores.append((memory, similarity))
                
        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [memory for memory, _ in scores[:limit]]


class RecencyRetriever(MemoryRetriever):
    """Retrieves memories based on recency."""
    
    def __init__(self, decay_factor: float = 0.99):
        self.decay_factor = decay_factor
        
    async def retrieve(
        self,
        query: str,
        memories: List[MemoryEntry],
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Retrieve most recent memories."""
        # Sort by timestamp
        sorted_memories = sorted(
            memories,
            key=lambda m: m.timestamp,
            reverse=True,
        )
        
        return sorted_memories[:limit]


class HybridRetriever(MemoryRetriever):
    """Combines multiple retrieval strategies."""
    
    def __init__(
        self,
        semantic_weight: float = 0.6,
        recency_weight: float = 0.2,
        importance_weight: float = 0.2,
        embedding_model: str | None = None,
    ):
        self.semantic_weight = semantic_weight
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight
        self.semantic_retriever = SemanticRetriever(embedding_model)
        self.recency_retriever = RecencyRetriever()
        
    async def retrieve(
        self,
        query: str,
        memories: List[MemoryEntry],
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Retrieve using hybrid scoring."""
        if not memories:
            return []
            
        # Get semantic scores
        semantic_results = await self.semantic_retriever.retrieve(
            query, memories, len(memories)
        )
        semantic_scores = {
            m.id: 1.0 - (i / len(semantic_results))
            for i, m in enumerate(semantic_results)
        }
        
        # Get recency scores
        now = time.time()
        recency_scores = {}
        for memory in memories:
            age_days = (now - memory.timestamp) / 86400
            recency_scores[memory.id] = 1.0 / (1.0 + age_days)
            
        # Get importance scores
        importance_scores = {m.id: m.importance for m in memories}
        
        # Combine scores
        final_scores = {}
        for memory in memories:
            semantic = semantic_scores.get(memory.id, 0.0)
            recency = recency_scores.get(memory.id, 0.0)
            importance = importance_scores.get(memory.id, 0.0)
            
            final_scores[memory.id] = (
                semantic * self.semantic_weight +
                recency * self.recency_weight +
                importance * self.importance_weight
            )
            
        # Sort by final score
        sorted_memories = sorted(
            memories,
            key=lambda m: final_scores[m.id],
            reverse=True,
        )
        
        return sorted_memories[:limit]