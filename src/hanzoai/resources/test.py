# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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

__all__ = ["TestResource", "AsyncTestResource"]


class TestResource(SyncAPIResource):
    __test__ = False

    @cached_property
    def with_raw_response(self) -> TestResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return TestResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TestResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return TestResourceWithStreamingResponse(self)

    def ping(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [DEPRECATED] use `/health/liveliness` instead.

        A test endpoint that pings the proxy server to check if it's healthy.

        Parameters: request (Request): The incoming request.

        Returns: dict: A dictionary containing the route of the request URL.
        """
        return self._get(
            "/test",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncTestResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTestResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTestResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTestResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncTestResourceWithStreamingResponse(self)

    async def ping(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [DEPRECATED] use `/health/liveliness` instead.

        A test endpoint that pings the proxy server to check if it's healthy.

        Parameters: request (Request): The incoming request.

        Returns: dict: A dictionary containing the route of the request URL.
        """
        return await self._get(
            "/test",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class TestResourceWithRawResponse:
    __test__ = False

    def __init__(self, test: TestResource) -> None:
        self._test = test

        self.ping = to_raw_response_wrapper(
            test.ping,
        )


class AsyncTestResourceWithRawResponse:
    def __init__(self, test: AsyncTestResource) -> None:
        self._test = test

        self.ping = async_to_raw_response_wrapper(
            test.ping,
        )


class TestResourceWithStreamingResponse:
    __test__ = False

    def __init__(self, test: TestResource) -> None:
        self._test = test

        self.ping = to_streamed_response_wrapper(
            test.ping,
        )


class AsyncTestResourceWithStreamingResponse:
    def __init__(self, test: AsyncTestResource) -> None:
        self._test = test

        self.ping = async_to_streamed_response_wrapper(
            test.ping,
        )
