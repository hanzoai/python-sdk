"""Qdrant vector database client wrapper for Hanzo infrastructure.

Provides async interface to Qdrant for vector similarity search,
supporting both cloud and local deployments.
"""

from __future__ import annotations

import os
from typing import Any, Optional, Sequence
from dataclasses import field, dataclass

from pydantic import Field, BaseModel


class VectorConfig(BaseModel):
    """Configuration for Qdrant vector database connection."""

    host: str = Field(default="localhost", description="Qdrant server host")
    port: int = Field(default=6333, description="Qdrant REST API port")
    grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    api_key: Optional[str] = Field(default=None, description="API key for Qdrant Cloud")
    url: Optional[str] = Field(
        default=None, description="Full URL (overrides host/port)"
    )
    https: bool = Field(default=False, description="Use HTTPS")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    prefer_grpc: bool = Field(default=True, description="Prefer gRPC over REST")

    @classmethod
    def from_env(cls) -> VectorConfig:
        """Create config from environment variables.

        Environment variables:
            QDRANT_HOST: Server host (default: localhost)
            QDRANT_PORT: REST API port (default: 6333)
            QDRANT_GRPC_PORT: gRPC port (default: 6334)
            QDRANT_API_KEY: API key for authentication
            QDRANT_URL: Full URL (overrides host/port)
            QDRANT_HTTPS: Use HTTPS (default: false)
        """
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            grpc_port=int(os.getenv("QDRANT_GRPC_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            url=os.getenv("QDRANT_URL"),
            https=os.getenv("QDRANT_HTTPS", "").lower() in ("true", "1", "yes"),
        )


@dataclass
class VectorPoint:
    """A point in vector space with optional payload."""

    id: str | int
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredPoint:
    """A search result with similarity score."""

    id: str | int
    score: float
    payload: dict[str, Any] = field(default_factory=dict)
    vector: Optional[list[float]] = None


class VectorClient:
    """Async client for Qdrant vector database.

    Wraps qdrant-client with async methods and Hanzo conventions.

    Example:
        ```python
        client = VectorClient(VectorConfig.from_env())
        await client.connect()

        # Create collection
        await client.create_collection("embeddings", vector_size=1536)

        # Upsert vectors
        points = [VectorPoint(id="doc1", vector=[0.1] * 1536, payload={"text": "hello"})]
        await client.upsert("embeddings", points)

        # Search
        results = await client.search("embeddings", query_vector=[0.1] * 1536, limit=10)
        ```
    """

    def __init__(self, config: Optional[VectorConfig] = None) -> None:
        """Initialize vector client.

        Args:
            config: Qdrant configuration. If None, loads from environment.
        """
        self.config = config or VectorConfig.from_env()
        self._client: Any = None
        self._async_client: Any = None

    async def connect(self) -> None:
        """Establish connection to Qdrant server."""
        try:
            from qdrant_client import AsyncQdrantClient
        except ImportError as e:
            raise ImportError(
                "qdrant-client is required for VectorClient. Install with: pip install qdrant-client"
            ) from e

        if self.config.url:
            self._async_client = AsyncQdrantClient(
                url=self.config.url,
                api_key=self.config.api_key,
                timeout=self.config.timeout,
                prefer_grpc=self.config.prefer_grpc,
            )
        else:
            self._async_client = AsyncQdrantClient(
                host=self.config.host,
                port=self.config.port,
                grpc_port=self.config.grpc_port,
                api_key=self.config.api_key,
                https=self.config.https,
                timeout=self.config.timeout,
                prefer_grpc=self.config.prefer_grpc,
            )

    async def close(self) -> None:
        """Close the connection."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None

    async def health_check(self) -> bool:
        """Check if Qdrant server is healthy.

        Returns:
            True if server is reachable and healthy.
        """
        if not self._async_client:
            return False
        try:
            await self._async_client.get_collections()
            return True
        except Exception:
            return False

    async def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "Cosine",
        on_disk: bool = False,
    ) -> None:
        """Create a new collection.

        Args:
            name: Collection name.
            vector_size: Dimension of vectors.
            distance: Distance metric (Cosine, Euclid, Dot).
            on_disk: Store vectors on disk instead of RAM.
        """
        from qdrant_client.models import Distance, VectorParams

        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT,
        }

        await self._async_client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance_map.get(distance, Distance.COSINE),
                on_disk=on_disk,
            ),
        )

    async def delete_collection(self, name: str) -> None:
        """Delete a collection.

        Args:
            name: Collection name to delete.
        """
        await self._async_client.delete_collection(collection_name=name)

    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Collection name.

        Returns:
            True if collection exists.
        """
        return await self._async_client.collection_exists(collection_name=name)

    async def list_collections(self) -> list[str]:
        """List all collections.

        Returns:
            List of collection names.
        """
        result = await self._async_client.get_collections()
        return [c.name for c in result.collections]

    async def upsert(
        self,
        collection: str,
        points: Sequence[VectorPoint],
    ) -> None:
        """Insert or update vectors.

        Args:
            collection: Collection name.
            points: Points to upsert.
        """
        from qdrant_client.models import PointStruct

        qdrant_points = [
            PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
        ]
        await self._async_client.upsert(
            collection_name=collection, points=qdrant_points
        )

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[dict[str, Any]] = None,
        with_vectors: bool = False,
    ) -> list[ScoredPoint]:
        """Search for similar vectors.

        Args:
            collection: Collection name.
            query_vector: Query vector.
            limit: Maximum results to return.
            score_threshold: Minimum similarity score.
            filter_conditions: Qdrant filter conditions.
            with_vectors: Include vectors in results.

        Returns:
            List of scored points sorted by similarity.
        """
        from qdrant_client.models import Filter

        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = Filter(**filter_conditions)

        results = await self._async_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_vectors=with_vectors,
        )

        return [
            ScoredPoint(
                id=r.id,
                score=r.score,
                payload=r.payload or {},
                vector=r.vector if with_vectors else None,
            )
            for r in results
        ]

    async def delete(
        self,
        collection: str,
        ids: Optional[Sequence[str | int]] = None,
        filter_conditions: Optional[dict[str, Any]] = None,
    ) -> None:
        """Delete vectors by ID or filter.

        Args:
            collection: Collection name.
            ids: Point IDs to delete.
            filter_conditions: Filter conditions for deletion.
        """
        from qdrant_client.models import Filter, PointIdsList

        if ids:
            await self._async_client.delete(
                collection_name=collection,
                points_selector=PointIdsList(points=list(ids)),
            )
        elif filter_conditions:
            await self._async_client.delete(
                collection_name=collection,
                points_selector=Filter(**filter_conditions),
            )

    async def get(
        self,
        collection: str,
        ids: Sequence[str | int],
        with_vectors: bool = False,
    ) -> list[VectorPoint]:
        """Retrieve vectors by ID.

        Args:
            collection: Collection name.
            ids: Point IDs to retrieve.
            with_vectors: Include vectors in results.

        Returns:
            List of retrieved points.
        """
        results = await self._async_client.retrieve(
            collection_name=collection,
            ids=list(ids),
            with_vectors=with_vectors,
        )

        return [
            VectorPoint(
                id=r.id,
                vector=r.vector if with_vectors and r.vector else [],
                payload=r.payload or {},
            )
            for r in results
        ]

    async def count(self, collection: str) -> int:
        """Count points in a collection.

        Args:
            collection: Collection name.

        Returns:
            Number of points.
        """
        info = await self._async_client.get_collection(collection_name=collection)
        return info.points_count or 0

    async def __aenter__(self) -> VectorClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
