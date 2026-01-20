"""Meilisearch client wrapper for Hanzo infrastructure.

Provides async interface to Meilisearch for full-text search
with typo tolerance, filtering, and faceted search.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field


class SearchConfig(BaseModel):
    """Configuration for Meilisearch connection."""

    host: str = Field(default="localhost", description="Meilisearch server host")
    port: int = Field(default=7700, description="Meilisearch server port")
    api_key: Optional[str] = Field(default=None, description="Master or API key")
    url: Optional[str] = Field(default=None, description="Full URL (overrides host/port)")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    ssl: bool = Field(default=False, description="Use HTTPS")

    @classmethod
    def from_env(cls) -> SearchConfig:
        """Create config from environment variables.

        Environment variables:
            MEILISEARCH_HOST: Server host (default: localhost)
            MEILISEARCH_PORT: Server port (default: 7700)
            MEILISEARCH_API_KEY: API key for authentication
            MEILISEARCH_URL: Full URL (overrides host/port)
            MEILISEARCH_SSL: Use HTTPS (default: false)
        """
        return cls(
            host=os.getenv("MEILISEARCH_HOST", "localhost"),
            port=int(os.getenv("MEILISEARCH_PORT", "7700")),
            api_key=os.getenv("MEILISEARCH_API_KEY") or os.getenv("MEILI_MASTER_KEY"),
            url=os.getenv("MEILISEARCH_URL"),
            ssl=os.getenv("MEILISEARCH_SSL", "").lower() in ("true", "1", "yes"),
        )

    @property
    def effective_url(self) -> str:
        """Get the effective URL to connect to."""
        if self.url:
            return self.url
        protocol = "https" if self.ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


@dataclass
class SearchHit:
    """A single search result."""

    id: str
    document: dict[str, Any]
    score: Optional[float] = None
    highlights: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Result of a search query."""

    hits: list[SearchHit]
    query: str
    processing_time_ms: int
    total_hits: int
    offset: int = 0
    limit: int = 20
    facet_distribution: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class IndexStats:
    """Statistics for an index."""

    number_of_documents: int
    is_indexing: bool
    field_distribution: dict[str, int] = field(default_factory=dict)


class SearchClient:
    """Async client for Meilisearch full-text search.

    Wraps meilisearch-python-sdk with async methods and Hanzo conventions.

    Example:
        ```python
        client = SearchClient(SearchConfig.from_env())
        await client.connect()

        # Create index
        await client.create_index("products", primary_key="id")

        # Add documents
        docs = [{"id": "1", "name": "Widget", "price": 99}]
        await client.add_documents("products", docs)

        # Search
        results = await client.search("products", "widget", filters="price > 50")
        for hit in results.hits:
            print(hit.document["name"])
        ```
    """

    def __init__(self, config: Optional[SearchConfig] = None) -> None:
        """Initialize search client.

        Args:
            config: Meilisearch configuration. If None, loads from environment.
        """
        self.config = config or SearchConfig.from_env()
        self._client: Any = None

    async def connect(self) -> None:
        """Establish connection to Meilisearch server."""
        try:
            from meilisearch_python_sdk import AsyncClient
        except ImportError as e:
            raise ImportError(
                "meilisearch-python-sdk is required for SearchClient. "
                "Install with: pip install meilisearch-python-sdk"
            ) from e

        self._client = AsyncClient(
            self.config.effective_url,
            api_key=self.config.api_key,
            timeout=int(self.config.timeout),
        )

    async def close(self) -> None:
        """Close the connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if Meilisearch server is healthy.

        Returns:
            True if server is reachable and healthy.
        """
        if not self._client:
            return False
        try:
            health = await self._client.health()
            return health.status == "available"
        except Exception:
            return False

    # Index operations

    async def create_index(
        self,
        name: str,
        primary_key: Optional[str] = None,
    ) -> None:
        """Create a new index.

        Args:
            name: Index name (uid).
            primary_key: Document primary key field.
        """
        task = await self._client.create_index(uid=name, primary_key=primary_key)
        await self._client.wait_for_task(task.task_uid)

    async def delete_index(self, name: str) -> None:
        """Delete an index.

        Args:
            name: Index name to delete.
        """
        task = await self._client.index(name).delete()
        await self._client.wait_for_task(task.task_uid)

    async def index_exists(self, name: str) -> bool:
        """Check if an index exists.

        Args:
            name: Index name.

        Returns:
            True if index exists.
        """
        try:
            await self._client.get_index(name)
            return True
        except Exception:
            return False

    async def list_indexes(self) -> list[str]:
        """List all indexes.

        Returns:
            List of index names.
        """
        indexes = await self._client.get_indexes()
        return [idx.uid for idx in indexes]

    async def get_index_stats(self, name: str) -> IndexStats:
        """Get statistics for an index.

        Args:
            name: Index name.

        Returns:
            Index statistics.
        """
        index = self._client.index(name)
        stats = await index.get_stats()
        return IndexStats(
            number_of_documents=stats.number_of_documents,
            is_indexing=stats.is_indexing,
            field_distribution=stats.field_distribution or {},
        )

    # Document operations

    async def add_documents(
        self,
        index: str,
        documents: Sequence[dict[str, Any]],
        primary_key: Optional[str] = None,
    ) -> None:
        """Add or update documents.

        Args:
            index: Index name.
            documents: Documents to add.
            primary_key: Override primary key for this operation.
        """
        idx = self._client.index(index)
        task = await idx.add_documents(list(documents), primary_key=primary_key)
        await self._client.wait_for_task(task.task_uid)

    async def update_documents(
        self,
        index: str,
        documents: Sequence[dict[str, Any]],
        primary_key: Optional[str] = None,
    ) -> None:
        """Update documents (partial update).

        Args:
            index: Index name.
            documents: Documents with updates.
            primary_key: Override primary key for this operation.
        """
        idx = self._client.index(index)
        task = await idx.update_documents(list(documents), primary_key=primary_key)
        await self._client.wait_for_task(task.task_uid)

    async def delete_document(self, index: str, document_id: str) -> None:
        """Delete a document by ID.

        Args:
            index: Index name.
            document_id: Document ID to delete.
        """
        idx = self._client.index(index)
        task = await idx.delete_document(document_id)
        await self._client.wait_for_task(task.task_uid)

    async def delete_documents(self, index: str, document_ids: list[str]) -> None:
        """Delete multiple documents by ID.

        Args:
            index: Index name.
            document_ids: Document IDs to delete.
        """
        idx = self._client.index(index)
        task = await idx.delete_documents(document_ids)
        await self._client.wait_for_task(task.task_uid)

    async def delete_all_documents(self, index: str) -> None:
        """Delete all documents in an index.

        Args:
            index: Index name.
        """
        idx = self._client.index(index)
        task = await idx.delete_all_documents()
        await self._client.wait_for_task(task.task_uid)

    async def get_document(
        self,
        index: str,
        document_id: str,
        fields: Optional[list[str]] = None,
    ) -> Optional[dict[str, Any]]:
        """Get a document by ID.

        Args:
            index: Index name.
            document_id: Document ID.
            fields: Fields to retrieve (all if not specified).

        Returns:
            Document or None if not found.
        """
        idx = self._client.index(index)
        try:
            return await idx.get_document(document_id, fields=fields)
        except Exception:
            return None

    async def get_documents(
        self,
        index: str,
        offset: int = 0,
        limit: int = 20,
        fields: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Get documents from an index.

        Args:
            index: Index name.
            offset: Number of documents to skip.
            limit: Maximum documents to return.
            fields: Fields to retrieve (all if not specified).

        Returns:
            List of documents.
        """
        idx = self._client.index(index)
        result = await idx.get_documents(offset=offset, limit=limit, fields=fields)
        return result.results

    # Search operations

    async def search(
        self,
        index: str,
        query: str,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[str] = None,
        facets: Optional[list[str]] = None,
        attributes_to_retrieve: Optional[list[str]] = None,
        attributes_to_highlight: Optional[list[str]] = None,
        sort: Optional[list[str]] = None,
        show_matches_position: bool = False,
        show_ranking_score: bool = False,
    ) -> SearchResult:
        """Search documents in an index.

        Args:
            index: Index name.
            query: Search query.
            offset: Number of results to skip.
            limit: Maximum results to return.
            filters: Filter expression (e.g., "price > 50 AND category = 'tech'").
            facets: Fields to get facet distribution for.
            attributes_to_retrieve: Fields to include in results.
            attributes_to_highlight: Fields to highlight matches in.
            sort: Sort expressions (e.g., ["price:asc", "name:desc"]).
            show_matches_position: Include match positions.
            show_ranking_score: Include ranking score.

        Returns:
            Search results with hits and metadata.
        """
        idx = self._client.index(index)
        result = await idx.search(
            query,
            offset=offset,
            limit=limit,
            filter=filters,
            facets=facets,
            attributes_to_retrieve=attributes_to_retrieve,
            attributes_to_highlight=attributes_to_highlight,
            sort=sort,
            show_matches_position=show_matches_position,
            show_ranking_score=show_ranking_score,
        )

        hits = []
        for hit in result.hits:
            # Handle both dict and object responses
            if isinstance(hit, dict):
                doc = hit
                formatted = hit.get("_formatted", {})
                score = hit.get("_rankingScore")
            else:
                doc = hit.__dict__ if hasattr(hit, "__dict__") else {}
                formatted = getattr(hit, "_formatted", {}) or {}
                score = getattr(hit, "_rankingScore", None)

            # Extract ID from document
            doc_id = doc.get("id") or doc.get("_id") or str(hash(str(doc)))

            hits.append(SearchHit(
                id=str(doc_id),
                document=doc,
                score=score,
                highlights=formatted,
            ))

        return SearchResult(
            hits=hits,
            query=query,
            processing_time_ms=result.processing_time_ms,
            total_hits=result.estimated_total_hits or len(hits),
            offset=offset,
            limit=limit,
            facet_distribution=result.facet_distribution or {},
        )

    # Settings operations

    async def get_settings(self, index: str) -> dict[str, Any]:
        """Get index settings.

        Args:
            index: Index name.

        Returns:
            Current settings.
        """
        idx = self._client.index(index)
        settings = await idx.get_settings()
        return settings.__dict__ if hasattr(settings, "__dict__") else dict(settings)

    async def update_settings(
        self,
        index: str,
        settings: dict[str, Any],
    ) -> None:
        """Update index settings.

        Args:
            index: Index name.
            settings: Settings to update.
        """
        idx = self._client.index(index)
        task = await idx.update_settings(settings)
        await self._client.wait_for_task(task.task_uid)

    async def update_searchable_attributes(
        self,
        index: str,
        attributes: list[str],
    ) -> None:
        """Set searchable attributes.

        Args:
            index: Index name.
            attributes: Ordered list of searchable attributes.
        """
        idx = self._client.index(index)
        task = await idx.update_searchable_attributes(attributes)
        await self._client.wait_for_task(task.task_uid)

    async def update_filterable_attributes(
        self,
        index: str,
        attributes: list[str],
    ) -> None:
        """Set filterable attributes.

        Args:
            index: Index name.
            attributes: List of filterable attributes.
        """
        idx = self._client.index(index)
        task = await idx.update_filterable_attributes(attributes)
        await self._client.wait_for_task(task.task_uid)

    async def update_sortable_attributes(
        self,
        index: str,
        attributes: list[str],
    ) -> None:
        """Set sortable attributes.

        Args:
            index: Index name.
            attributes: List of sortable attributes.
        """
        idx = self._client.index(index)
        task = await idx.update_sortable_attributes(attributes)
        await self._client.wait_for_task(task.task_uid)

    async def update_ranking_rules(
        self,
        index: str,
        rules: list[str],
    ) -> None:
        """Set ranking rules.

        Args:
            index: Index name.
            rules: Ordered list of ranking rules.
        """
        idx = self._client.index(index)
        task = await idx.update_ranking_rules(rules)
        await self._client.wait_for_task(task.task_uid)

    async def __aenter__(self) -> SearchClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
