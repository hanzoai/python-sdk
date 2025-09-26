"""Database backend interfaces and implementations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class DatabaseType(Enum):
    """Types of database backends."""

    VECTOR = "vector"          # For embeddings and similarity search (LanceDB, Pinecone, Weaviate)
    RELATIONAL = "relational"  # For structured data (PostgreSQL, MySQL, SQLite)
    DOCUMENT = "document"      # For JSON documents (MongoDB, CouchDB)
    GRAPH = "graph"            # For relationships (Neo4j, ArangoDB)
    KEY_VALUE = "key_value"    # For simple storage (Redis, RocksDB)
    TIME_SERIES = "time_series"  # For temporal data (InfluxDB, TimescaleDB)
    SEARCH = "search"          # For full-text search (Elasticsearch, MeiliSearch)
    FILE = "file"              # For file-based storage (JSON, CSV, Parquet)


class VectorDatabase(Protocol):
    """Interface for vector databases."""

    async def upsert_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Insert or update vectors with metadata."""
        ...

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        ...

    async def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        ...

    async def get_vectors(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve vectors by ID."""
        ...


class RelationalDatabase(Protocol):
    """Interface for relational databases."""

    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query."""
        ...

    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
    ) -> str:
        """Insert a record and return ID."""
        ...

    async def update(
        self,
        table: str,
        id: str,
        data: Dict[str, Any],
    ) -> bool:
        """Update a record."""
        ...

    async def delete(
        self,
        table: str,
        id: str,
    ) -> bool:
        """Delete a record."""
        ...

    async def select(
        self,
        table: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Select records from table."""
        ...

    async def create_table(
        self,
        table: str,
        schema: Dict[str, str],
    ) -> None:
        """Create a table with schema."""
        ...


class DocumentDatabase(Protocol):
    """Interface for document databases."""

    async def insert_document(
        self,
        collection: str,
        document: Dict[str, Any],
    ) -> str:
        """Insert a document and return ID."""
        ...

    async def find_documents(
        self,
        collection: str,
        filter: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find documents matching filter."""
        ...

    async def update_document(
        self,
        collection: str,
        id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a document."""
        ...

    async def delete_document(
        self,
        collection: str,
        id: str,
    ) -> bool:
        """Delete a document."""
        ...

    async def create_index(
        self,
        collection: str,
        fields: List[str],
    ) -> None:
        """Create an index on fields."""
        ...


class GraphDatabase(Protocol):
    """Interface for graph databases."""

    async def add_node(
        self,
        id: str,
        labels: List[str],
        properties: Dict[str, Any],
    ) -> None:
        """Add a node to the graph."""
        ...

    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        relationship: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an edge between nodes."""
        ...

    async def find_neighbors(
        self,
        node_id: str,
        relationship: Optional[str] = None,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """Find neighboring nodes."""
        ...

    async def shortest_path(
        self,
        from_id: str,
        to_id: str,
    ) -> Optional[List[str]]:
        """Find shortest path between nodes."""
        ...


class KeyValueDatabase(Protocol):
    """Interface for key-value databases."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set key-value with optional TTL."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

    async def keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern."""
        ...


class SearchDatabase(Protocol):
    """Interface for search databases."""

    async def index_document(
        self,
        index: str,
        id: str,
        document: Dict[str, Any],
    ) -> None:
        """Index a document for search."""
        ...

    async def search(
        self,
        index: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Full-text search."""
        ...

    async def delete_document(
        self,
        index: str,
        id: str,
    ) -> bool:
        """Delete a document from index."""
        ...

    async def create_index(
        self,
        index: str,
        mappings: Dict[str, Any],
    ) -> None:
        """Create a search index."""
        ...


class TimeSeriesDatabase(Protocol):
    """Interface for time-series databases."""

    async def write_point(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: Optional[int] = None,
    ) -> None:
        """Write a time-series data point."""
        ...

    async def query(
        self,
        measurement: str,
        start_time: int,
        end_time: int,
        aggregation: Optional[str] = None,
        group_by: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query time-series data."""
        ...

    async def delete_series(
        self,
        measurement: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Delete a time series."""
        ...


class FileDatabase(Protocol):
    """Interface for file-based storage."""

    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read data from file."""
        ...

    async def write_file(
        self,
        path: str,
        data: Dict[str, Any],
    ) -> None:
        """Write data to file."""
        ...

    async def append_file(
        self,
        path: str,
        data: Any,
    ) -> None:
        """Append data to file."""
        ...

    async def delete_file(self, path: str) -> bool:
        """Delete a file."""
        ...

    async def list_files(
        self,
        pattern: str = "*",
    ) -> List[str]:
        """List files matching pattern."""
        ...


class DatabaseBackend(ABC):
    """Base class for all database backends."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.db_type: DatabaseType = DatabaseType.FILE
        self.capabilities: List[str] = []

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is healthy."""
        pass

    def supports(self, capability: str) -> bool:
        """Check if backend supports a capability."""
        return capability in self.capabilities