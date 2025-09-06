"""Database factory for selecting the appropriate backend."""


from structlog import get_logger

from ..config import settings
from .base import BaseVectorDB
from .client import InfinityClient
from .lancedb_client import LanceDBClient

logger = get_logger()

# Global database client instance
_db_client: BaseVectorDB | None = None


def get_db_client() -> BaseVectorDB:
    """Get or create the global database client based on configuration."""
    global _db_client

    if _db_client is None:
        backend = settings.db_backend.lower()

        if backend == "lancedb":
            logger.info("Using LanceDB backend")
            _db_client = LanceDBClient()
        elif backend == "infinity":
            logger.info("Using InfinityDB backend")
            _db_client = InfinityClient()
        else:
            raise ValueError(f"Unknown database backend: {backend}")

    return _db_client


def reset_db_client() -> None:
    """Reset the global database client (useful for testing)."""
    global _db_client
    _db_client = None
