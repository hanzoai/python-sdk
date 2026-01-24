# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import Body, Query, Headers, NotGiven, not_given
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["ActiveResource", "AsyncActiveResource"]


class ActiveResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ActiveResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ActiveResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ActiveResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ActiveResourceWithStreamingResponse(self)

    def list_callbacks(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Returns a list of litellm level settings

        This is useful for debugging and ensuring the proxy server is configured
        correctly.

        Response schema:

        ```
        {
            "alerting": _alerting,
            "litellm.callbacks": litellm_callbacks,
            "litellm.input_callback": litellm_input_callbacks,
            "litellm.failure_callback": litellm_failure_callbacks,
            "litellm.success_callback": litellm_success_callbacks,
            "litellm._async_success_callback": litellm_async_success_callbacks,
            "litellm._async_failure_callback": litellm_async_failure_callbacks,
            "litellm._async_input_callback": litellm_async_input_callbacks,
            "all_litellm_callbacks": all_litellm_callbacks,
            "num_callbacks": len(all_litellm_callbacks),
            "num_alerting": _num_alerting,
            "litellm.request_timeout": litellm.request_timeout,
        }
        ```
        """
        return self._get(
            "/active/callbacks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncActiveResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncActiveResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncActiveResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncActiveResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncActiveResourceWithStreamingResponse(self)

    async def list_callbacks(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Returns a list of litellm level settings

        This is useful for debugging and ensuring the proxy server is configured
        correctly.

        Response schema:

        ```
        {
            "alerting": _alerting,
            "litellm.callbacks": litellm_callbacks,
            "litellm.input_callback": litellm_input_callbacks,
            "litellm.failure_callback": litellm_failure_callbacks,
            "litellm.success_callback": litellm_success_callbacks,
            "litellm._async_success_callback": litellm_async_success_callbacks,
            "litellm._async_failure_callback": litellm_async_failure_callbacks,
            "litellm._async_input_callback": litellm_async_input_callbacks,
            "all_litellm_callbacks": all_litellm_callbacks,
            "num_callbacks": len(all_litellm_callbacks),
            "num_alerting": _num_alerting,
            "litellm.request_timeout": litellm.request_timeout,
        }
        ```
        """
        return await self._get(
            "/active/callbacks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class ActiveResourceWithRawResponse:
    def __init__(self, active: ActiveResource) -> None:
        self._active = active

        self.list_callbacks = to_raw_response_wrapper(
            active.list_callbacks,
        )


class AsyncActiveResourceWithRawResponse:
    def __init__(self, active: AsyncActiveResource) -> None:
        self._active = active

        self.list_callbacks = async_to_raw_response_wrapper(
            active.list_callbacks,
        )


class ActiveResourceWithStreamingResponse:
    def __init__(self, active: ActiveResource) -> None:
        self._active = active

        self.list_callbacks = to_streamed_response_wrapper(
            active.list_callbacks,
        )


class AsyncActiveResourceWithStreamingResponse:
    def __init__(self, active: AsyncActiveResource) -> None:
        self._active = active

        self.list_callbacks = async_to_streamed_response_wrapper(
            active.list_callbacks,
        )
