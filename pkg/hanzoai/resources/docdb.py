# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, cast

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven, FileTypes
from .._utils import extract_files, deepcopy_minimal
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["DocDBResource", "AsyncDocDBResource"]


class DocDBResource(SyncAPIResource):
    """Document database service backed by FerretDB + PostgreSQL.

    Manages document stores, files, vectors, and tree-structured documents
    via the Hanzo Cloud API.
    """

    @cached_property
    def with_raw_response(self) -> DocDBResourceWithRawResponse:
        return DocDBResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DocDBResourceWithStreamingResponse:
        return DocDBResourceWithStreamingResponse(self)

    # ── Stores ────────────────────────────────────────────────────────────

    def list_stores(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all document stores.

        Args:
          owner: Filter stores by owner.
        """
        return self._get(
            "/docdb/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def create_store(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        owner: str | NotGiven = NOT_GIVEN,
        tenant: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new document store.

        Args:
          name: Store name.
          description: Optional store description.
          owner: Owner identifier.
          tenant: Tenant identifier for multi-tenancy.
        """
        return self._post(
            "/docdb/stores",
            body={
                "name": name,
                "description": description,
                "owner": owner,
                "tenant": tenant,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_store(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific document store.

        Args:
          store_id: The store ID.
        """
        return self._get(
            f"/docdb/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_store(
        self,
        store_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update store metadata.

        Args:
          store_id: The store ID.
          name: New store name.
          description: New store description.
        """
        return self._post(
            f"/docdb/stores/{store_id}",
            body={"name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_store(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a document store.

        Args:
          store_id: The store ID.
        """
        return self._delete(
            f"/docdb/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Files / Documents ─────────────────────────────────────────────────

    def list_files(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List files in a document store.

        Args:
          store_id: The store ID.
        """
        return self._get(
            f"/docdb/stores/{store_id}/files",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_file(
        self,
        store_id: str,
        *,
        name: str,
        content: str,
        type: str | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a file/document to a store.

        Args:
          store_id: The store ID.
          name: File name.
          content: File content.
          type: File type/mime.
          metadata: Arbitrary metadata dict.
        """
        return self._post(
            f"/docdb/stores/{store_id}/files",
            body={
                "name": name,
                "content": content,
                "type": type,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_file(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific file.

        Args:
          file_id: The file ID.
        """
        return self._get(
            f"/docdb/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_file(
        self,
        file_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        content: str | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update file metadata or content.

        Args:
          file_id: The file ID.
          name: New file name.
          content: New file content.
          metadata: Updated metadata dict.
        """
        return self._post(
            f"/docdb/files/{file_id}",
            body={"name": name, "content": content, "metadata": metadata},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_file(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a file.

        Args:
          file_id: The file ID.
        """
        return self._delete(
            f"/docdb/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def upload_file(
        self,
        store_id: str,
        *,
        file: FileTypes,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Upload a file to a store via multipart form data.

        Args:
          store_id: The store ID.
          file: The file to upload.
          metadata: Optional metadata dict.
        """
        body = deepcopy_minimal({"file": file, "metadata": metadata})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            f"/docdb/stores/{store_id}/upload",
            body=body,
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Vectors ───────────────────────────────────────────────────────────

    def list_vectors(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List vectors for a store.

        Args:
          store_id: The store ID.
        """
        return self._get(
            f"/docdb/stores/{store_id}/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_vector(
        self,
        store_id: str,
        *,
        file_id: str,
        content: str,
        embedding: List[float] | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a vector to a store.

        Args:
          store_id: The store ID.
          file_id: The associated file ID.
          content: Text content for the vector.
          embedding: Pre-computed embedding. If omitted, the server will generate one.
          metadata: Arbitrary metadata dict.
        """
        return self._post(
            f"/docdb/stores/{store_id}/vectors",
            body={
                "file_id": file_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_vector(
        self,
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vector.

        Args:
          vector_id: The vector ID.
        """
        return self._delete(
            f"/docdb/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def refresh_vectors(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Re-embed all vectors in a store.

        Args:
          store_id: The store ID.
        """
        return self._post(
            f"/docdb/stores/{store_id}/vectors/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Tree Files ────────────────────────────────────────────────────────

    def list_tree_files(
        self,
        store_id: str,
        *,
        parent_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List tree-structured files in a store.

        Args:
          store_id: The store ID.
          parent_id: Filter by parent node ID.
        """
        return self._get(
            f"/docdb/stores/{store_id}/tree",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"parent_id": parent_id},
            ),
            cast_to=object,
        )

    def create_tree_file(
        self,
        store_id: str,
        *,
        name: str,
        parent_id: str | NotGiven = NOT_GIVEN,
        content: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a tree node to a store.

        Args:
          store_id: The store ID.
          name: Node name.
          parent_id: Parent node ID. Omit for root-level nodes.
          content: Node content.
        """
        return self._post(
            f"/docdb/stores/{store_id}/tree",
            body={"name": name, "parent_id": parent_id, "content": content},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncDocDBResource(AsyncAPIResource):
    """Document database service backed by FerretDB + PostgreSQL (async).

    Manages document stores, files, vectors, and tree-structured documents
    via the Hanzo Cloud API.
    """

    @cached_property
    def with_raw_response(self) -> AsyncDocDBResourceWithRawResponse:
        return AsyncDocDBResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDocDBResourceWithStreamingResponse:
        return AsyncDocDBResourceWithStreamingResponse(self)

    # ── Stores ────────────────────────────────────────────────────────────

    async def list_stores(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all document stores."""
        return await self._get(
            "/docdb/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def create_store(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        owner: str | NotGiven = NOT_GIVEN,
        tenant: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new document store."""
        return await self._post(
            "/docdb/stores",
            body={
                "name": name,
                "description": description,
                "owner": owner,
                "tenant": tenant,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_store(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific document store."""
        return await self._get(
            f"/docdb/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_store(
        self,
        store_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update store metadata."""
        return await self._post(
            f"/docdb/stores/{store_id}",
            body={"name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_store(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a document store."""
        return await self._delete(
            f"/docdb/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Files / Documents ─────────────────────────────────────────────────

    async def list_files(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List files in a document store."""
        return await self._get(
            f"/docdb/stores/{store_id}/files",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_file(
        self,
        store_id: str,
        *,
        name: str,
        content: str,
        type: str | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a file/document to a store."""
        return await self._post(
            f"/docdb/stores/{store_id}/files",
            body={
                "name": name,
                "content": content,
                "type": type,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_file(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific file."""
        return await self._get(
            f"/docdb/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_file(
        self,
        file_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        content: str | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update file metadata or content."""
        return await self._post(
            f"/docdb/files/{file_id}",
            body={"name": name, "content": content, "metadata": metadata},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_file(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a file."""
        return await self._delete(
            f"/docdb/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def upload_file(
        self,
        store_id: str,
        *,
        file: FileTypes,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Upload a file to a store via multipart form data."""
        body = deepcopy_minimal({"file": file, "metadata": metadata})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            f"/docdb/stores/{store_id}/upload",
            body=body,
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Vectors ───────────────────────────────────────────────────────────

    async def list_vectors(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List vectors for a store."""
        return await self._get(
            f"/docdb/stores/{store_id}/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_vector(
        self,
        store_id: str,
        *,
        file_id: str,
        content: str,
        embedding: List[float] | NotGiven = NOT_GIVEN,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a vector to a store."""
        return await self._post(
            f"/docdb/stores/{store_id}/vectors",
            body={
                "file_id": file_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_vector(
        self,
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vector."""
        return await self._delete(
            f"/docdb/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def refresh_vectors(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Re-embed all vectors in a store."""
        return await self._post(
            f"/docdb/stores/{store_id}/vectors/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Tree Files ────────────────────────────────────────────────────────

    async def list_tree_files(
        self,
        store_id: str,
        *,
        parent_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List tree-structured files in a store."""
        return await self._get(
            f"/docdb/stores/{store_id}/tree",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"parent_id": parent_id},
            ),
            cast_to=object,
        )

    async def create_tree_file(
        self,
        store_id: str,
        *,
        name: str,
        parent_id: str | NotGiven = NOT_GIVEN,
        content: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a tree node to a store."""
        return await self._post(
            f"/docdb/stores/{store_id}/tree",
            body={"name": name, "parent_id": parent_id, "content": content},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class DocDBResourceWithRawResponse:
    def __init__(self, docdb: DocDBResource) -> None:
        self._docdb = docdb
        # Stores
        self.list_stores = to_raw_response_wrapper(docdb.list_stores)
        self.create_store = to_raw_response_wrapper(docdb.create_store)
        self.retrieve_store = to_raw_response_wrapper(docdb.retrieve_store)
        self.update_store = to_raw_response_wrapper(docdb.update_store)
        self.delete_store = to_raw_response_wrapper(docdb.delete_store)
        # Files
        self.list_files = to_raw_response_wrapper(docdb.list_files)
        self.create_file = to_raw_response_wrapper(docdb.create_file)
        self.retrieve_file = to_raw_response_wrapper(docdb.retrieve_file)
        self.update_file = to_raw_response_wrapper(docdb.update_file)
        self.delete_file = to_raw_response_wrapper(docdb.delete_file)
        self.upload_file = to_raw_response_wrapper(docdb.upload_file)
        # Vectors
        self.list_vectors = to_raw_response_wrapper(docdb.list_vectors)
        self.create_vector = to_raw_response_wrapper(docdb.create_vector)
        self.delete_vector = to_raw_response_wrapper(docdb.delete_vector)
        self.refresh_vectors = to_raw_response_wrapper(docdb.refresh_vectors)
        # Tree
        self.list_tree_files = to_raw_response_wrapper(docdb.list_tree_files)
        self.create_tree_file = to_raw_response_wrapper(docdb.create_tree_file)


class AsyncDocDBResourceWithRawResponse:
    def __init__(self, docdb: AsyncDocDBResource) -> None:
        self._docdb = docdb
        # Stores
        self.list_stores = async_to_raw_response_wrapper(docdb.list_stores)
        self.create_store = async_to_raw_response_wrapper(docdb.create_store)
        self.retrieve_store = async_to_raw_response_wrapper(docdb.retrieve_store)
        self.update_store = async_to_raw_response_wrapper(docdb.update_store)
        self.delete_store = async_to_raw_response_wrapper(docdb.delete_store)
        # Files
        self.list_files = async_to_raw_response_wrapper(docdb.list_files)
        self.create_file = async_to_raw_response_wrapper(docdb.create_file)
        self.retrieve_file = async_to_raw_response_wrapper(docdb.retrieve_file)
        self.update_file = async_to_raw_response_wrapper(docdb.update_file)
        self.delete_file = async_to_raw_response_wrapper(docdb.delete_file)
        self.upload_file = async_to_raw_response_wrapper(docdb.upload_file)
        # Vectors
        self.list_vectors = async_to_raw_response_wrapper(docdb.list_vectors)
        self.create_vector = async_to_raw_response_wrapper(docdb.create_vector)
        self.delete_vector = async_to_raw_response_wrapper(docdb.delete_vector)
        self.refresh_vectors = async_to_raw_response_wrapper(docdb.refresh_vectors)
        # Tree
        self.list_tree_files = async_to_raw_response_wrapper(docdb.list_tree_files)
        self.create_tree_file = async_to_raw_response_wrapper(docdb.create_tree_file)


class DocDBResourceWithStreamingResponse:
    def __init__(self, docdb: DocDBResource) -> None:
        self._docdb = docdb
        # Stores
        self.list_stores = to_streamed_response_wrapper(docdb.list_stores)
        self.create_store = to_streamed_response_wrapper(docdb.create_store)
        self.retrieve_store = to_streamed_response_wrapper(docdb.retrieve_store)
        self.update_store = to_streamed_response_wrapper(docdb.update_store)
        self.delete_store = to_streamed_response_wrapper(docdb.delete_store)
        # Files
        self.list_files = to_streamed_response_wrapper(docdb.list_files)
        self.create_file = to_streamed_response_wrapper(docdb.create_file)
        self.retrieve_file = to_streamed_response_wrapper(docdb.retrieve_file)
        self.update_file = to_streamed_response_wrapper(docdb.update_file)
        self.delete_file = to_streamed_response_wrapper(docdb.delete_file)
        self.upload_file = to_streamed_response_wrapper(docdb.upload_file)
        # Vectors
        self.list_vectors = to_streamed_response_wrapper(docdb.list_vectors)
        self.create_vector = to_streamed_response_wrapper(docdb.create_vector)
        self.delete_vector = to_streamed_response_wrapper(docdb.delete_vector)
        self.refresh_vectors = to_streamed_response_wrapper(docdb.refresh_vectors)
        # Tree
        self.list_tree_files = to_streamed_response_wrapper(docdb.list_tree_files)
        self.create_tree_file = to_streamed_response_wrapper(docdb.create_tree_file)


class AsyncDocDBResourceWithStreamingResponse:
    def __init__(self, docdb: AsyncDocDBResource) -> None:
        self._docdb = docdb
        # Stores
        self.list_stores = async_to_streamed_response_wrapper(docdb.list_stores)
        self.create_store = async_to_streamed_response_wrapper(docdb.create_store)
        self.retrieve_store = async_to_streamed_response_wrapper(docdb.retrieve_store)
        self.update_store = async_to_streamed_response_wrapper(docdb.update_store)
        self.delete_store = async_to_streamed_response_wrapper(docdb.delete_store)
        # Files
        self.list_files = async_to_streamed_response_wrapper(docdb.list_files)
        self.create_file = async_to_streamed_response_wrapper(docdb.create_file)
        self.retrieve_file = async_to_streamed_response_wrapper(docdb.retrieve_file)
        self.update_file = async_to_streamed_response_wrapper(docdb.update_file)
        self.delete_file = async_to_streamed_response_wrapper(docdb.delete_file)
        self.upload_file = async_to_streamed_response_wrapper(docdb.upload_file)
        # Vectors
        self.list_vectors = async_to_streamed_response_wrapper(docdb.list_vectors)
        self.create_vector = async_to_streamed_response_wrapper(docdb.create_vector)
        self.delete_vector = async_to_streamed_response_wrapper(docdb.delete_vector)
        self.refresh_vectors = async_to_streamed_response_wrapper(docdb.refresh_vectors)
        # Tree
        self.list_tree_files = async_to_streamed_response_wrapper(docdb.list_tree_files)
        self.create_tree_file = async_to_streamed_response_wrapper(docdb.create_tree_file)
