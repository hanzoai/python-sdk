# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import model_group_retrieve_info_params
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

__all__ = ["ModelGroupResource", "AsyncModelGroupResource"]


class ModelGroupResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ModelGroupResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ModelGroupResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModelGroupResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ModelGroupResourceWithStreamingResponse(self)

    def retrieve_info(
        self,
        *,
        model_group: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get information about all the deployments on llm proxy, including config.yaml
        descriptions (except api key and api base)

        - /model_group/info returns all model groups. End users of proxy should use
          /model_group/info since those models will be used for /chat/completions,
          /embeddings, etc.
        - /model_group/info?model_group=rerank-english-v3.0 returns all model groups for
          a specific model group (`model_name` in config.yaml)

        Example Request (All Models):

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info'     -H 'accept: application/json'     -H 'x-api-key: sk-1234'
        ```

        Example Request (Specific Model Group):

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info?model_group=rerank-english-v3.0'     -H 'accept: application/json'     -H 'Authorization: Bearer sk-1234'
        ```

        Example Request (Specific Wildcard Model Group): (e.g. `model_name: openai/*` on
        config.yaml)

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info?model_group=openai/tts-1'
        -H 'accept: application/json'     -H 'Authorization: Bearersk-1234'
        ```

        Learn how to use and set wildcard models
        [here](https://docs.hanzo.ai/docs/wildcard_routing)

        Example Response:

        ```json
        {
          "data": [
            {
              "model_group": "rerank-english-v3.0",
              "providers": ["cohere"],
              "max_input_tokens": null,
              "max_output_tokens": null,
              "input_cost_per_token": 0.0,
              "output_cost_per_token": 0.0,
              "mode": null,
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": false,
              "supports_function_calling": false,
              "supported_openai_params": [
                "stream",
                "temperature",
                "max_tokens",
                "logit_bias",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
                "stop",
                "n",
                "extra_headers"
              ]
            },
            {
              "model_group": "gpt-3.5-turbo",
              "providers": ["openai"],
              "max_input_tokens": 16385.0,
              "max_output_tokens": 4096.0,
              "input_cost_per_token": 1.5e-6,
              "output_cost_per_token": 2e-6,
              "mode": "chat",
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": false,
              "supports_function_calling": true,
              "supported_openai_params": [
                "frequency_penalty",
                "logit_bias",
                "logprobs",
                "top_logprobs",
                "max_tokens",
                "max_completion_tokens",
                "n",
                "presence_penalty",
                "seed",
                "stop",
                "stream",
                "stream_options",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
                "function_call",
                "functions",
                "max_retries",
                "extra_headers",
                "parallel_tool_calls",
                "response_format"
              ]
            },
            {
              "model_group": "llava-hf",
              "providers": ["openai"],
              "max_input_tokens": null,
              "max_output_tokens": null,
              "input_cost_per_token": 0.0,
              "output_cost_per_token": 0.0,
              "mode": null,
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": true,
              "supports_function_calling": false,
              "supported_openai_params": [
                "frequency_penalty",
                "logit_bias",
                "logprobs",
                "top_logprobs",
                "max_tokens",
                "max_completion_tokens",
                "n",
                "presence_penalty",
                "seed",
                "stop",
                "stream",
                "stream_options",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
                "function_call",
                "functions",
                "max_retries",
                "extra_headers",
                "parallel_tool_calls",
                "response_format"
              ]
            }
          ]
        }
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/model_group/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"model_group": model_group}, model_group_retrieve_info_params.ModelGroupRetrieveInfoParams
                ),
            ),
            cast_to=object,
        )


class AsyncModelGroupResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncModelGroupResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncModelGroupResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModelGroupResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncModelGroupResourceWithStreamingResponse(self)

    async def retrieve_info(
        self,
        *,
        model_group: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get information about all the deployments on llm proxy, including config.yaml
        descriptions (except api key and api base)

        - /model_group/info returns all model groups. End users of proxy should use
          /model_group/info since those models will be used for /chat/completions,
          /embeddings, etc.
        - /model_group/info?model_group=rerank-english-v3.0 returns all model groups for
          a specific model group (`model_name` in config.yaml)

        Example Request (All Models):

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info'     -H 'accept: application/json'     -H 'x-api-key: sk-1234'
        ```

        Example Request (Specific Model Group):

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info?model_group=rerank-english-v3.0'     -H 'accept: application/json'     -H 'Authorization: Bearer sk-1234'
        ```

        Example Request (Specific Wildcard Model Group): (e.g. `model_name: openai/*` on
        config.yaml)

        ```shell
        curl -X 'GET'     'http://localhost:4000/model_group/info?model_group=openai/tts-1'
        -H 'accept: application/json'     -H 'Authorization: Bearersk-1234'
        ```

        Learn how to use and set wildcard models
        [here](https://docs.hanzo.ai/docs/wildcard_routing)

        Example Response:

        ```json
        {
          "data": [
            {
              "model_group": "rerank-english-v3.0",
              "providers": ["cohere"],
              "max_input_tokens": null,
              "max_output_tokens": null,
              "input_cost_per_token": 0.0,
              "output_cost_per_token": 0.0,
              "mode": null,
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": false,
              "supports_function_calling": false,
              "supported_openai_params": [
                "stream",
                "temperature",
                "max_tokens",
                "logit_bias",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
                "stop",
                "n",
                "extra_headers"
              ]
            },
            {
              "model_group": "gpt-3.5-turbo",
              "providers": ["openai"],
              "max_input_tokens": 16385.0,
              "max_output_tokens": 4096.0,
              "input_cost_per_token": 1.5e-6,
              "output_cost_per_token": 2e-6,
              "mode": "chat",
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": false,
              "supports_function_calling": true,
              "supported_openai_params": [
                "frequency_penalty",
                "logit_bias",
                "logprobs",
                "top_logprobs",
                "max_tokens",
                "max_completion_tokens",
                "n",
                "presence_penalty",
                "seed",
                "stop",
                "stream",
                "stream_options",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
                "function_call",
                "functions",
                "max_retries",
                "extra_headers",
                "parallel_tool_calls",
                "response_format"
              ]
            },
            {
              "model_group": "llava-hf",
              "providers": ["openai"],
              "max_input_tokens": null,
              "max_output_tokens": null,
              "input_cost_per_token": 0.0,
              "output_cost_per_token": 0.0,
              "mode": null,
              "tpm": null,
              "rpm": null,
              "supports_parallel_function_calling": false,
              "supports_vision": true,
              "supports_function_calling": false,
              "supported_openai_params": [
                "frequency_penalty",
                "logit_bias",
                "logprobs",
                "top_logprobs",
                "max_tokens",
                "max_completion_tokens",
                "n",
                "presence_penalty",
                "seed",
                "stop",
                "stream",
                "stream_options",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
                "function_call",
                "functions",
                "max_retries",
                "extra_headers",
                "parallel_tool_calls",
                "response_format"
              ]
            }
          ]
        }
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/model_group/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"model_group": model_group}, model_group_retrieve_info_params.ModelGroupRetrieveInfoParams
                ),
            ),
            cast_to=object,
        )


class ModelGroupResourceWithRawResponse:
    def __init__(self, model_group: ModelGroupResource) -> None:
        self._model_group = model_group

        self.retrieve_info = to_raw_response_wrapper(
            model_group.retrieve_info,
        )


class AsyncModelGroupResourceWithRawResponse:
    def __init__(self, model_group: AsyncModelGroupResource) -> None:
        self._model_group = model_group

        self.retrieve_info = async_to_raw_response_wrapper(
            model_group.retrieve_info,
        )


class ModelGroupResourceWithStreamingResponse:
    def __init__(self, model_group: ModelGroupResource) -> None:
        self._model_group = model_group

        self.retrieve_info = to_streamed_response_wrapper(
            model_group.retrieve_info,
        )


class AsyncModelGroupResourceWithStreamingResponse:
    def __init__(self, model_group: AsyncModelGroupResource) -> None:
        self._model_group = model_group

        self.retrieve_info = async_to_streamed_response_wrapper(
            model_group.retrieve_info,
        )
