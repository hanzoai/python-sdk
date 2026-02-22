# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["VectorsResource", "AsyncVectorsResource"]


class VectorsResource(SyncAPIResource):
    """Vector embedding operations."""

    @cached_property
    def with_raw_response(self) -> VectorsResourceWithRawResponse:
        return VectorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VectorsResourceWithStreamingResponse:
        return VectorsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        store_id: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vectors."""
        return self._get(
            "/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"store_id": store_id, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    def get(
        self,
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific vector."""
        return self._get(
            f"/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        content: str,
        store_id: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vector embedding."""
        return self._post(
            "/vectors",
            body={"content": content, "store_id": store_id, "metadata": metadata},
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
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vector."""
        return self._delete(
            f"/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_all(
        self,
        *,
        store_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete all vectors in a store."""
        return self._delete(
            "/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"store_id": store_id},
            ),
            cast_to=object,
        )

    def search(
        self,
        *,
        query: str,
        store_id: str,
        limit: int | NotGiven = NOT_GIVEN,
        threshold: float | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Search vectors by semantic similarity."""
        return self._post(
            "/vectors/search",
            body={
                "query": query,
                "store_id": store_id,
                "limit": limit,
                "threshold": threshold,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncVectorsResource(AsyncAPIResource):
    """Vector embedding operations (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncVectorsResourceWithRawResponse:
        return AsyncVectorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVectorsResourceWithStreamingResponse:
        return AsyncVectorsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        store_id: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vectors."""
        return await self._get(
            "/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"store_id": store_id, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    async def get(
        self,
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific vector."""
        return await self._get(
            f"/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        content: str,
        store_id: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vector embedding."""
        return await self._post(
            "/vectors",
            body={"content": content, "store_id": store_id, "metadata": metadata},
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
        vector_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vector."""
        return await self._delete(
            f"/vectors/{vector_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_all(
        self,
        *,
        store_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete all vectors in a store."""
        return await self._delete(
            "/vectors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"store_id": store_id},
            ),
            cast_to=object,
        )

    async def search(
        self,
        *,
        query: str,
        store_id: str,
        limit: int | NotGiven = NOT_GIVEN,
        threshold: float | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Search vectors by semantic similarity."""
        return await self._post(
            "/vectors/search",
            body={
                "query": query,
                "store_id": store_id,
                "limit": limit,
                "threshold": threshold,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class VectorsResourceWithRawResponse:
    def __init__(self, vectors: VectorsResource) -> None:
        self._vectors = vectors
        self.list = to_raw_response_wrapper(vectors.list)
        self.get = to_raw_response_wrapper(vectors.get)
        self.create = to_raw_response_wrapper(vectors.create)
        self.delete = to_raw_response_wrapper(vectors.delete)
        self.delete_all = to_raw_response_wrapper(vectors.delete_all)
        self.search = to_raw_response_wrapper(vectors.search)


class AsyncVectorsResourceWithRawResponse:
    def __init__(self, vectors: AsyncVectorsResource) -> None:
        self._vectors = vectors
        self.list = async_to_raw_response_wrapper(vectors.list)
        self.get = async_to_raw_response_wrapper(vectors.get)
        self.create = async_to_raw_response_wrapper(vectors.create)
        self.delete = async_to_raw_response_wrapper(vectors.delete)
        self.delete_all = async_to_raw_response_wrapper(vectors.delete_all)
        self.search = async_to_raw_response_wrapper(vectors.search)


class VectorsResourceWithStreamingResponse:
    def __init__(self, vectors: VectorsResource) -> None:
        self._vectors = vectors
        self.list = to_streamed_response_wrapper(vectors.list)
        self.get = to_streamed_response_wrapper(vectors.get)
        self.create = to_streamed_response_wrapper(vectors.create)
        self.delete = to_streamed_response_wrapper(vectors.delete)
        self.delete_all = to_streamed_response_wrapper(vectors.delete_all)
        self.search = to_streamed_response_wrapper(vectors.search)


class AsyncVectorsResourceWithStreamingResponse:
    def __init__(self, vectors: AsyncVectorsResource) -> None:
        self._vectors = vectors
        self.list = async_to_streamed_response_wrapper(vectors.list)
        self.get = async_to_streamed_response_wrapper(vectors.get)
        self.create = async_to_streamed_response_wrapper(vectors.create)
        self.delete = async_to_streamed_response_wrapper(vectors.delete)
        self.delete_all = async_to_streamed_response_wrapper(vectors.delete_all)
        self.search = async_to_streamed_response_wrapper(vectors.search)
