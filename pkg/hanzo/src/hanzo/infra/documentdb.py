"""MongoDB document database client wrapper for Hanzo infrastructure.

Provides async interface to MongoDB for document storage and querying,
supporting both MongoDB Atlas and self-hosted deployments.
"""

from __future__ import annotations

import os
from typing import Any, TypeVar, Optional, Sequence
from datetime import datetime
from dataclasses import field, dataclass

from pydantic import Field, BaseModel

T = TypeVar("T", bound=dict[str, Any])


class DocumentDBConfig(BaseModel):
    """Configuration for MongoDB connection."""

    host: str = Field(default="localhost", description="MongoDB server host")
    port: int = Field(default=27017, description="MongoDB server port")
    username: Optional[str] = Field(default=None, description="Authentication username")
    password: Optional[str] = Field(default=None, description="Authentication password")
    database: str = Field(default="hanzo", description="Default database name")
    uri: Optional[str] = Field(default=None, description="Full connection URI (overrides host/port)")
    auth_source: str = Field(default="admin", description="Authentication database")
    replica_set: Optional[str] = Field(default=None, description="Replica set name")
    tls: bool = Field(default=False, description="Use TLS/SSL")
    server_selection_timeout_ms: int = Field(default=5000, description="Server selection timeout")
    connect_timeout_ms: int = Field(default=5000, description="Connection timeout")
    socket_timeout_ms: int = Field(default=30000, description="Socket timeout")

    @classmethod
    def from_env(cls) -> DocumentDBConfig:
        """Create config from environment variables.

        Environment variables:
            MONGODB_HOST: Server host (default: localhost)
            MONGODB_PORT: Server port (default: 27017)
            MONGODB_USERNAME: Authentication username
            MONGODB_PASSWORD: Authentication password
            MONGODB_DATABASE: Database name (default: hanzo)
            MONGODB_URI: Full connection URI (overrides host/port)
            MONGODB_TLS: Use TLS (default: false)
        """
        return cls(
            host=os.getenv("MONGODB_HOST", "localhost"),
            port=int(os.getenv("MONGODB_PORT", "27017")),
            username=os.getenv("MONGODB_USERNAME"),
            password=os.getenv("MONGODB_PASSWORD"),
            database=os.getenv("MONGODB_DATABASE", "hanzo"),
            uri=os.getenv("MONGODB_URI"),
            tls=os.getenv("MONGODB_TLS", "").lower() in ("true", "1", "yes"),
        )


@dataclass
class Document:
    """A MongoDB document with metadata."""

    id: str
    data: dict[str, Any]
    collection: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class QueryResult:
    """Result of a query operation."""

    documents: list[dict[str, Any]]
    count: int
    has_more: bool = False


@dataclass
class UpdateResult:
    """Result of an update operation."""

    matched_count: int
    modified_count: int
    upserted_id: Optional[str] = None


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted_count: int


class DocumentDBClient:
    """Async client for MongoDB document database.

    Wraps motor (async MongoDB driver) with Hanzo conventions.

    Example:
        ```python
        client = DocumentDBClient(DocumentDBConfig.from_env())
        await client.connect()

        # Insert documents
        doc_id = await client.insert_one("users", {"name": "Alice", "email": "alice@example.com"})

        # Find documents
        users = await client.find("users", {"name": "Alice"})

        # Update documents
        result = await client.update_one("users", {"_id": doc_id}, {"$set": {"status": "active"}})

        # Aggregate
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        stats = await client.aggregate("users", pipeline)
        ```
    """

    def __init__(self, config: Optional[DocumentDBConfig] = None) -> None:
        """Initialize document database client.

        Args:
            config: MongoDB configuration. If None, loads from environment.
        """
        self.config = config or DocumentDBConfig.from_env()
        self._client: Any = None
        self._db: Any = None

    async def connect(self) -> None:
        """Establish connection to MongoDB server."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError as e:
            raise ImportError("motor is required for DocumentDBClient. Install with: pip install motor") from e

        if self.config.uri:
            self._client = AsyncIOMotorClient(
                self.config.uri,
                serverSelectionTimeoutMS=self.config.server_selection_timeout_ms,
                connectTimeoutMS=self.config.connect_timeout_ms,
                socketTimeoutMS=self.config.socket_timeout_ms,
            )
        else:
            self._client = AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                authSource=self.config.auth_source,
                replicaSet=self.config.replica_set,
                tls=self.config.tls,
                serverSelectionTimeoutMS=self.config.server_selection_timeout_ms,
                connectTimeoutMS=self.config.connect_timeout_ms,
                socketTimeoutMS=self.config.socket_timeout_ms,
            )

        self._db = self._client[self.config.database]

    async def close(self) -> None:
        """Close the connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def health_check(self) -> bool:
        """Check if MongoDB server is healthy.

        Returns:
            True if server is reachable and responding.
        """
        if not self._client:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def _get_collection(self, collection: str) -> Any:
        """Get a collection object."""
        return self._db[collection]

    # Insert operations

    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        """Insert a single document.

        Args:
            collection: Collection name.
            document: Document to insert.

        Returns:
            Inserted document ID as string.
        """
        coll = self._get_collection(collection)
        result = await coll.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection: str, documents: Sequence[dict[str, Any]]) -> list[str]:
        """Insert multiple documents.

        Args:
            collection: Collection name.
            documents: Documents to insert.

        Returns:
            List of inserted document IDs.
        """
        coll = self._get_collection(collection)
        result = await coll.insert_many(list(documents))
        return [str(id_) for id_ in result.inserted_ids]

    # Find operations

    async def find_one(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Find a single document.

        Args:
            collection: Collection name.
            filter: Query filter.
            projection: Fields to include/exclude.

        Returns:
            Document or None if not found.
        """
        coll = self._get_collection(collection)
        return await coll.find_one(filter, projection)

    async def find(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
        sort: Optional[list[tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Find documents matching a filter.

        Args:
            collection: Collection name.
            filter: Query filter.
            projection: Fields to include/exclude.
            sort: Sort specification [(field, direction), ...].
            skip: Number of documents to skip.
            limit: Maximum documents to return (0 = no limit).

        Returns:
            List of matching documents.
        """
        coll = self._get_collection(collection)
        cursor = coll.find(filter, projection)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return await cursor.to_list(length=limit if limit else None)

    async def find_by_id(
        self,
        collection: str,
        id: str,
        projection: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Find a document by ID.

        Args:
            collection: Collection name.
            id: Document ID.
            projection: Fields to include/exclude.

        Returns:
            Document or None if not found.
        """
        from bson import ObjectId

        return await self.find_one(collection, {"_id": ObjectId(id)}, projection)

    # Update operations

    async def update_one(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update a single document.

        Args:
            collection: Collection name.
            filter: Query filter.
            update: Update operations.
            upsert: Insert if not found.

        Returns:
            Update result with counts.
        """
        coll = self._get_collection(collection)
        result = await coll.update_one(filter, update, upsert=upsert)
        return UpdateResult(
            matched_count=result.matched_count,
            modified_count=result.modified_count,
            upserted_id=str(result.upserted_id) if result.upserted_id else None,
        )

    async def update_many(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update multiple documents.

        Args:
            collection: Collection name.
            filter: Query filter.
            update: Update operations.
            upsert: Insert if not found.

        Returns:
            Update result with counts.
        """
        coll = self._get_collection(collection)
        result = await coll.update_many(filter, update, upsert=upsert)
        return UpdateResult(
            matched_count=result.matched_count,
            modified_count=result.modified_count,
            upserted_id=str(result.upserted_id) if result.upserted_id else None,
        )

    async def replace_one(
        self,
        collection: str,
        filter: dict[str, Any],
        replacement: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Replace a single document.

        Args:
            collection: Collection name.
            filter: Query filter.
            replacement: New document.
            upsert: Insert if not found.

        Returns:
            Update result with counts.
        """
        coll = self._get_collection(collection)
        result = await coll.replace_one(filter, replacement, upsert=upsert)
        return UpdateResult(
            matched_count=result.matched_count,
            modified_count=result.modified_count,
            upserted_id=str(result.upserted_id) if result.upserted_id else None,
        )

    # Delete operations

    async def delete_one(self, collection: str, filter: dict[str, Any]) -> DeleteResult:
        """Delete a single document.

        Args:
            collection: Collection name.
            filter: Query filter.

        Returns:
            Delete result with count.
        """
        coll = self._get_collection(collection)
        result = await coll.delete_one(filter)
        return DeleteResult(deleted_count=result.deleted_count)

    async def delete_many(self, collection: str, filter: dict[str, Any]) -> DeleteResult:
        """Delete multiple documents.

        Args:
            collection: Collection name.
            filter: Query filter.

        Returns:
            Delete result with count.
        """
        coll = self._get_collection(collection)
        result = await coll.delete_many(filter)
        return DeleteResult(deleted_count=result.deleted_count)

    async def delete_by_id(self, collection: str, id: str) -> DeleteResult:
        """Delete a document by ID.

        Args:
            collection: Collection name.
            id: Document ID.

        Returns:
            Delete result with count.
        """
        from bson import ObjectId

        return await self.delete_one(collection, {"_id": ObjectId(id)})

    # Aggregation

    async def aggregate(
        self,
        collection: str,
        pipeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run an aggregation pipeline.

        Args:
            collection: Collection name.
            pipeline: Aggregation pipeline stages.

        Returns:
            List of aggregation results.
        """
        coll = self._get_collection(collection)
        cursor = coll.aggregate(pipeline)
        return await cursor.to_list(length=None)

    # Count operations

    async def count_documents(
        self,
        collection: str,
        filter: Optional[dict[str, Any]] = None,
    ) -> int:
        """Count documents matching a filter.

        Args:
            collection: Collection name.
            filter: Query filter (empty for all).

        Returns:
            Number of matching documents.
        """
        coll = self._get_collection(collection)
        return await coll.count_documents(filter or {})

    async def estimated_document_count(self, collection: str) -> int:
        """Get estimated document count (faster than count_documents).

        Args:
            collection: Collection name.

        Returns:
            Estimated number of documents.
        """
        coll = self._get_collection(collection)
        return await coll.estimated_document_count()

    # Index operations

    async def create_index(
        self,
        collection: str,
        keys: list[tuple[str, int]],
        unique: bool = False,
        name: Optional[str] = None,
    ) -> str:
        """Create an index.

        Args:
            collection: Collection name.
            keys: Index keys [(field, direction), ...].
            unique: Unique index.
            name: Index name.

        Returns:
            Created index name.
        """
        coll = self._get_collection(collection)
        return await coll.create_index(keys, unique=unique, name=name)

    async def drop_index(self, collection: str, name: str) -> None:
        """Drop an index.

        Args:
            collection: Collection name.
            name: Index name.
        """
        coll = self._get_collection(collection)
        await coll.drop_index(name)

    async def list_indexes(self, collection: str) -> list[dict[str, Any]]:
        """List all indexes on a collection.

        Args:
            collection: Collection name.

        Returns:
            List of index specifications.
        """
        coll = self._get_collection(collection)
        cursor = coll.list_indexes()
        return await cursor.to_list(length=None)

    # Collection operations

    async def list_collections(self) -> list[str]:
        """List all collections in the database.

        Returns:
            List of collection names.
        """
        return await self._db.list_collection_names()

    async def create_collection(self, name: str) -> None:
        """Create a new collection.

        Args:
            name: Collection name.
        """
        await self._db.create_collection(name)

    async def drop_collection(self, name: str) -> None:
        """Drop a collection.

        Args:
            name: Collection name.
        """
        await self._db.drop_collection(name)

    # Database operations

    def use_database(self, name: str) -> None:
        """Switch to a different database.

        Args:
            name: Database name.
        """
        self._db = self._client[name]

    async def list_databases(self) -> list[str]:
        """List all databases.

        Returns:
            List of database names.
        """
        return await self._client.list_database_names()

    async def __aenter__(self) -> DocumentDBClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
