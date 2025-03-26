# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    util_token_counter_params,
    util_transform_request_params,
    util_get_supported_openai_params_params,
)
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
from ..types.util_token_counter_response import UtilTokenCounterResponse
from ..types.util_transform_request_response import UtilTransformRequestResponse

__all__ = ["UtilsResource", "AsyncUtilsResource"]


class UtilsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UtilsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return UtilsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UtilsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return UtilsResourceWithStreamingResponse(self)

    def get_supported_openai_params(
        self,
        *,
        model: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Returns supported openai params for a given llm model name

        e.g.

        `gpt-4` vs `gpt-3.5-turbo`

        Example curl:

        ```
        curl -X GET --location 'http://localhost:4000/utils/supported_openai_params?model=gpt-3.5-turbo-16k'         --header 'Authorization: Bearer sk-1234'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/utils/supported_openai_params",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"model": model}, util_get_supported_openai_params_params.UtilGetSupportedOpenAIParamsParams
                ),
            ),
            cast_to=object,
        )

    def token_counter(
        self,
        *,
        model: str,
        messages: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        prompt: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UtilTokenCounterResponse:
        """
        Token Counter

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/utils/token_counter",
            body=maybe_transform(
                {
                    "model": model,
                    "messages": messages,
                    "prompt": prompt,
                },
                util_token_counter_params.UtilTokenCounterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UtilTokenCounterResponse,
        )

    def transform_request(
        self,
        *,
        call_type: Literal[
            "embedding",
            "aembedding",
            "completion",
            "acompletion",
            "atext_completion",
            "text_completion",
            "image_generation",
            "aimage_generation",
            "moderation",
            "amoderation",
            "atranscription",
            "transcription",
            "aspeech",
            "speech",
            "rerank",
            "arerank",
            "_arealtime",
            "create_batch",
            "acreate_batch",
            "aretrieve_batch",
            "retrieve_batch",
            "pass_through_endpoint",
            "anthropic_messages",
            "get_assistants",
            "aget_assistants",
            "create_assistants",
            "acreate_assistants",
            "delete_assistant",
            "adelete_assistant",
            "acreate_thread",
            "create_thread",
            "aget_thread",
            "get_thread",
            "a_add_message",
            "add_message",
            "aget_messages",
            "get_messages",
            "arun_thread",
            "run_thread",
            "arun_thread_stream",
            "run_thread_stream",
            "afile_retrieve",
            "file_retrieve",
            "afile_delete",
            "file_delete",
            "afile_list",
            "file_list",
            "acreate_file",
            "create_file",
            "afile_content",
            "file_content",
            "create_fine_tuning_job",
            "acreate_fine_tuning_job",
            "acancel_fine_tuning_job",
            "cancel_fine_tuning_job",
            "alist_fine_tuning_jobs",
            "list_fine_tuning_jobs",
            "aretrieve_fine_tuning_job",
            "retrieve_fine_tuning_job",
            "responses",
            "aresponses",
        ],
        request_body: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UtilTransformRequestResponse:
        """
        Transform Request

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/utils/transform_request",
            body=maybe_transform(
                {
                    "call_type": call_type,
                    "request_body": request_body,
                },
                util_transform_request_params.UtilTransformRequestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UtilTransformRequestResponse,
        )


class AsyncUtilsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUtilsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncUtilsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUtilsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncUtilsResourceWithStreamingResponse(self)

    async def get_supported_openai_params(
        self,
        *,
        model: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Returns supported openai params for a given llm model name

        e.g.

        `gpt-4` vs `gpt-3.5-turbo`

        Example curl:

        ```
        curl -X GET --location 'http://localhost:4000/utils/supported_openai_params?model=gpt-3.5-turbo-16k'         --header 'Authorization: Bearer sk-1234'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/utils/supported_openai_params",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"model": model}, util_get_supported_openai_params_params.UtilGetSupportedOpenAIParamsParams
                ),
            ),
            cast_to=object,
        )

    async def token_counter(
        self,
        *,
        model: str,
        messages: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        prompt: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UtilTokenCounterResponse:
        """
        Token Counter

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/utils/token_counter",
            body=await async_maybe_transform(
                {
                    "model": model,
                    "messages": messages,
                    "prompt": prompt,
                },
                util_token_counter_params.UtilTokenCounterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UtilTokenCounterResponse,
        )

    async def transform_request(
        self,
        *,
        call_type: Literal[
            "embedding",
            "aembedding",
            "completion",
            "acompletion",
            "atext_completion",
            "text_completion",
            "image_generation",
            "aimage_generation",
            "moderation",
            "amoderation",
            "atranscription",
            "transcription",
            "aspeech",
            "speech",
            "rerank",
            "arerank",
            "_arealtime",
            "create_batch",
            "acreate_batch",
            "aretrieve_batch",
            "retrieve_batch",
            "pass_through_endpoint",
            "anthropic_messages",
            "get_assistants",
            "aget_assistants",
            "create_assistants",
            "acreate_assistants",
            "delete_assistant",
            "adelete_assistant",
            "acreate_thread",
            "create_thread",
            "aget_thread",
            "get_thread",
            "a_add_message",
            "add_message",
            "aget_messages",
            "get_messages",
            "arun_thread",
            "run_thread",
            "arun_thread_stream",
            "run_thread_stream",
            "afile_retrieve",
            "file_retrieve",
            "afile_delete",
            "file_delete",
            "afile_list",
            "file_list",
            "acreate_file",
            "create_file",
            "afile_content",
            "file_content",
            "create_fine_tuning_job",
            "acreate_fine_tuning_job",
            "acancel_fine_tuning_job",
            "cancel_fine_tuning_job",
            "alist_fine_tuning_jobs",
            "list_fine_tuning_jobs",
            "aretrieve_fine_tuning_job",
            "retrieve_fine_tuning_job",
            "responses",
            "aresponses",
        ],
        request_body: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UtilTransformRequestResponse:
        """
        Transform Request

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/utils/transform_request",
            body=await async_maybe_transform(
                {
                    "call_type": call_type,
                    "request_body": request_body,
                },
                util_transform_request_params.UtilTransformRequestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UtilTransformRequestResponse,
        )


class UtilsResourceWithRawResponse:
    def __init__(self, utils: UtilsResource) -> None:
        self._utils = utils

        self.get_supported_openai_params = to_raw_response_wrapper(
            utils.get_supported_openai_params,
        )
        self.token_counter = to_raw_response_wrapper(
            utils.token_counter,
        )
        self.transform_request = to_raw_response_wrapper(
            utils.transform_request,
        )


class AsyncUtilsResourceWithRawResponse:
    def __init__(self, utils: AsyncUtilsResource) -> None:
        self._utils = utils

        self.get_supported_openai_params = async_to_raw_response_wrapper(
            utils.get_supported_openai_params,
        )
        self.token_counter = async_to_raw_response_wrapper(
            utils.token_counter,
        )
        self.transform_request = async_to_raw_response_wrapper(
            utils.transform_request,
        )


class UtilsResourceWithStreamingResponse:
    def __init__(self, utils: UtilsResource) -> None:
        self._utils = utils

        self.get_supported_openai_params = to_streamed_response_wrapper(
            utils.get_supported_openai_params,
        )
        self.token_counter = to_streamed_response_wrapper(
            utils.token_counter,
        )
        self.transform_request = to_streamed_response_wrapper(
            utils.transform_request,
        )


class AsyncUtilsResourceWithStreamingResponse:
    def __init__(self, utils: AsyncUtilsResource) -> None:
        self._utils = utils

        self.get_supported_openai_params = async_to_streamed_response_wrapper(
            utils.get_supported_openai_params,
        )
        self.token_counter = async_to_streamed_response_wrapper(
            utils.token_counter,
        )
        self.transform_request = async_to_streamed_response_wrapper(
            utils.transform_request,
        )
