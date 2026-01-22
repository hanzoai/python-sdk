# Hanzo AI SDK

from __future__ import annotations

from typing import Optional, Dict, Any

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

__all__ = ["StoresResource", "AsyncStoresResource"]


class StoresResource(SyncAPIResource):
    """Vector store management."""

    @cached_property
    def with_raw_response(self) -> StoresResourceWithRawResponse:
        return StoresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StoresResourceWithStreamingResponse:
        return StoresResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vector stores."""
        return self._get(
            "/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific vector store."""
        return self._get(
            f"/stores/{store_id}",
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
        name: str,
        provider: str | NotGiven = NOT_GIVEN,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vector store."""
        return self._post(
            "/stores",
            body={"name": name, "provider": provider, "config": config},
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
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a vector store."""
        return self._put(
            f"/stores/{store_id}",
            body={"name": name, "config": config},
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
        """Delete a vector store."""
        return self._delete(
            f"/stores/{store_id}",
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
        """Refresh vectors in a store."""
        return self._post(
            f"/stores/{store_id}/vectors/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncStoresResource(AsyncAPIResource):
    """Vector store management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncStoresResourceWithRawResponse:
        return AsyncStoresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStoresResourceWithStreamingResponse:
        return AsyncStoresResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vector stores."""
        return await self._get(
            "/stores",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific vector store."""
        return await self._get(
            f"/stores/{store_id}",
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
        name: str,
        provider: str | NotGiven = NOT_GIVEN,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vector store."""
        return await self._post(
            "/stores",
            body={"name": name, "provider": provider, "config": config},
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
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a vector store."""
        return await self._put(
            f"/stores/{store_id}",
            body={"name": name, "config": config},
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
        """Delete a vector store."""
        return await self._delete(
            f"/stores/{store_id}",
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
        """Refresh vectors in a store."""
        return await self._post(
            f"/stores/{store_id}/vectors/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class StoresResourceWithRawResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores
        self.list = to_raw_response_wrapper(stores.list)
        self.get = to_raw_response_wrapper(stores.get)
        self.create = to_raw_response_wrapper(stores.create)
        self.update = to_raw_response_wrapper(stores.update)
        self.delete = to_raw_response_wrapper(stores.delete)
        self.refresh_vectors = to_raw_response_wrapper(stores.refresh_vectors)


class AsyncStoresResourceWithRawResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores
        self.list = async_to_raw_response_wrapper(stores.list)
        self.get = async_to_raw_response_wrapper(stores.get)
        self.create = async_to_raw_response_wrapper(stores.create)
        self.update = async_to_raw_response_wrapper(stores.update)
        self.delete = async_to_raw_response_wrapper(stores.delete)
        self.refresh_vectors = async_to_raw_response_wrapper(stores.refresh_vectors)


class StoresResourceWithStreamingResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores
        self.list = to_streamed_response_wrapper(stores.list)
        self.get = to_streamed_response_wrapper(stores.get)
        self.create = to_streamed_response_wrapper(stores.create)
        self.update = to_streamed_response_wrapper(stores.update)
        self.delete = to_streamed_response_wrapper(stores.delete)
        self.refresh_vectors = to_streamed_response_wrapper(stores.refresh_vectors)


class AsyncStoresResourceWithStreamingResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores
        self.list = async_to_streamed_response_wrapper(stores.list)
        self.get = async_to_streamed_response_wrapper(stores.get)
        self.create = async_to_streamed_response_wrapper(stores.create)
        self.update = async_to_streamed_response_wrapper(stores.update)
        self.delete = async_to_streamed_response_wrapper(stores.delete)
        self.refresh_vectors = async_to_streamed_response_wrapper(stores.refresh_vectors)
