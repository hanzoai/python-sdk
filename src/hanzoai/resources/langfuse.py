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

__all__ = ["LangfuseResource", "AsyncLangfuseResource"]


class LangfuseResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LangfuseResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return LangfuseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LangfuseResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return LangfuseResourceWithStreamingResponse(self)

    def create(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return self._post(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return self._get(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return self._put(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return self._delete(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def patch(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return self._patch(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncLangfuseResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLangfuseResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncLangfuseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLangfuseResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncLangfuseResourceWithStreamingResponse(self)

    async def create(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return await self._post(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return await self._get(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return await self._put(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return await self._delete(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def patch(
        self,
        endpoint: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call Langfuse via LLM proxy.

        Works with Langfuse SDK.

        [Docs](https://docs.hanzo.ai/docs/pass_through/langfuse)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint:
            raise ValueError(f"Expected a non-empty value for `endpoint` but received {endpoint!r}")
        return await self._patch(
            f"/langfuse/{endpoint}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class LangfuseResourceWithRawResponse:
    def __init__(self, langfuse: LangfuseResource) -> None:
        self._langfuse = langfuse

        self.create = to_raw_response_wrapper(
            langfuse.create,
        )
        self.retrieve = to_raw_response_wrapper(
            langfuse.retrieve,
        )
        self.update = to_raw_response_wrapper(
            langfuse.update,
        )
        self.delete = to_raw_response_wrapper(
            langfuse.delete,
        )
        self.patch = to_raw_response_wrapper(
            langfuse.patch,
        )


class AsyncLangfuseResourceWithRawResponse:
    def __init__(self, langfuse: AsyncLangfuseResource) -> None:
        self._langfuse = langfuse

        self.create = async_to_raw_response_wrapper(
            langfuse.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            langfuse.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            langfuse.update,
        )
        self.delete = async_to_raw_response_wrapper(
            langfuse.delete,
        )
        self.patch = async_to_raw_response_wrapper(
            langfuse.patch,
        )


class LangfuseResourceWithStreamingResponse:
    def __init__(self, langfuse: LangfuseResource) -> None:
        self._langfuse = langfuse

        self.create = to_streamed_response_wrapper(
            langfuse.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            langfuse.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            langfuse.update,
        )
        self.delete = to_streamed_response_wrapper(
            langfuse.delete,
        )
        self.patch = to_streamed_response_wrapper(
            langfuse.patch,
        )


class AsyncLangfuseResourceWithStreamingResponse:
    def __init__(self, langfuse: AsyncLangfuseResource) -> None:
        self._langfuse = langfuse

        self.create = async_to_streamed_response_wrapper(
            langfuse.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            langfuse.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            langfuse.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            langfuse.delete,
        )
        self.patch = async_to_streamed_response_wrapper(
            langfuse.patch,
        )
