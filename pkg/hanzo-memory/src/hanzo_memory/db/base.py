"""Base database interface for vector storage backends."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseVectorDB(ABC):
    """Abstract base class for vector database backends."""

    @abstractmethod
    def create_project(
        self,
        project_id: str,
        user_id: str,
        name: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new project."""
        pass

    @abstractmethod
    def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """Get all projects for a user."""
        pass

    @abstractmethod
    def create_memories_table(self, user_id: str) -> None:
        """Create a memories table for a user."""
        pass

    @abstractmethod
    def add_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
        importance: float = 0.5,
    ) -> dict[str, Any]:
        """Add a memory to the database."""
        pass

    @abstractmethod
    def search_memories(
        self,
        user_id: str,
        query_embedding: list[float],
        project_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search memories by similarity."""
        pass

    @abstractmethod
    def create_knowledge_base(
        self,
        knowledge_base_id: str,
        project_id: str,
        name: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new knowledge base."""
        pass

    @abstractmethod
    def get_knowledge_bases(self, project_id: str) -> list[dict[str, Any]]:
        """Get all knowledge bases for a project."""
        pass

    @abstractmethod
    def add_fact(
        self,
        fact_id: str,
        knowledge_base_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Add a fact to a knowledge base."""
        pass

    @abstractmethod
    def search_facts(
        self,
        knowledge_base_id: str,
        query_embedding: Optional[list[float]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search facts in a knowledge base."""
        pass

    @abstractmethod
    def delete_fact(self, fact_id: str, knowledge_base_id: str) -> bool:
        """Delete a fact from a knowledge base."""
        pass

    @abstractmethod
    def create_chat_session(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a new chat session."""
        pass

    @abstractmethod
    def add_chat_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Add a message to a chat session."""
        pass

    @abstractmethod
    def get_chat_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get messages from a chat session."""
        pass

    @abstractmethod
    def search_chat_messages(
        self,
        session_id: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search messages in a chat session by similarity."""
        pass

    # Optional methods for implementations - not abstract
    # Implementations can override these if needed

    def close(self) -> None:
        """Close the database connection (optional for implementations)."""
        # Default implementation does nothing
        return None

    def create_projects_table(self) -> None:
        """Create projects table if not exists (optional for implementations)."""
        # Default implementation does nothing
        return None

    def create_knowledge_bases_table(self) -> None:
        """Create knowledge bases table if not exists (optional for implementations)."""
        # Default implementation does nothing
        return None
