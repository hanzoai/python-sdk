# Hanzo AI SDK

from __future__ import annotations

from typing import List, Optional

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

__all__ = ["KVResource", "AsyncKVResource"]


class KVResource(SyncAPIResource):
    """Key-value store service."""

    @cached_property
    def with_raw_response(self) -> KVResourceWithRawResponse:
        return KVResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KVResourceWithStreamingResponse:
        return KVResourceWithStreamingResponse(self)

    def list_namespaces(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all KV namespaces."""
        return self._get(
            "/kv/namespaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_namespace(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new KV namespace."""
        return self._post(
            "/kv/namespaces",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_namespace(
        self,
        namespace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a KV namespace."""
        return self._delete(
            f"/kv/namespaces/{namespace_id}",
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
        namespace_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a value from KV store."""
        return self._get(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def put(
        self,
        namespace_id: str,
        key: str,
        *,
        value: str,
        ttl: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Put a value into KV store."""
        return self._put(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            body={"value": value, "ttl": ttl},
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
        namespace_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a value from KV store."""
        return self._delete(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_keys(
        self,
        namespace_id: str,
        *,
        prefix: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List keys in a namespace."""
        return self._get(
            f"/kv/namespaces/{namespace_id}/keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"prefix": prefix, "limit": limit},
            ),
            cast_to=object,
        )


class AsyncKVResource(AsyncAPIResource):
    """Key-value store service (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncKVResourceWithRawResponse:
        return AsyncKVResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKVResourceWithStreamingResponse:
        return AsyncKVResourceWithStreamingResponse(self)

    async def list_namespaces(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/kv/namespaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_namespace(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/kv/namespaces",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_namespace(
        self,
        namespace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/kv/namespaces/{namespace_id}",
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
        namespace_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def put(
        self,
        namespace_id: str,
        key: str,
        *,
        value: str,
        ttl: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            body={"value": value, "ttl": ttl},
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
        namespace_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/kv/namespaces/{namespace_id}/values/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_keys(
        self,
        namespace_id: str,
        *,
        prefix: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/kv/namespaces/{namespace_id}/keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"prefix": prefix, "limit": limit},
            ),
            cast_to=object,
        )


class KVResourceWithRawResponse:
    def __init__(self, kv: KVResource) -> None:
        self._kv = kv
        self.list_namespaces = to_raw_response_wrapper(kv.list_namespaces)
        self.create_namespace = to_raw_response_wrapper(kv.create_namespace)
        self.delete_namespace = to_raw_response_wrapper(kv.delete_namespace)
        self.get = to_raw_response_wrapper(kv.get)
        self.put = to_raw_response_wrapper(kv.put)
        self.delete = to_raw_response_wrapper(kv.delete)
        self.list_keys = to_raw_response_wrapper(kv.list_keys)


class AsyncKVResourceWithRawResponse:
    def __init__(self, kv: AsyncKVResource) -> None:
        self._kv = kv
        self.list_namespaces = async_to_raw_response_wrapper(kv.list_namespaces)
        self.create_namespace = async_to_raw_response_wrapper(kv.create_namespace)
        self.delete_namespace = async_to_raw_response_wrapper(kv.delete_namespace)
        self.get = async_to_raw_response_wrapper(kv.get)
        self.put = async_to_raw_response_wrapper(kv.put)
        self.delete = async_to_raw_response_wrapper(kv.delete)
        self.list_keys = async_to_raw_response_wrapper(kv.list_keys)


class KVResourceWithStreamingResponse:
    def __init__(self, kv: KVResource) -> None:
        self._kv = kv
        self.list_namespaces = to_streamed_response_wrapper(kv.list_namespaces)
        self.create_namespace = to_streamed_response_wrapper(kv.create_namespace)
        self.delete_namespace = to_streamed_response_wrapper(kv.delete_namespace)
        self.get = to_streamed_response_wrapper(kv.get)
        self.put = to_streamed_response_wrapper(kv.put)
        self.delete = to_streamed_response_wrapper(kv.delete)
        self.list_keys = to_streamed_response_wrapper(kv.list_keys)


class AsyncKVResourceWithStreamingResponse:
    def __init__(self, kv: AsyncKVResource) -> None:
        self._kv = kv
        self.list_namespaces = async_to_streamed_response_wrapper(kv.list_namespaces)
        self.create_namespace = async_to_streamed_response_wrapper(kv.create_namespace)
        self.delete_namespace = async_to_streamed_response_wrapper(kv.delete_namespace)
        self.get = async_to_streamed_response_wrapper(kv.get)
        self.put = async_to_streamed_response_wrapper(kv.put)
        self.delete = async_to_streamed_response_wrapper(kv.delete)
        self.list_keys = async_to_streamed_response_wrapper(kv.list_keys)
