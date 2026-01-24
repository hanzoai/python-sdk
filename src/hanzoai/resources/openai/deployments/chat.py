# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.openai.deployments import chat_complete_params

__all__ = ["ChatResource", "AsyncChatResource"]


class ChatResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ChatResourceWithStreamingResponse(self)

    def complete(
        self,
        path_model: str,
        *,
        messages: Iterable[chat_complete_params.Message],
        body_model: str,
        caching: Optional[bool] | Omit = omit,
        context_window_fallback_dict: Optional[Dict[str, str]] | Omit = omit,
        fallbacks: Optional[SequenceNotStr[str]] | Omit = omit,
        frequency_penalty: Optional[float] | Omit = omit,
        function_call: Union[str, Dict[str, object], None] | Omit = omit,
        functions: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        guardrails: Optional[SequenceNotStr[str]] | Omit = omit,
        logit_bias: Optional[Dict[str, float]] | Omit = omit,
        logprobs: Optional[bool] | Omit = omit,
        max_tokens: Optional[int] | Omit = omit,
        metadata: Optional[Dict[str, object]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        num_retries: Optional[int] | Omit = omit,
        parallel_tool_calls: Optional[bool] | Omit = omit,
        presence_penalty: Optional[float] | Omit = omit,
        response_format: Optional[Dict[str, object]] | Omit = omit,
        seed: Optional[int] | Omit = omit,
        service_tier: Optional[str] | Omit = omit,
        stop: Union[str, SequenceNotStr[str], None] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        stream_options: Optional[Dict[str, object]] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        tool_choice: Union[str, Dict[str, object], None] | Omit = omit,
        tools: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        top_logprobs: Optional[int] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
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
        `OpenAI's Chat API https://platform.openai.com/docs/api-reference/chat`

        ```bash
        curl -X POST http://localhost:4000/v1/chat/completions
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
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
            f"/openai/deployments/{path_model}/chat/completions",
            body=maybe_transform(
                {
                    "messages": messages,
                    "body_model": body_model,
                    "caching": caching,
                    "context_window_fallback_dict": context_window_fallback_dict,
                    "fallbacks": fallbacks,
                    "frequency_penalty": frequency_penalty,
                    "function_call": function_call,
                    "functions": functions,
                    "guardrails": guardrails,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "num_retries": num_retries,
                    "parallel_tool_calls": parallel_tool_calls,
                    "presence_penalty": presence_penalty,
                    "response_format": response_format,
                    "seed": seed,
                    "service_tier": service_tier,
                    "stop": stop,
                    "stream": stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                },
                chat_complete_params.ChatCompleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncChatResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncChatResourceWithStreamingResponse(self)

    async def complete(
        self,
        path_model: str,
        *,
        messages: Iterable[chat_complete_params.Message],
        body_model: str,
        caching: Optional[bool] | Omit = omit,
        context_window_fallback_dict: Optional[Dict[str, str]] | Omit = omit,
        fallbacks: Optional[SequenceNotStr[str]] | Omit = omit,
        frequency_penalty: Optional[float] | Omit = omit,
        function_call: Union[str, Dict[str, object], None] | Omit = omit,
        functions: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        guardrails: Optional[SequenceNotStr[str]] | Omit = omit,
        logit_bias: Optional[Dict[str, float]] | Omit = omit,
        logprobs: Optional[bool] | Omit = omit,
        max_tokens: Optional[int] | Omit = omit,
        metadata: Optional[Dict[str, object]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        num_retries: Optional[int] | Omit = omit,
        parallel_tool_calls: Optional[bool] | Omit = omit,
        presence_penalty: Optional[float] | Omit = omit,
        response_format: Optional[Dict[str, object]] | Omit = omit,
        seed: Optional[int] | Omit = omit,
        service_tier: Optional[str] | Omit = omit,
        stop: Union[str, SequenceNotStr[str], None] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        stream_options: Optional[Dict[str, object]] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        tool_choice: Union[str, Dict[str, object], None] | Omit = omit,
        tools: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        top_logprobs: Optional[int] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
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
        `OpenAI's Chat API https://platform.openai.com/docs/api-reference/chat`

        ```bash
        curl -X POST http://localhost:4000/v1/chat/completions
        -H "Content-Type: application/json"
        -H "Authorization: Bearer sk-1234"
        -d '{
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
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
            f"/openai/deployments/{path_model}/chat/completions",
            body=await async_maybe_transform(
                {
                    "messages": messages,
                    "body_model": body_model,
                    "caching": caching,
                    "context_window_fallback_dict": context_window_fallback_dict,
                    "fallbacks": fallbacks,
                    "frequency_penalty": frequency_penalty,
                    "function_call": function_call,
                    "functions": functions,
                    "guardrails": guardrails,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "num_retries": num_retries,
                    "parallel_tool_calls": parallel_tool_calls,
                    "presence_penalty": presence_penalty,
                    "response_format": response_format,
                    "seed": seed,
                    "service_tier": service_tier,
                    "stop": stop,
                    "stream": stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                },
                chat_complete_params.ChatCompleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class ChatResourceWithRawResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.complete = to_raw_response_wrapper(
            chat.complete,
        )


class AsyncChatResourceWithRawResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.complete = async_to_raw_response_wrapper(
            chat.complete,
        )


class ChatResourceWithStreamingResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.complete = to_streamed_response_wrapper(
            chat.complete,
        )


class AsyncChatResourceWithStreamingResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.complete = async_to_streamed_response_wrapper(
            chat.complete,
        )
