# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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

__all__ = ["RedisResource", "AsyncRedisResource"]


class RedisResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RedisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return RedisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RedisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return RedisResourceWithStreamingResponse(self)

    def retrieve_info(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Endpoint for getting /redis/info"""
        return self._get(
            "/cache/redis/info",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncRedisResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRedisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRedisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRedisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncRedisResourceWithStreamingResponse(self)

    async def retrieve_info(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Endpoint for getting /redis/info"""
        return await self._get(
            "/cache/redis/info",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class RedisResourceWithRawResponse:
    def __init__(self, redis: RedisResource) -> None:
        self._redis = redis

        self.retrieve_info = to_raw_response_wrapper(
            redis.retrieve_info,
        )


class AsyncRedisResourceWithRawResponse:
    def __init__(self, redis: AsyncRedisResource) -> None:
        self._redis = redis

        self.retrieve_info = async_to_raw_response_wrapper(
            redis.retrieve_info,
        )


class RedisResourceWithStreamingResponse:
    def __init__(self, redis: RedisResource) -> None:
        self._redis = redis

        self.retrieve_info = to_streamed_response_wrapper(
            redis.retrieve_info,
        )


class AsyncRedisResourceWithStreamingResponse:
    def __init__(self, redis: AsyncRedisResource) -> None:
        self._redis = redis

        self.retrieve_info = async_to_streamed_response_wrapper(
            redis.retrieve_info,
        )
