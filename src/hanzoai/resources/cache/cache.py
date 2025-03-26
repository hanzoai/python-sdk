# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .redis import (
    RedisResource,
    AsyncRedisResource,
    RedisResourceWithRawResponse,
    AsyncRedisResourceWithRawResponse,
    RedisResourceWithStreamingResponse,
    AsyncRedisResourceWithStreamingResponse,
)
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.cache_ping_response import CachePingResponse

__all__ = ["CacheResource", "AsyncCacheResource"]


class CacheResource(SyncAPIResource):
    @cached_property
    def redis(self) -> RedisResource:
        return RedisResource(self._client)

    @cached_property
    def with_raw_response(self) -> CacheResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return CacheResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CacheResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return CacheResourceWithStreamingResponse(self)

    def delete(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Endpoint for deleting a key from the cache.

        All responses from llm proxy have
        `x-llm-cache-key` in the headers

        Parameters:

        - **keys**: _Optional[List[str]]_ - A list of keys to delete from the cache.
          Example {"keys": ["key1", "key2"]}

        ```shell
        curl -X POST "http://0.0.0.0:4000/cache/delete"     -H "Authorization: Bearer sk-1234"     -d '{"keys": ["key1", "key2"]}'
        ```
        """
        return self._post(
            "/cache/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def flush_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """A function to flush all items from the cache.

        (All items will be deleted from
        the cache with this) Raises HTTPException if the cache is not initialized or if
        the cache type does not support flushing. Returns a dictionary with the status
        of the operation.

        Usage:

        ```
        curl -X POST http://0.0.0.0:4000/cache/flushall -H "Authorization: Bearer sk-1234"
        ```
        """
        return self._post(
            "/cache/flushall",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def ping(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CachePingResponse:
        """Endpoint for checking if cache can be pinged"""
        return self._get(
            "/cache/ping",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CachePingResponse,
        )


class AsyncCacheResource(AsyncAPIResource):
    @cached_property
    def redis(self) -> AsyncRedisResource:
        return AsyncRedisResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCacheResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCacheResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCacheResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncCacheResourceWithStreamingResponse(self)

    async def delete(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Endpoint for deleting a key from the cache.

        All responses from llm proxy have
        `x-llm-cache-key` in the headers

        Parameters:

        - **keys**: _Optional[List[str]]_ - A list of keys to delete from the cache.
          Example {"keys": ["key1", "key2"]}

        ```shell
        curl -X POST "http://0.0.0.0:4000/cache/delete"     -H "Authorization: Bearer sk-1234"     -d '{"keys": ["key1", "key2"]}'
        ```
        """
        return await self._post(
            "/cache/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def flush_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """A function to flush all items from the cache.

        (All items will be deleted from
        the cache with this) Raises HTTPException if the cache is not initialized or if
        the cache type does not support flushing. Returns a dictionary with the status
        of the operation.

        Usage:

        ```
        curl -X POST http://0.0.0.0:4000/cache/flushall -H "Authorization: Bearer sk-1234"
        ```
        """
        return await self._post(
            "/cache/flushall",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def ping(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CachePingResponse:
        """Endpoint for checking if cache can be pinged"""
        return await self._get(
            "/cache/ping",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CachePingResponse,
        )


class CacheResourceWithRawResponse:
    def __init__(self, cache: CacheResource) -> None:
        self._cache = cache

        self.delete = to_raw_response_wrapper(
            cache.delete,
        )
        self.flush_all = to_raw_response_wrapper(
            cache.flush_all,
        )
        self.ping = to_raw_response_wrapper(
            cache.ping,
        )

    @cached_property
    def redis(self) -> RedisResourceWithRawResponse:
        return RedisResourceWithRawResponse(self._cache.redis)


class AsyncCacheResourceWithRawResponse:
    def __init__(self, cache: AsyncCacheResource) -> None:
        self._cache = cache

        self.delete = async_to_raw_response_wrapper(
            cache.delete,
        )
        self.flush_all = async_to_raw_response_wrapper(
            cache.flush_all,
        )
        self.ping = async_to_raw_response_wrapper(
            cache.ping,
        )

    @cached_property
    def redis(self) -> AsyncRedisResourceWithRawResponse:
        return AsyncRedisResourceWithRawResponse(self._cache.redis)


class CacheResourceWithStreamingResponse:
    def __init__(self, cache: CacheResource) -> None:
        self._cache = cache

        self.delete = to_streamed_response_wrapper(
            cache.delete,
        )
        self.flush_all = to_streamed_response_wrapper(
            cache.flush_all,
        )
        self.ping = to_streamed_response_wrapper(
            cache.ping,
        )

    @cached_property
    def redis(self) -> RedisResourceWithStreamingResponse:
        return RedisResourceWithStreamingResponse(self._cache.redis)


class AsyncCacheResourceWithStreamingResponse:
    def __init__(self, cache: AsyncCacheResource) -> None:
        self._cache = cache

        self.delete = async_to_streamed_response_wrapper(
            cache.delete,
        )
        self.flush_all = async_to_streamed_response_wrapper(
            cache.flush_all,
        )
        self.ping = async_to_streamed_response_wrapper(
            cache.ping,
        )

    @cached_property
    def redis(self) -> AsyncRedisResourceWithStreamingResponse:
        return AsyncRedisResourceWithStreamingResponse(self._cache.redis)
