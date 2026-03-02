# Hanzo AI SDK — Datastore (RAG Vector Store)

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

__all__ = ["DatastoreResource", "AsyncDatastoreResource"]


class DatastoreResource(SyncAPIResource):
    """RAG vector store service for semantic search over embedded documents.

    Manages stores (knowledge bases), files, vectors, and search queries
    against the Hanzo Cloud API backend.
    """

    @cached_property
    def with_raw_response(self) -> DatastoreResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return DatastoreResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DatastoreResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return DatastoreResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------
    # Store CRUD
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all stores, optionally filtered by owner or type.

        Args:
          owner: Filter stores by owner identifier.
          type: Filter stores by type.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        query_params: Dict[str, Any] = {}
        if not isinstance(owner, NotGiven):
            query_params["owner"] = owner
        if not isinstance(type, NotGiven):
            query_params["type"] = type
        return self._get(
            "/datastore/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query_params if query_params else None,
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        embedding_provider: str | NotGiven = NOT_GIVEN,
        embedding_model: str | NotGiven = NOT_GIVEN,
        dimension: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new store (knowledge base) for RAG.

        Args:
          name: Name of the store.
          description: Human-readable description.
          embedding_provider: Embedding provider (e.g. "OpenAI", "Cohere", "Jina").
          embedding_model: Model name for embedding generation.
          dimension: Embedding vector dimension.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        body: Dict[str, Any] = {"name": name}
        if not isinstance(description, NotGiven):
            body["description"] = description
        if not isinstance(embedding_provider, NotGiven):
            body["embeddingProvider"] = embedding_provider
        if not isinstance(embedding_model, NotGiven):
            body["embeddingModel"] = embedding_model
        if not isinstance(dimension, NotGiven):
            body["dimension"] = dimension
        return self._post(
            "/datastore/stores",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a store by ID.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return self._get(
            f"/datastore/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update(
        self,
        store_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        embedding_provider: str | NotGiven = NOT_GIVEN,
        embedding_model: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing store.

        Args:
          store_id: The store identifier.
          name: Updated name.
          description: Updated description.
          embedding_provider: Updated embedding provider.
          embedding_model: Updated embedding model.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {}
        if not isinstance(name, NotGiven):
            body["name"] = name
        if not isinstance(description, NotGiven):
            body["description"] = description
        if not isinstance(embedding_provider, NotGiven):
            body["embeddingProvider"] = embedding_provider
        if not isinstance(embedding_model, NotGiven):
            body["embeddingModel"] = embedding_model
        return self._post(
            f"/datastore/stores/{store_id}",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a store.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return self._delete(
            f"/datastore/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def list_files(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all files in a store.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return self._get(
            f"/datastore/stores/{store_id}/files",
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
        split_method: str | NotGiven = NOT_GIVEN,
        chunk_size: int | NotGiven = NOT_GIVEN,
        chunk_overlap: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a file (text content) to a store for chunking and embedding.

        Args:
          store_id: The store identifier.
          name: File name.
          content: Raw text content of the file.
          type: File/content type hint.
          split_method: How to split the document (e.g. "character", "token").
          chunk_size: Number of characters/tokens per chunk.
          chunk_overlap: Overlap between consecutive chunks.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "name": name,
            "content": content,
        }
        if not isinstance(type, NotGiven):
            body["type"] = type
        if not isinstance(split_method, NotGiven):
            body["splitMethod"] = split_method
        if not isinstance(chunk_size, NotGiven):
            body["chunkSize"] = chunk_size
        if not isinstance(chunk_overlap, NotGiven):
            body["chunkOverlap"] = chunk_overlap
        return self._post(
            f"/datastore/stores/{store_id}/files",
            body=body,
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
        """Get a file by ID.

        Args:
          file_id: The file identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._get(
            f"/datastore/files/{file_id}",
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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing file.

        Args:
          file_id: The file identifier.
          name: Updated file name.
          content: Updated text content.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        body: Dict[str, Any] = {}
        if not isinstance(name, NotGiven):
            body["name"] = name
        if not isinstance(content, NotGiven):
            body["content"] = content
        return self._post(
            f"/datastore/files/{file_id}",
            body=body,
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
          file_id: The file identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._delete(
            f"/datastore/files/{file_id}",
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
        split_method: str | NotGiven = NOT_GIVEN,
        chunk_size: int | NotGiven = NOT_GIVEN,
        chunk_overlap: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Upload a binary file (PDF, DOCX, etc.) to a store via multipart form.

        The backend parses the file, chunks it, and generates embeddings.

        Args:
          store_id: The store identifier.
          file: The file to upload (path, bytes, or file-like object).
          split_method: How to split the document (e.g. "character", "token").
          chunk_size: Number of characters/tokens per chunk.
          chunk_overlap: Overlap between consecutive chunks.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body = deepcopy_minimal(
            {
                "file": file,
                "store_id": store_id,
                "split_method": split_method,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            f"/datastore/stores/{store_id}/upload",
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

    # ------------------------------------------------------------------
    # Vector operations
    # ------------------------------------------------------------------

    def list_vectors(
        self,
        store_id: str,
        *,
        file_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List vectors in a store, optionally filtered by file.

        Args:
          store_id: The store identifier.
          file_id: Filter vectors by source file.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        query_params: Dict[str, Any] = {}
        if not isinstance(file_id, NotGiven):
            query_params["file_id"] = file_id
        return self._get(
            f"/datastore/stores/{store_id}/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query_params if query_params else None,
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
        """Manually add a vector to a store.

        Args:
          store_id: The store identifier.
          file_id: Source file identifier.
          content: Text content for this vector chunk.
          embedding: Pre-computed embedding vector (optional; backend can generate).
          metadata: Arbitrary metadata attached to the vector.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "file_id": file_id,
            "content": content,
        }
        if not isinstance(embedding, NotGiven):
            body["embedding"] = embedding
        if not isinstance(metadata, NotGiven):
            body["metadata"] = metadata
        return self._post(
            f"/datastore/stores/{store_id}/vectors",
            body=body,
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
        """Delete a vector by ID.

        Args:
          vector_id: The vector identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not vector_id:
            raise ValueError(f"Expected a non-empty value for `vector_id` but received {vector_id!r}")
        return self._delete(
            f"/datastore/vectors/{vector_id}",
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
        """Re-embed all documents in a store, regenerating all vectors.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return self._post(
            f"/datastore/stores/{store_id}/vectors/refresh",
            body={"store_id": store_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Search / Query
    # ------------------------------------------------------------------

    def query(
        self,
        store_id: str,
        *,
        query: str,
        top_k: int | NotGiven = NOT_GIVEN,
        score_threshold: float | NotGiven = NOT_GIVEN,
        filter: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Semantic vector search against a store.

        Args:
          store_id: The store identifier.
          query: Natural language query string.
          top_k: Maximum number of results to return.
          score_threshold: Minimum cosine similarity score (0.0-1.0).
          filter: Metadata filter object for narrowing results.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "query": query,
        }
        if not isinstance(top_k, NotGiven):
            body["topK"] = top_k
        if not isinstance(score_threshold, NotGiven):
            body["scoreThreshold"] = score_threshold
        if not isinstance(filter, NotGiven):
            body["filter"] = filter
        return self._post(
            f"/datastore/stores/{store_id}/query",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def search(
        self,
        store_id: str,
        *,
        query: str,
        top_k: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """LLM-enhanced hierarchical search against a store.

        Uses an LLM to refine and rank results beyond pure vector similarity.

        Args:
          store_id: The store identifier.
          query: Natural language query string.
          top_k: Maximum number of results to return.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "query": query,
        }
        if not isinstance(top_k, NotGiven):
            body["topK"] = top_k
        return self._post(
            f"/datastore/stores/{store_id}/search",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncDatastoreResource(AsyncAPIResource):
    """RAG vector store service for semantic search over embedded documents (async).

    Manages stores (knowledge bases), files, vectors, and search queries
    against the Hanzo Cloud API backend.
    """

    @cached_property
    def with_raw_response(self) -> AsyncDatastoreResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDatastoreResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDatastoreResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncDatastoreResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------
    # Store CRUD
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all stores, optionally filtered by owner or type.

        Args:
          owner: Filter stores by owner identifier.
          type: Filter stores by type.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        query_params: Dict[str, Any] = {}
        if not isinstance(owner, NotGiven):
            query_params["owner"] = owner
        if not isinstance(type, NotGiven):
            query_params["type"] = type
        return await self._get(
            "/datastore/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query_params if query_params else None,
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        embedding_provider: str | NotGiven = NOT_GIVEN,
        embedding_model: str | NotGiven = NOT_GIVEN,
        dimension: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new store (knowledge base) for RAG.

        Args:
          name: Name of the store.
          description: Human-readable description.
          embedding_provider: Embedding provider (e.g. "OpenAI", "Cohere", "Jina").
          embedding_model: Model name for embedding generation.
          dimension: Embedding vector dimension.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        body: Dict[str, Any] = {"name": name}
        if not isinstance(description, NotGiven):
            body["description"] = description
        if not isinstance(embedding_provider, NotGiven):
            body["embeddingProvider"] = embedding_provider
        if not isinstance(embedding_model, NotGiven):
            body["embeddingModel"] = embedding_model
        if not isinstance(dimension, NotGiven):
            body["dimension"] = dimension
        return await self._post(
            "/datastore/stores",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a store by ID.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return await self._get(
            f"/datastore/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update(
        self,
        store_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        embedding_provider: str | NotGiven = NOT_GIVEN,
        embedding_model: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing store.

        Args:
          store_id: The store identifier.
          name: Updated name.
          description: Updated description.
          embedding_provider: Updated embedding provider.
          embedding_model: Updated embedding model.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {}
        if not isinstance(name, NotGiven):
            body["name"] = name
        if not isinstance(description, NotGiven):
            body["description"] = description
        if not isinstance(embedding_provider, NotGiven):
            body["embeddingProvider"] = embedding_provider
        if not isinstance(embedding_model, NotGiven):
            body["embeddingModel"] = embedding_model
        return await self._post(
            f"/datastore/stores/{store_id}",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a store.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return await self._delete(
            f"/datastore/stores/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    async def list_files(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all files in a store.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return await self._get(
            f"/datastore/stores/{store_id}/files",
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
        split_method: str | NotGiven = NOT_GIVEN,
        chunk_size: int | NotGiven = NOT_GIVEN,
        chunk_overlap: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a file (text content) to a store for chunking and embedding.

        Args:
          store_id: The store identifier.
          name: File name.
          content: Raw text content of the file.
          type: File/content type hint.
          split_method: How to split the document (e.g. "character", "token").
          chunk_size: Number of characters/tokens per chunk.
          chunk_overlap: Overlap between consecutive chunks.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "name": name,
            "content": content,
        }
        if not isinstance(type, NotGiven):
            body["type"] = type
        if not isinstance(split_method, NotGiven):
            body["splitMethod"] = split_method
        if not isinstance(chunk_size, NotGiven):
            body["chunkSize"] = chunk_size
        if not isinstance(chunk_overlap, NotGiven):
            body["chunkOverlap"] = chunk_overlap
        return await self._post(
            f"/datastore/stores/{store_id}/files",
            body=body,
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
        """Get a file by ID.

        Args:
          file_id: The file identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._get(
            f"/datastore/files/{file_id}",
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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing file.

        Args:
          file_id: The file identifier.
          name: Updated file name.
          content: Updated text content.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        body: Dict[str, Any] = {}
        if not isinstance(name, NotGiven):
            body["name"] = name
        if not isinstance(content, NotGiven):
            body["content"] = content
        return await self._post(
            f"/datastore/files/{file_id}",
            body=body,
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
        """Delete a file.

        Args:
          file_id: The file identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._delete(
            f"/datastore/files/{file_id}",
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
        split_method: str | NotGiven = NOT_GIVEN,
        chunk_size: int | NotGiven = NOT_GIVEN,
        chunk_overlap: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Upload a binary file (PDF, DOCX, etc.) to a store via multipart form.

        The backend parses the file, chunks it, and generates embeddings.

        Args:
          store_id: The store identifier.
          file: The file to upload (path, bytes, or file-like object).
          split_method: How to split the document (e.g. "character", "token").
          chunk_size: Number of characters/tokens per chunk.
          chunk_overlap: Overlap between consecutive chunks.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body = deepcopy_minimal(
            {
                "file": file,
                "store_id": store_id,
                "split_method": split_method,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            f"/datastore/stores/{store_id}/upload",
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

    # ------------------------------------------------------------------
    # Vector operations
    # ------------------------------------------------------------------

    async def list_vectors(
        self,
        store_id: str,
        *,
        file_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List vectors in a store, optionally filtered by file.

        Args:
          store_id: The store identifier.
          file_id: Filter vectors by source file.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        query_params: Dict[str, Any] = {}
        if not isinstance(file_id, NotGiven):
            query_params["file_id"] = file_id
        return await self._get(
            f"/datastore/stores/{store_id}/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query_params if query_params else None,
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
        """Manually add a vector to a store.

        Args:
          store_id: The store identifier.
          file_id: Source file identifier.
          content: Text content for this vector chunk.
          embedding: Pre-computed embedding vector (optional; backend can generate).
          metadata: Arbitrary metadata attached to the vector.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "file_id": file_id,
            "content": content,
        }
        if not isinstance(embedding, NotGiven):
            body["embedding"] = embedding
        if not isinstance(metadata, NotGiven):
            body["metadata"] = metadata
        return await self._post(
            f"/datastore/stores/{store_id}/vectors",
            body=body,
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
        """Delete a vector by ID.

        Args:
          vector_id: The vector identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not vector_id:
            raise ValueError(f"Expected a non-empty value for `vector_id` but received {vector_id!r}")
        return await self._delete(
            f"/datastore/vectors/{vector_id}",
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
        """Re-embed all documents in a store, regenerating all vectors.

        Args:
          store_id: The store identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        return await self._post(
            f"/datastore/stores/{store_id}/vectors/refresh",
            body={"store_id": store_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Search / Query
    # ------------------------------------------------------------------

    async def query(
        self,
        store_id: str,
        *,
        query: str,
        top_k: int | NotGiven = NOT_GIVEN,
        score_threshold: float | NotGiven = NOT_GIVEN,
        filter: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Semantic vector search against a store.

        Args:
          store_id: The store identifier.
          query: Natural language query string.
          top_k: Maximum number of results to return.
          score_threshold: Minimum cosine similarity score (0.0-1.0).
          filter: Metadata filter object for narrowing results.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "query": query,
        }
        if not isinstance(top_k, NotGiven):
            body["topK"] = top_k
        if not isinstance(score_threshold, NotGiven):
            body["scoreThreshold"] = score_threshold
        if not isinstance(filter, NotGiven):
            body["filter"] = filter
        return await self._post(
            f"/datastore/stores/{store_id}/query",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def search(
        self,
        store_id: str,
        *,
        query: str,
        top_k: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """LLM-enhanced hierarchical search against a store.

        Uses an LLM to refine and rank results beyond pure vector similarity.

        Args:
          store_id: The store identifier.
          query: Natural language query string.
          top_k: Maximum number of results to return.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not store_id:
            raise ValueError(f"Expected a non-empty value for `store_id` but received {store_id!r}")
        body: Dict[str, Any] = {
            "store_id": store_id,
            "query": query,
        }
        if not isinstance(top_k, NotGiven):
            body["topK"] = top_k
        return await self._post(
            f"/datastore/stores/{store_id}/search",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class DatastoreResourceWithRawResponse:
    def __init__(self, datastore: DatastoreResource) -> None:
        self._datastore = datastore

        # Store CRUD
        self.list = to_raw_response_wrapper(datastore.list)
        self.create = to_raw_response_wrapper(datastore.create)
        self.retrieve = to_raw_response_wrapper(datastore.retrieve)
        self.update = to_raw_response_wrapper(datastore.update)
        self.delete = to_raw_response_wrapper(datastore.delete)

        # File management
        self.list_files = to_raw_response_wrapper(datastore.list_files)
        self.create_file = to_raw_response_wrapper(datastore.create_file)
        self.retrieve_file = to_raw_response_wrapper(datastore.retrieve_file)
        self.update_file = to_raw_response_wrapper(datastore.update_file)
        self.delete_file = to_raw_response_wrapper(datastore.delete_file)
        self.upload_file = to_raw_response_wrapper(datastore.upload_file)

        # Vector operations
        self.list_vectors = to_raw_response_wrapper(datastore.list_vectors)
        self.create_vector = to_raw_response_wrapper(datastore.create_vector)
        self.delete_vector = to_raw_response_wrapper(datastore.delete_vector)
        self.refresh_vectors = to_raw_response_wrapper(datastore.refresh_vectors)

        # Search / Query
        self.query = to_raw_response_wrapper(datastore.query)
        self.search = to_raw_response_wrapper(datastore.search)


class AsyncDatastoreResourceWithRawResponse:
    def __init__(self, datastore: AsyncDatastoreResource) -> None:
        self._datastore = datastore

        # Store CRUD
        self.list = async_to_raw_response_wrapper(datastore.list)
        self.create = async_to_raw_response_wrapper(datastore.create)
        self.retrieve = async_to_raw_response_wrapper(datastore.retrieve)
        self.update = async_to_raw_response_wrapper(datastore.update)
        self.delete = async_to_raw_response_wrapper(datastore.delete)

        # File management
        self.list_files = async_to_raw_response_wrapper(datastore.list_files)
        self.create_file = async_to_raw_response_wrapper(datastore.create_file)
        self.retrieve_file = async_to_raw_response_wrapper(datastore.retrieve_file)
        self.update_file = async_to_raw_response_wrapper(datastore.update_file)
        self.delete_file = async_to_raw_response_wrapper(datastore.delete_file)
        self.upload_file = async_to_raw_response_wrapper(datastore.upload_file)

        # Vector operations
        self.list_vectors = async_to_raw_response_wrapper(datastore.list_vectors)
        self.create_vector = async_to_raw_response_wrapper(datastore.create_vector)
        self.delete_vector = async_to_raw_response_wrapper(datastore.delete_vector)
        self.refresh_vectors = async_to_raw_response_wrapper(datastore.refresh_vectors)

        # Search / Query
        self.query = async_to_raw_response_wrapper(datastore.query)
        self.search = async_to_raw_response_wrapper(datastore.search)


class DatastoreResourceWithStreamingResponse:
    def __init__(self, datastore: DatastoreResource) -> None:
        self._datastore = datastore

        # Store CRUD
        self.list = to_streamed_response_wrapper(datastore.list)
        self.create = to_streamed_response_wrapper(datastore.create)
        self.retrieve = to_streamed_response_wrapper(datastore.retrieve)
        self.update = to_streamed_response_wrapper(datastore.update)
        self.delete = to_streamed_response_wrapper(datastore.delete)

        # File management
        self.list_files = to_streamed_response_wrapper(datastore.list_files)
        self.create_file = to_streamed_response_wrapper(datastore.create_file)
        self.retrieve_file = to_streamed_response_wrapper(datastore.retrieve_file)
        self.update_file = to_streamed_response_wrapper(datastore.update_file)
        self.delete_file = to_streamed_response_wrapper(datastore.delete_file)
        self.upload_file = to_streamed_response_wrapper(datastore.upload_file)

        # Vector operations
        self.list_vectors = to_streamed_response_wrapper(datastore.list_vectors)
        self.create_vector = to_streamed_response_wrapper(datastore.create_vector)
        self.delete_vector = to_streamed_response_wrapper(datastore.delete_vector)
        self.refresh_vectors = to_streamed_response_wrapper(datastore.refresh_vectors)

        # Search / Query
        self.query = to_streamed_response_wrapper(datastore.query)
        self.search = to_streamed_response_wrapper(datastore.search)


class AsyncDatastoreResourceWithStreamingResponse:
    def __init__(self, datastore: AsyncDatastoreResource) -> None:
        self._datastore = datastore

        # Store CRUD
        self.list = async_to_streamed_response_wrapper(datastore.list)
        self.create = async_to_streamed_response_wrapper(datastore.create)
        self.retrieve = async_to_streamed_response_wrapper(datastore.retrieve)
        self.update = async_to_streamed_response_wrapper(datastore.update)
        self.delete = async_to_streamed_response_wrapper(datastore.delete)

        # File management
        self.list_files = async_to_streamed_response_wrapper(datastore.list_files)
        self.create_file = async_to_streamed_response_wrapper(datastore.create_file)
        self.retrieve_file = async_to_streamed_response_wrapper(datastore.retrieve_file)
        self.update_file = async_to_streamed_response_wrapper(datastore.update_file)
        self.delete_file = async_to_streamed_response_wrapper(datastore.delete_file)
        self.upload_file = async_to_streamed_response_wrapper(datastore.upload_file)

        # Vector operations
        self.list_vectors = async_to_streamed_response_wrapper(datastore.list_vectors)
        self.create_vector = async_to_streamed_response_wrapper(datastore.create_vector)
        self.delete_vector = async_to_streamed_response_wrapper(datastore.delete_vector)
        self.refresh_vectors = async_to_streamed_response_wrapper(datastore.refresh_vectors)

        # Search / Query
        self.query = async_to_streamed_response_wrapper(datastore.query)
        self.search = async_to_streamed_response_wrapper(datastore.search)
