"""Database factory for selecting the appropriate backend."""

from typing import Optional, Dict, Any
from structlog import get_logger

from ..config import settings
from .base import BaseVectorDB
from .backends.backend_registry import BackendRegistry

logger = get_logger()

# Global database client instance
_db_client: BaseVectorDB | None = None


def get_db_client(
    backend: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> BaseVectorDB:
    """Get or create the global database client.

    Args:
        backend: Override backend type (default: from settings)
        config: Optional configuration for the backend

    Returns:
        Database client instance
    """
    global _db_client

    # Determine backend
    backend_name = backend or settings.db_backend.lower()

    # Reset client if backend changed
    if _db_client and hasattr(_db_client, "__backend_name__"):
        if _db_client.__backend_name__ != backend_name:  # type: ignore
            logger.info(f"Backend changed from {_db_client.__backend_name__} to {backend_name}, resetting client")  # type: ignore
            _db_client = None

    if _db_client is None:
        # Special handling for legacy "infinity" backend name
        if backend_name == "infinity":
            logger.warning("InfinityDB backend is optional, falling back to local")
            backend_name = "local"

        try:
            _db_client = BackendRegistry.get_backend(backend_name, config)
            _db_client.__backend_name__ = backend_name  # type: ignore  # Store for comparison
        except ValueError as e:
            logger.error(f"Failed to create backend {backend_name}: {e}")
            logger.info("Falling back to local backend")
            _db_client = BackendRegistry.get_backend("local", config)
            _db_client.__backend_name__ = "local"  # type: ignore

    return _db_client


def reset_db_client() -> None:
    """Reset the global database client (useful for testing)."""
    global _db_client
    _db_client = None


def list_available_backends() -> Dict[str, Dict]:
    """List all available backends and their capabilities."""
    return BackendRegistry.list_backends()


def get_backend_for_task(task: str) -> str:
    """Get the recommended backend for a specific task.

    Args:
        task: Task description (e.g., "vector_search", "document_storage")

    Returns:
        Recommended backend name
    """
    return BackendRegistry.get_backend_for_task(task)
