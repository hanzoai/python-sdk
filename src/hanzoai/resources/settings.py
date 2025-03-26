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

__all__ = ["SettingsResource", "AsyncSettingsResource"]


class SettingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return SettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return SettingsResourceWithStreamingResponse(self)

    def retrieve(
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
        Returns a list of llm level settings

        This is useful for debugging and ensuring the proxy server is configured
        correctly.

        Response schema:

        ```
        {
            "alerting": _alerting,
            "llm.callbacks": llm_callbacks,
            "llm.input_callback": llm_input_callbacks,
            "llm.failure_callback": llm_failure_callbacks,
            "llm.success_callback": llm_success_callbacks,
            "llm._async_success_callback": llm_async_success_callbacks,
            "llm._async_failure_callback": llm_async_failure_callbacks,
            "llm._async_input_callback": llm_async_input_callbacks,
            "all_llm_callbacks": all_llm_callbacks,
            "num_callbacks": len(all_llm_callbacks),
            "num_alerting": _num_alerting,
            "llm.request_timeout": llm.request_timeout,
        }
        ```
        """
        return self._get(
            "/settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncSettingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncSettingsResourceWithStreamingResponse(self)

    async def retrieve(
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
        Returns a list of llm level settings

        This is useful for debugging and ensuring the proxy server is configured
        correctly.

        Response schema:

        ```
        {
            "alerting": _alerting,
            "llm.callbacks": llm_callbacks,
            "llm.input_callback": llm_input_callbacks,
            "llm.failure_callback": llm_failure_callbacks,
            "llm.success_callback": llm_success_callbacks,
            "llm._async_success_callback": llm_async_success_callbacks,
            "llm._async_failure_callback": llm_async_failure_callbacks,
            "llm._async_input_callback": llm_async_input_callbacks,
            "all_llm_callbacks": all_llm_callbacks,
            "num_callbacks": len(all_llm_callbacks),
            "num_alerting": _num_alerting,
            "llm.request_timeout": llm.request_timeout,
        }
        ```
        """
        return await self._get(
            "/settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class SettingsResourceWithRawResponse:
    def __init__(self, settings: SettingsResource) -> None:
        self._settings = settings

        self.retrieve = to_raw_response_wrapper(
            settings.retrieve,
        )


class AsyncSettingsResourceWithRawResponse:
    def __init__(self, settings: AsyncSettingsResource) -> None:
        self._settings = settings

        self.retrieve = async_to_raw_response_wrapper(
            settings.retrieve,
        )


class SettingsResourceWithStreamingResponse:
    def __init__(self, settings: SettingsResource) -> None:
        self._settings = settings

        self.retrieve = to_streamed_response_wrapper(
            settings.retrieve,
        )


class AsyncSettingsResourceWithStreamingResponse:
    def __init__(self, settings: AsyncSettingsResource) -> None:
        self._settings = settings

        self.retrieve = async_to_streamed_response_wrapper(
            settings.retrieve,
        )
