# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import add_add_allowed_ip_params
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import (
    maybe_transform,
    async_maybe_transform,
)
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["AddResource", "AsyncAddResource"]


class AddResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AddResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AddResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AddResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AddResourceWithStreamingResponse(self)

    def add_allowed_ip(
        self,
        *,
        ip: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Add Allowed Ip

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/add/allowed_ip",
            body=maybe_transform({"ip": ip}, add_add_allowed_ip_params.AddAddAllowedIPParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncAddResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAddResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncAddResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAddResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncAddResourceWithStreamingResponse(self)

    async def add_allowed_ip(
        self,
        *,
        ip: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Add Allowed Ip

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/add/allowed_ip",
            body=await async_maybe_transform({"ip": ip}, add_add_allowed_ip_params.AddAddAllowedIPParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AddResourceWithRawResponse:
    def __init__(self, add: AddResource) -> None:
        self._add = add

        self.add_allowed_ip = to_raw_response_wrapper(
            add.add_allowed_ip,
        )


class AsyncAddResourceWithRawResponse:
    def __init__(self, add: AsyncAddResource) -> None:
        self._add = add

        self.add_allowed_ip = async_to_raw_response_wrapper(
            add.add_allowed_ip,
        )


class AddResourceWithStreamingResponse:
    def __init__(self, add: AddResource) -> None:
        self._add = add

        self.add_allowed_ip = to_streamed_response_wrapper(
            add.add_allowed_ip,
        )


class AsyncAddResourceWithStreamingResponse:
    def __init__(self, add: AsyncAddResource) -> None:
        self._add = add

        self.add_allowed_ip = async_to_streamed_response_wrapper(
            add.add_allowed_ip,
        )
