# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .chat import (
    ChatResource,
    AsyncChatResource,
    ChatResourceWithRawResponse,
    AsyncChatResourceWithRawResponse,
    ChatResourceWithStreamingResponse,
    AsyncChatResourceWithStreamingResponse,
)
from ...._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options

__all__ = ["DeploymentsResource", "AsyncDeploymentsResource"]


class DeploymentsResource(SyncAPIResource):
    @cached_property
    def chat(self) -> ChatResource:
        return ChatResource(self._client)

    @cached_property
    def with_raw_response(self) -> DeploymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeploymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return DeploymentsResourceWithStreamingResponse(self)

    def complete(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Follows the exact same API spec as
        `OpenAI's Completions API https://platform.openai.com/docs/api-reference/completions`

        ```bash
        curl -X POST http://localhost:4000/v1/completions
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "gpt-3.5-turbo-instruct",
            "prompt": "Once upon a time",
            "max_tokens": 50,
            "temperature": 0.7
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model:
            raise ValueError(f"Expected a non-empty value for `model` but received {model!r}")
        return self._post(
            f"/openai/deployments/{model}/completions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def embed(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Follows the exact same API spec as
        `OpenAI's Embeddings API https://platform.openai.com/docs/api-reference/embeddings`

        ```bash
        curl -X POST http://localhost:4000/v1/embeddings
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "text-embedding-ada-002",
            "input": "The quick brown fox jumps over the lazy dog"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model:
            raise ValueError(f"Expected a non-empty value for `model` but received {model!r}")
        return self._post(
            f"/openai/deployments/{model}/embeddings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncDeploymentsResource(AsyncAPIResource):
    @cached_property
    def chat(self) -> AsyncChatResource:
        return AsyncChatResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDeploymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeploymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncDeploymentsResourceWithStreamingResponse(self)

    async def complete(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Follows the exact same API spec as
        `OpenAI's Completions API https://platform.openai.com/docs/api-reference/completions`

        ```bash
        curl -X POST http://localhost:4000/v1/completions
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "gpt-3.5-turbo-instruct",
            "prompt": "Once upon a time",
            "max_tokens": 50,
            "temperature": 0.7
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model:
            raise ValueError(f"Expected a non-empty value for `model` but received {model!r}")
        return await self._post(
            f"/openai/deployments/{model}/completions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def embed(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Follows the exact same API spec as
        `OpenAI's Embeddings API https://platform.openai.com/docs/api-reference/embeddings`

        ```bash
        curl -X POST http://localhost:4000/v1/embeddings
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "text-embedding-ada-002",
            "input": "The quick brown fox jumps over the lazy dog"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model:
            raise ValueError(f"Expected a non-empty value for `model` but received {model!r}")
        return await self._post(
            f"/openai/deployments/{model}/embeddings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class DeploymentsResourceWithRawResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments

        self.complete = to_raw_response_wrapper(
            deployments.complete,
        )
        self.embed = to_raw_response_wrapper(
            deployments.embed,
        )

    @cached_property
    def chat(self) -> ChatResourceWithRawResponse:
        return ChatResourceWithRawResponse(self._deployments.chat)


class AsyncDeploymentsResourceWithRawResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments

        self.complete = async_to_raw_response_wrapper(
            deployments.complete,
        )
        self.embed = async_to_raw_response_wrapper(
            deployments.embed,
        )

    @cached_property
    def chat(self) -> AsyncChatResourceWithRawResponse:
        return AsyncChatResourceWithRawResponse(self._deployments.chat)


class DeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments

        self.complete = to_streamed_response_wrapper(
            deployments.complete,
        )
        self.embed = to_streamed_response_wrapper(
            deployments.embed,
        )

    @cached_property
    def chat(self) -> ChatResourceWithStreamingResponse:
        return ChatResourceWithStreamingResponse(self._deployments.chat)


class AsyncDeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments

        self.complete = async_to_streamed_response_wrapper(
            deployments.complete,
        )
        self.embed = async_to_streamed_response_wrapper(
            deployments.embed,
        )

    @cached_property
    def chat(self) -> AsyncChatResourceWithStreamingResponse:
        return AsyncChatResourceWithStreamingResponse(self._deployments.chat)
