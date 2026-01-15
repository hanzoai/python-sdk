"""Unified memory interface with backend selection.

This module provides a clean API for accessing different memory backends
using a simple syntax like:
    memory['lancedb']  # Access LanceDB backend
    memory['kuzudb']   # Access KuzuDB backend
    memory['infinity'] # Access InfinityDB backend
    memory.local       # Access local backend (default)
"""

from typing import Dict, Optional, Any
from structlog import get_logger

from .db.factory import get_db_client, reset_db_client, list_available_backends
from .db.base import BaseVectorDB
from .services.memory import MemoryService
from .services.embeddings import EmbeddingService
from .services.llm import LLMService

logger = get_logger()


class MemoryBackendProxy:
    """Proxy for accessing specific memory backends."""

    def __init__(self, backend_name: str, config: Optional[Dict] = None):
        """Initialize backend proxy.

        Args:
            backend_name: Name of the backend to use
            config: Optional backend configuration
        """
        self.backend_name = backend_name
        self.config = config or {}
        self._client = None
        self._service = None

    @property
    def client(self) -> BaseVectorDB:
        """Get the database client for this backend."""
        if self._client is None:
            reset_db_client()
            self._client = get_db_client(
                backend=self.backend_name,
                config=self.config
            )
        return self._client

    @property
    def service(self) -> MemoryService:
        """Get the memory service for this backend."""
        if self._service is None:
            # Initialize services
            embeddings = EmbeddingService()
            llm = LLMService()

            # Create service with this backend
            self._service = MemoryService()
            self._service.db = self.client
            self._service.embeddings = embeddings
            self._service.llm = llm

        return self._service

    async def initialize(self):
        """Initialize the backend."""
        await self.client.initialize()
        logger.info(f"Initialized {self.backend_name} backend")

    async def close(self):
        """Close the backend connection."""
        if self._client:
            await self._client.close()
            logger.info(f"Closed {self.backend_name} backend")

    def __repr__(self):
        """String representation."""
        return f"<MemoryBackend:{self.backend_name}>"


class Memory:
    """Main memory interface with backend selection.

    Usage:
        # Using dictionary syntax
        memory['lancedb']   # Get LanceDB backend
        memory['kuzudb']    # Get KuzuDB backend
        memory['infinity']  # Get InfinityDB backend

        # Using attribute syntax
        memory.lancedb      # Get LanceDB backend
        memory.kuzudb       # Get KuzuDB backend
        memory.infinity     # Get InfinityDB backend
        memory.local        # Get local backend (default)

        # List available backends
        memory.backends()   # Returns list of available backends

        # Use a specific backend
        lance = memory['lancedb']
        await lance.initialize()
        await lance.service.create_memory(...)

        # Or with context manager (auto initialize/close)
        async with memory.use('lancedb') as backend:
            await backend.service.create_memory(...)
    """

    def __init__(self, default_backend: str = "local"):
        """Initialize memory interface.

        Args:
            default_backend: Default backend to use
        """
        self.default_backend = default_backend
        self._backends: Dict[str, MemoryBackendProxy] = {}

    def __getitem__(self, backend_name: str) -> MemoryBackendProxy:
        """Get a backend using dictionary syntax.

        Args:
            backend_name: Name of the backend

        Returns:
            Backend proxy instance
        """
        if backend_name not in self._backends:
            self._backends[backend_name] = MemoryBackendProxy(backend_name)
        return self._backends[backend_name]

    def __getattr__(self, backend_name: str) -> MemoryBackendProxy:
        """Get a backend using attribute syntax.

        Args:
            backend_name: Name of the backend

        Returns:
            Backend proxy instance
        """
        # Handle special attributes
        if backend_name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{backend_name}'")

        # Convert attribute name to backend name (e.g., 'infinity_db' -> 'infinitydb')
        backend_name = backend_name.replace('_', '')

        return self[backend_name]

    def backends(self) -> Dict[str, Dict]:
        """List all available backends.

        Returns:
            Dictionary of backend names to their info
        """
        return list_available_backends()

    def use(self, backend_name: str, config: Optional[Dict] = None):
        """Context manager for using a specific backend.

        Args:
            backend_name: Name of the backend
            config: Optional backend configuration

        Returns:
            Async context manager for the backend
        """
        return MemoryBackendContext(backend_name, config)

    def __repr__(self):
        """String representation."""
        backends = list(self.backends().keys())
        return f"<Memory backends={backends}>"


class MemoryBackendContext:
    """Async context manager for using a memory backend."""

    def __init__(self, backend_name: str, config: Optional[Dict] = None):
        """Initialize context.

        Args:
            backend_name: Name of the backend
            config: Optional backend configuration
        """
        self.backend = MemoryBackendProxy(backend_name, config)

    async def __aenter__(self):
        """Enter context - initialize backend."""
        await self.backend.initialize()
        return self.backend

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - close backend."""
        await self.backend.close()


# Global memory instance
memory = Memory()


# Convenience functions for common operations
async def remember(content: str, backend: str = "local", **kwargs):
    """Quick function to remember something.

    Args:
        content: Content to remember
        backend: Backend to use (default: local)
        **kwargs: Additional parameters for memory creation

    Returns:
        Created memory object
    """
    async with memory.use(backend) as mem:
        from .models.memory import MemoryCreate

        memory_obj = MemoryCreate(
            content=content,
            **kwargs
        )
        return await mem.service.create_memory(
            memory=memory_obj,
            project_id=kwargs.get('project_id', 'default'),
            user_id=kwargs.get('user_id', 'default')
        )


async def recall(query: str, backend: str = "local", **kwargs):
    """Quick function to recall memories.

    Args:
        query: Search query
        backend: Backend to use (default: local)
        **kwargs: Additional search parameters

    Returns:
        List of matching memories
    """
    async with memory.use(backend) as mem:
        return await mem.service.search_memories(
            query=query,
            user_id=kwargs.get('user_id', 'default'),
            project_id=kwargs.get('project_id', 'default'),
            limit=kwargs.get('limit', 10)
        )


# Export main components
__all__ = [
    'Memory',
    'memory',
    'remember',
    'recall',
    'MemoryBackendProxy',
    'MemoryBackendContext',
]