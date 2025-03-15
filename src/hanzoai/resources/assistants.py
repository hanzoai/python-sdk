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

__all__ = ["AssistantsResource", "AsyncAssistantsResource"]


class AssistantsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AssistantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AssistantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AssistantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AssistantsResourceWithStreamingResponse(self)

    def create(
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
        Create assistant

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/createAssistant
        """
        return self._post(
            "/v1/assistants",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
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
        Returns a list of assistants.

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/listAssistants
        """
        return self._get(
            "/v1/assistants",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        assistant_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete assistant

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/createAssistant

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not assistant_id:
            raise ValueError(f"Expected a non-empty value for `assistant_id` but received {assistant_id!r}")
        return self._delete(
            f"/v1/assistants/{assistant_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncAssistantsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAssistantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncAssistantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAssistantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncAssistantsResourceWithStreamingResponse(self)

    async def create(
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
        Create assistant

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/createAssistant
        """
        return await self._post(
            "/v1/assistants",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
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
        Returns a list of assistants.

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/listAssistants
        """
        return await self._get(
            "/v1/assistants",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        assistant_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete assistant

        API Reference docs -
        https://platform.openai.com/docs/api-reference/assistants/createAssistant

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not assistant_id:
            raise ValueError(f"Expected a non-empty value for `assistant_id` but received {assistant_id!r}")
        return await self._delete(
            f"/v1/assistants/{assistant_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AssistantsResourceWithRawResponse:
    def __init__(self, assistants: AssistantsResource) -> None:
        self._assistants = assistants

        self.create = to_raw_response_wrapper(
            assistants.create,
        )
        self.list = to_raw_response_wrapper(
            assistants.list,
        )
        self.delete = to_raw_response_wrapper(
            assistants.delete,
        )


class AsyncAssistantsResourceWithRawResponse:
    def __init__(self, assistants: AsyncAssistantsResource) -> None:
        self._assistants = assistants

        self.create = async_to_raw_response_wrapper(
            assistants.create,
        )
        self.list = async_to_raw_response_wrapper(
            assistants.list,
        )
        self.delete = async_to_raw_response_wrapper(
            assistants.delete,
        )


class AssistantsResourceWithStreamingResponse:
    def __init__(self, assistants: AssistantsResource) -> None:
        self._assistants = assistants

        self.create = to_streamed_response_wrapper(
            assistants.create,
        )
        self.list = to_streamed_response_wrapper(
            assistants.list,
        )
        self.delete = to_streamed_response_wrapper(
            assistants.delete,
        )


class AsyncAssistantsResourceWithStreamingResponse:
    def __init__(self, assistants: AsyncAssistantsResource) -> None:
        self._assistants = assistants

        self.create = async_to_streamed_response_wrapper(
            assistants.create,
        )
        self.list = async_to_streamed_response_wrapper(
            assistants.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            assistants.delete,
        )
