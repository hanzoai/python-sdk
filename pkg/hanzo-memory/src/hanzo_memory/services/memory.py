"""Memory service for managing memories."""

import json
import uuid
from datetime import datetime

from structlog import get_logger

from ..db import get_db_client
from ..models.memory import Memory, MemoryWithScore
from .embeddings import get_embedding_service
from .llm import get_llm_service

logger = get_logger()


class MemoryService:
    """Service for managing memories."""

    def __init__(self) -> None:
        """Initialize memory service."""
        self.db = get_db_client()
        self.embeddings = get_embedding_service()
        self.llm = get_llm_service()

    def create_memory(
        self,
        user_id: str,
        project_id: str,
        content: str,
        metadata: dict | None = None,
        importance: float = 1.0,
        strip_pii: bool = False,
    ) -> Memory:
        """
        Create a new memory.

        Args:
            user_id: User ID
            project_id: Project ID
            content: Memory content
            metadata: Additional metadata
            importance: Importance score
            strip_pii: Whether to strip PII from content

        Returns:
            Created memory
        """
        # Ensure user's memory table exists
        self.db.create_memories_table(user_id)

        # Strip PII if requested
        if strip_pii:
            content = self._strip_pii(content)

        # Generate embedding
        embedding = self.embeddings.embed_single(content)

        # Create memory
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        memory_data = self.db.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            importance=importance,
        )

        # Parse JSON fields if needed
        if isinstance(memory_data.get("metadata"), str):
            memory_data["metadata"] = json.loads(memory_data["metadata"])

        return Memory(**memory_data)

    def search_memories(
        self,
        user_id: str,
        query: str,
        project_id: str | None = None,
        limit: int = 10,
        filter_with_llm: bool = False,
        additional_context: str | None = None,
    ) -> list[MemoryWithScore]:
        """
        Search memories by semantic similarity.

        Args:
            user_id: User ID
            query: Search query
            project_id: Optional project filter
            limit: Maximum results
            filter_with_llm: Use LLM to filter results
            additional_context: Additional context for filtering

        Returns:
            List of memories with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_single(query)

        # Search memories
        results_df = self.db.search_memories(
            user_id=user_id,
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit * 2 if filter_with_llm else limit,  # Get more if filtering
        )

        # Handle both list and DataFrame results
        if isinstance(results_df, list):
            results = results_df
        else:
            # DataFrame case
            if results_df.empty:
                return []
            results = (
                results_df.to_dicts()
                if hasattr(results_df, "to_dicts")
                else results_df.to_dict("records")
            )

        if not results:
            return []

        # Convert to memories with scores
        memories = []
        for row in results:
            # Get similarity score if available, otherwise calculate it
            if "similarity_score" in row:
                score = row["similarity_score"]
            elif "embedding" in row:
                # Calculate similarity score (cosine similarity)
                embedding = row["embedding"]
                score = self.embeddings.compute_similarity(
                    query_embedding, [embedding], metric="cosine"
                )[0]
            else:
                score = 0.0  # Default score if no embedding available

            # Parse metadata if it's a string
            metadata = row.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            memory = MemoryWithScore(
                memory_id=row.get("memory_id", row.get("id")),
                user_id=row.get("user_id"),
                project_id=row.get("project_id"),
                content=row.get("content"),
                metadata=metadata,
                importance=row.get("importance", 0.5),
                created_at=datetime.fromisoformat(
                    row.get("created_at", datetime.now().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    row.get("updated_at", datetime.now().isoformat())
                ),
                embedding=row.get("embedding"),
                similarity_score=score,
            )
            memories.append(memory)

        # Sort by similarity score
        memories.sort(key=lambda m: m.similarity_score, reverse=True)

        # Filter with LLM if requested
        if filter_with_llm and memories:
            memories = self._filter_with_llm(
                query=query,
                memories=memories[: limit * 2],
                limit=limit,
                additional_context=additional_context,
            )

        return memories[:limit]

    def get_memory(self, user_id: str, memory_id: str) -> Memory | None:
        """Get a specific memory by ID."""
        # This would need to be implemented in the DB client
        # For now, return None
        logger.warning(f"get_memory not fully implemented for {memory_id}")
        return None

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a memory."""
        # This would need to be implemented in the DB client
        logger.warning(f"delete_memory not fully implemented for {memory_id}")
        return False

    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        project_id: str,
        content: str | None = None,
        metadata: dict | None = None,
        importance: float | None = None,
    ) -> Memory | None:
        """Update a memory."""
        # Update the memory in the database
        updated_data = self.db.update_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            metadata=metadata,
            importance=importance,
        )

        if updated_data:
            # Parse JSON fields if needed
            if isinstance(updated_data.get("metadata"), str):
                updated_data["metadata"] = json.loads(updated_data["metadata"])
            if isinstance(updated_data.get("context"), str):
                updated_data["context"] = json.loads(updated_data.get("context", "{}"))

            return Memory(**updated_data)

        return None

    def delete_user_memories(self, user_id: str) -> int:
        """Delete all memories for a user."""
        # This would need to be implemented in the DB client
        logger.warning(f"delete_user_memories not fully implemented for {user_id}")
        return 0

    def _strip_pii(self, content: str) -> str:
        """Strip PII from content using LLM."""
        prompt = f"""Remove any personally identifiable information (PII) from the following text.
Replace names with [NAME], emails with [EMAIL], phone numbers with [PHONE], addresses with [ADDRESS], etc.

Text: {content}

Anonymized text:"""

        try:
            anonymized = self.llm.complete(prompt)
            return anonymized.strip()
        except Exception as e:
            logger.error(f"Error stripping PII: {e}")
            return content

    def _filter_with_llm(
        self,
        query: str,
        memories: list[MemoryWithScore],
        limit: int,
        additional_context: str | None = None,
    ) -> list[MemoryWithScore]:
        """Filter memories using LLM to select most relevant."""
        # Create memory list for LLM
        memory_texts = []
        for i, memory in enumerate(memories):
            memory_texts.append(f"{i + 1}. {memory.content}")

        context = (
            f"Additional context: {additional_context}" if additional_context else ""
        )

        prompt = f"""Given the query: "{query}"
{context}

Select the {limit} most relevant memories from the following list.
Return only the numbers of the selected memories, separated by commas.

Memories:
{chr(10).join(memory_texts)}

Selected memory numbers:"""

        try:
            response = self.llm.complete(prompt)
            # Parse selected indices
            selected_indices = []
            for part in response.strip().split(","):
                try:
                    idx = int(part.strip()) - 1
                    if 0 <= idx < len(memories):
                        selected_indices.append(idx)
                except ValueError:
                    continue

            # Return selected memories
            return [memories[i] for i in selected_indices[:limit]]
        except Exception as e:
            logger.error(f"Error filtering with LLM: {e}")
            return memories[:limit]


# Global memory service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get or create the global memory service."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


def reset_memory_service() -> None:
    """Reset the global memory service (useful for testing)."""
    global _memory_service
    _memory_service = None
