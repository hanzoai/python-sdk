"""Backend registry for memory storage.

This provides a simple way to register and use different backends.
Supports multiple database types:
- LanceDB: Vector database with SQL-like queries
- KuzuDB: Graph database for relationship-based queries
- InfinityDB: High-performance vector database
- Local files: Simple JSON storage for development
"""

from typing import Dict, Optional, Type
from structlog import get_logger

from ..base import BaseVectorDB
from ..local_client import LocalMemoryClient

logger = get_logger()

# Try to import optional backends
try:
    from ..lancedb_client import LanceDBClient
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logger.debug("LanceDB client not available")

try:
    from ..kuzudb_client import KuzuDBClient
    KUZU_AVAILABLE = True
except ImportError:
    KUZU_AVAILABLE = False
    logger.debug("KuzuDB client not available")

try:
    from ..client import InfinityClient
    INFINITY_AVAILABLE = True
except ImportError:
    INFINITY_AVAILABLE = False
    logger.debug("InfinityDB client not available")

try:
    from ..sqlite_client import SQLiteMemoryClient
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.debug("SQLite client not available")


class BackendCapability:
    """Capabilities that backends can support."""

    VECTOR_SEARCH = "vector_search"
    FULL_TEXT_SEARCH = "full_text_search"
    STRUCTURED_QUERY = "structured_query"
    MARKDOWN_IMPORT = "markdown_import"
    PERSISTENCE = "persistence"
    EMBEDDINGS = "embeddings"
    GRAPH_QUERIES = "graph_queries"
    TIME_SERIES = "time_series"


class BackendRegistry:
    """Registry for memory backends."""

    # Registered backends and their capabilities
    BACKENDS: Dict[str, Dict] = {
        "local": {
            "class": LocalMemoryClient,
            "description": "Local file storage using JSON files",
            "capabilities": [
                BackendCapability.PERSISTENCE,
                BackendCapability.MARKDOWN_IMPORT,
                BackendCapability.FULL_TEXT_SEARCH,
            ],
            "config": {
                "enable_markdown": True,
            },
        },
    }

    # Add optional backends if available
    @classmethod
    def _init_optional_backends(cls):
        """Initialize optional backends if they're available."""
        if LANCEDB_AVAILABLE and "lancedb" not in cls.BACKENDS:
            cls.BACKENDS["lancedb"] = {
                "class": LanceDBClient,
                "description": "LanceDB - Embedded vector database with SQL-like queries",
                "capabilities": [
                    BackendCapability.VECTOR_SEARCH,
                    BackendCapability.STRUCTURED_QUERY,
                    BackendCapability.PERSISTENCE,
                    BackendCapability.EMBEDDINGS,
                    BackendCapability.MARKDOWN_IMPORT,
                ],
                "config": {
                    "enable_markdown": True,
                },
            }

        if KUZU_AVAILABLE and "kuzudb" not in cls.BACKENDS:
            cls.BACKENDS["kuzudb"] = {
                "class": KuzuDBClient,
                "description": "KuzuDB - Graph database for relationship-based memory storage",
                "capabilities": [
                    BackendCapability.GRAPH_QUERIES,
                    BackendCapability.STRUCTURED_QUERY,
                    BackendCapability.PERSISTENCE,
                    BackendCapability.EMBEDDINGS,
                    BackendCapability.MARKDOWN_IMPORT,
                ],
                "config": {
                    "enable_markdown": True,
                },
            }

        if INFINITY_AVAILABLE and "infinity" not in cls.BACKENDS:
            cls.BACKENDS["infinity"] = {
                "class": InfinityClient,
                "description": "InfinityDB - High-performance vector database",
                "capabilities": [
                    BackendCapability.VECTOR_SEARCH,
                    BackendCapability.STRUCTURED_QUERY,
                    BackendCapability.FULL_TEXT_SEARCH,
                    BackendCapability.PERSISTENCE,
                    BackendCapability.EMBEDDINGS,
                    BackendCapability.TIME_SERIES,
                ],
                "config": {},
            }

        if SQLITE_AVAILABLE and "sqlite" not in cls.BACKENDS:
            cls.BACKENDS["sqlite"] = {
                "class": SQLiteMemoryClient,
                "description": "SQLite - Lightweight embedded database with vector search via sqlite-vec",
                "capabilities": [
                    BackendCapability.VECTOR_SEARCH,
                    BackendCapability.STRUCTURED_QUERY,
                    BackendCapability.PERSISTENCE,
                    BackendCapability.EMBEDDINGS,
                    BackendCapability.MARKDOWN_IMPORT,
                ],
                "config": {},
            }

    @classmethod
    def get_backend(
        cls,
        name: str,
        config: Optional[Dict] = None,
    ) -> BaseVectorDB:
        """Get a backend instance by name.

        Args:
            name: Backend name (e.g., "lancedb", "local")
            config: Optional configuration overrides

        Returns:
            Backend instance

        Raises:
            ValueError: If backend not found
        """
        # Initialize optional backends
        cls._init_optional_backends()

        if name not in cls.BACKENDS:
            available = ", ".join(cls.BACKENDS.keys())
            raise ValueError(f"Unknown backend: {name}. Available: {available}")

        backend_info = cls.BACKENDS[name]
        backend_class = backend_info["class"]

        # Merge default config with user config
        backend_config = backend_info.get("config", {}).copy()
        if config:
            backend_config.update(config)

        logger.info(
            f"Creating {name} backend",
            description=backend_info["description"],
            capabilities=backend_info["capabilities"],
        )

        # Create instance with config
        if backend_config:
            return backend_class(**backend_config)
        return backend_class()

    @classmethod
    def list_backends(cls) -> Dict[str, Dict]:
        """List all available backends and their capabilities."""
        # Initialize optional backends
        cls._init_optional_backends()

        return {
            name: {
                "description": info["description"],
                "capabilities": info["capabilities"],
            }
            for name, info in cls.BACKENDS.items()
        }

    @classmethod
    def find_backend_for_capability(
        cls,
        capability: str,
    ) -> Optional[str]:
        """Find the best backend for a specific capability.

        Args:
            capability: Required capability

        Returns:
            Backend name or None if no backend supports it
        """
        for name, info in cls.BACKENDS.items():
            if capability in info["capabilities"]:
                return name
        return None

    @classmethod
    def get_backend_for_task(
        cls,
        task: str,
    ) -> str:
        """Get the recommended backend for a specific task.

        Args:
            task: Task type (e.g., "similarity_search", "document_storage")

        Returns:
            Recommended backend name
        """
        task_mapping = {
            "similarity_search": "lancedb",
            "vector_search": "lancedb",
            "embeddings": "lancedb",
            "document_storage": "local",
            "simple_storage": "local",
            "markdown_import": "local",  # Both support it, but local is simpler
            "development": "local",  # Simple for dev
            "production": "lancedb",  # Better for production
        }

        return task_mapping.get(task, "local")  # Default to local

    @classmethod
    def register_backend(
        cls,
        name: str,
        backend_class: Type[BaseVectorDB],
        description: str,
        capabilities: list[str],
        config: Optional[Dict] = None,
    ) -> None:
        """Register a new backend.

        Args:
            name: Backend name
            backend_class: Backend class
            description: Human-readable description
            capabilities: List of capabilities
            config: Default configuration
        """
        cls.BACKENDS[name] = {
            "class": backend_class,
            "description": description,
            "capabilities": capabilities,
            "config": config or {},
        }
        logger.info(f"Registered backend: {name}")


# Convenience functions
def get_backend(name: str = "local", **config) -> BaseVectorDB:
    """Get a backend instance.

    Args:
        name: Backend name (default: "local")
        **config: Configuration options

    Returns:
        Backend instance
    """
    return BackendRegistry.get_backend(name, config)


def list_backends() -> Dict[str, Dict]:
    """List all available backends."""
    return BackendRegistry.list_backends()


def get_best_backend_for(capability: str) -> Optional[str]:
    """Get the best backend for a capability."""
    return BackendRegistry.find_backend_for_capability(capability)