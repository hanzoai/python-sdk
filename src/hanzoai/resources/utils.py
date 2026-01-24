# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal

import httpx

from ..types import util_token_counter_params, util_transform_request_params, util_get_supported_openai_params_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
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
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Returns supported openai params for a given litellm model name

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
        call_endpoint: bool | Omit = omit,
        contents: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        messages: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UtilTokenCounterResponse:
        """
        Args: request: TokenCountRequest call_endpoint: bool - When set to "True" it
        will call the token counting endpoint - e.g Anthropic or Google AI Studio Token
        Counting APIs.

        Returns: TokenCountResponse

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
                    "contents": contents,
                    "messages": messages,
                    "prompt": prompt,
                },
                util_token_counter_params.UtilTokenCounterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"call_endpoint": call_endpoint}, util_token_counter_params.UtilTokenCounterParams
                ),
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
            "image_edit",
            "aimage_edit",
            "moderation",
            "amoderation",
            "atranscription",
            "transcription",
            "aspeech",
            "speech",
            "rerank",
            "arerank",
            "search",
            "asearch",
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
            "create_video",
            "acreate_video",
            "avideo_retrieve",
            "video_retrieve",
            "avideo_content",
            "video_content",
            "video_remix",
            "avideo_remix",
            "video_list",
            "avideo_list",
            "video_retrieve_job",
            "avideo_retrieve_job",
            "video_delete",
            "avideo_delete",
            "vector_store_file_create",
            "avector_store_file_create",
            "vector_store_file_list",
            "avector_store_file_list",
            "vector_store_file_retrieve",
            "avector_store_file_retrieve",
            "vector_store_file_content",
            "avector_store_file_content",
            "vector_store_file_update",
            "avector_store_file_update",
            "vector_store_file_delete",
            "avector_store_file_delete",
            "vector_store_create",
            "avector_store_create",
            "vector_store_search",
            "avector_store_search",
            "create_container",
            "acreate_container",
            "list_containers",
            "alist_containers",
            "retrieve_container",
            "aretrieve_container",
            "delete_container",
            "adelete_container",
            "list_container_files",
            "alist_container_files",
            "upload_container_file",
            "aupload_container_file",
            "acancel_fine_tuning_job",
            "cancel_fine_tuning_job",
            "alist_fine_tuning_jobs",
            "list_fine_tuning_jobs",
            "aretrieve_fine_tuning_job",
            "retrieve_fine_tuning_job",
            "responses",
            "aresponses",
            "alist_input_items",
            "llm_passthrough_route",
            "allm_passthrough_route",
            "generate_content",
            "agenerate_content",
            "generate_content_stream",
            "agenerate_content_stream",
            "ocr",
            "aocr",
            "call_mcp_tool",
            "asend_message",
            "send_message",
            "acreate_skill",
        ],
        request_body: Dict[str, object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Returns supported openai params for a given litellm model name

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
        call_endpoint: bool | Omit = omit,
        contents: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        messages: Optional[Iterable[Dict[str, object]]] | Omit = omit,
        prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UtilTokenCounterResponse:
        """
        Args: request: TokenCountRequest call_endpoint: bool - When set to "True" it
        will call the token counting endpoint - e.g Anthropic or Google AI Studio Token
        Counting APIs.

        Returns: TokenCountResponse

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
                    "contents": contents,
                    "messages": messages,
                    "prompt": prompt,
                },
                util_token_counter_params.UtilTokenCounterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"call_endpoint": call_endpoint}, util_token_counter_params.UtilTokenCounterParams
                ),
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
            "image_edit",
            "aimage_edit",
            "moderation",
            "amoderation",
            "atranscription",
            "transcription",
            "aspeech",
            "speech",
            "rerank",
            "arerank",
            "search",
            "asearch",
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
            "create_video",
            "acreate_video",
            "avideo_retrieve",
            "video_retrieve",
            "avideo_content",
            "video_content",
            "video_remix",
            "avideo_remix",
            "video_list",
            "avideo_list",
            "video_retrieve_job",
            "avideo_retrieve_job",
            "video_delete",
            "avideo_delete",
            "vector_store_file_create",
            "avector_store_file_create",
            "vector_store_file_list",
            "avector_store_file_list",
            "vector_store_file_retrieve",
            "avector_store_file_retrieve",
            "vector_store_file_content",
            "avector_store_file_content",
            "vector_store_file_update",
            "avector_store_file_update",
            "vector_store_file_delete",
            "avector_store_file_delete",
            "vector_store_create",
            "avector_store_create",
            "vector_store_search",
            "avector_store_search",
            "create_container",
            "acreate_container",
            "list_containers",
            "alist_containers",
            "retrieve_container",
            "aretrieve_container",
            "delete_container",
            "adelete_container",
            "list_container_files",
            "alist_container_files",
            "upload_container_file",
            "aupload_container_file",
            "acancel_fine_tuning_job",
            "cancel_fine_tuning_job",
            "alist_fine_tuning_jobs",
            "list_fine_tuning_jobs",
            "aretrieve_fine_tuning_job",
            "retrieve_fine_tuning_job",
            "responses",
            "aresponses",
            "alist_input_items",
            "llm_passthrough_route",
            "allm_passthrough_route",
            "generate_content",
            "agenerate_content",
            "generate_content_stream",
            "agenerate_content_stream",
            "ocr",
            "aocr",
            "call_mcp_tool",
            "asend_message",
            "send_message",
            "acreate_skill",
        ],
        request_body: Dict[str, object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
