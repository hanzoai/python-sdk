# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional

import httpx

from .chat import (
    ChatResource,
    AsyncChatResource,
    ChatResourceWithRawResponse,
    AsyncChatResourceWithRawResponse,
    ChatResourceWithStreamingResponse,
    AsyncChatResourceWithStreamingResponse,
)
from ...types import engine_embed_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options

__all__ = ["EnginesResource", "AsyncEnginesResource"]


class EnginesResource(SyncAPIResource):
    @cached_property
    def chat(self) -> ChatResource:
        return ChatResource(self._client)

    @cached_property
    def with_raw_response(self) -> EnginesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return EnginesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EnginesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return EnginesResourceWithStreamingResponse(self)

    def complete(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
            f"/engines/{model}/completions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def embed(
        self,
        path_model: str,
        *,
        body_model: str,
        api_base: Optional[str] | Omit = omit,
        api_key: Optional[str] | Omit = omit,
        api_type: Optional[str] | Omit = omit,
        api_version: Optional[str] | Omit = omit,
        caching: bool | Omit = omit,
        custom_llm_provider: Union[str, Dict[str, object], None] | Omit = omit,
        input: SequenceNotStr[str] | Omit = omit,
        litellm_call_id: Optional[str] | Omit = omit,
        litellm_logging_obj: Optional[Dict[str, object]] | Omit = omit,
        logger_fn: Optional[str] | Omit = omit,
        api_timeout: int | Omit = omit,
        user: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
        if not path_model:
            raise ValueError(f"Expected a non-empty value for `path_model` but received {path_model!r}")
        return self._post(
            f"/engines/{path_model}/embeddings",
            body=maybe_transform(
                {
                    "body_model": body_model,
                    "api_base": api_base,
                    "api_key": api_key,
                    "api_type": api_type,
                    "api_version": api_version,
                    "caching": caching,
                    "custom_llm_provider": custom_llm_provider,
                    "input": input,
                    "litellm_call_id": litellm_call_id,
                    "litellm_logging_obj": litellm_logging_obj,
                    "logger_fn": logger_fn,
                    "api_timeout": api_timeout,
                    "user": user,
                },
                engine_embed_params.EngineEmbedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncEnginesResource(AsyncAPIResource):
    @cached_property
    def chat(self) -> AsyncChatResource:
        return AsyncChatResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncEnginesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncEnginesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEnginesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncEnginesResourceWithStreamingResponse(self)

    async def complete(
        self,
        model: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
            f"/engines/{model}/completions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def embed(
        self,
        path_model: str,
        *,
        body_model: str,
        api_base: Optional[str] | Omit = omit,
        api_key: Optional[str] | Omit = omit,
        api_type: Optional[str] | Omit = omit,
        api_version: Optional[str] | Omit = omit,
        caching: bool | Omit = omit,
        custom_llm_provider: Union[str, Dict[str, object], None] | Omit = omit,
        input: SequenceNotStr[str] | Omit = omit,
        litellm_call_id: Optional[str] | Omit = omit,
        litellm_logging_obj: Optional[Dict[str, object]] | Omit = omit,
        logger_fn: Optional[str] | Omit = omit,
        api_timeout: int | Omit = omit,
        user: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
        if not path_model:
            raise ValueError(f"Expected a non-empty value for `path_model` but received {path_model!r}")
        return await self._post(
            f"/engines/{path_model}/embeddings",
            body=await async_maybe_transform(
                {
                    "body_model": body_model,
                    "api_base": api_base,
                    "api_key": api_key,
                    "api_type": api_type,
                    "api_version": api_version,
                    "caching": caching,
                    "custom_llm_provider": custom_llm_provider,
                    "input": input,
                    "litellm_call_id": litellm_call_id,
                    "litellm_logging_obj": litellm_logging_obj,
                    "logger_fn": logger_fn,
                    "api_timeout": api_timeout,
                    "user": user,
                },
                engine_embed_params.EngineEmbedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class EnginesResourceWithRawResponse:
    def __init__(self, engines: EnginesResource) -> None:
        self._engines = engines

        self.complete = to_raw_response_wrapper(
            engines.complete,
        )
        self.embed = to_raw_response_wrapper(
            engines.embed,
        )

    @cached_property
    def chat(self) -> ChatResourceWithRawResponse:
        return ChatResourceWithRawResponse(self._engines.chat)


class AsyncEnginesResourceWithRawResponse:
    def __init__(self, engines: AsyncEnginesResource) -> None:
        self._engines = engines

        self.complete = async_to_raw_response_wrapper(
            engines.complete,
        )
        self.embed = async_to_raw_response_wrapper(
            engines.embed,
        )

    @cached_property
    def chat(self) -> AsyncChatResourceWithRawResponse:
        return AsyncChatResourceWithRawResponse(self._engines.chat)


class EnginesResourceWithStreamingResponse:
    def __init__(self, engines: EnginesResource) -> None:
        self._engines = engines

        self.complete = to_streamed_response_wrapper(
            engines.complete,
        )
        self.embed = to_streamed_response_wrapper(
            engines.embed,
        )

    @cached_property
    def chat(self) -> ChatResourceWithStreamingResponse:
        return ChatResourceWithStreamingResponse(self._engines.chat)


class AsyncEnginesResourceWithStreamingResponse:
    def __init__(self, engines: AsyncEnginesResource) -> None:
        self._engines = engines

        self.complete = async_to_streamed_response_wrapper(
            engines.complete,
        )
        self.embed = async_to_streamed_response_wrapper(
            engines.embed,
        )

    @cached_property
    def chat(self) -> AsyncChatResourceWithStreamingResponse:
        return AsyncChatResourceWithStreamingResponse(self._engines.chat)
