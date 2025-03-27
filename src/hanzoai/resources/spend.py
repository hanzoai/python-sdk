# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional

import httpx

from ..types import spend_list_logs_params, spend_list_tags_params, spend_calculate_spend_params
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
from ..types.spend_list_logs_response import SpendListLogsResponse
from ..types.spend_list_tags_response import SpendListTagsResponse

__all__ = ["SpendResource", "AsyncSpendResource"]


class SpendResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SpendResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return SpendResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SpendResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return SpendResourceWithStreamingResponse(self)

    def calculate_spend(
        self,
        *,
        completion_response: Optional[object] | NotGiven = NOT_GIVEN,
        messages: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        model: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Accepts all the params of completion_cost.

        Calculate spend **before** making call:

        Note: If you see a spend of $0.0 you need to set custom_pricing for your model:
        https://docs.hanzo.ai/docs/proxy/custom_pricing

        ```
        curl --location 'http://localhost:4000/spend/calculate'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "model": "anthropic.claude-v2",
            "messages": [{"role": "user", "content": "Hey, how'''s it going?"}]
        }'
        ```

        Calculate spend **after** making call:

        ```
        curl --location 'http://localhost:4000/spend/calculate'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "completion_response": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-3.5-turbo-0125",
                "system_fingerprint": "fp_44709d6fcb",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there, how may I assist you today?"
                    },
                    "logprobs": null,
                    "finish_reason": "stop"
                }]
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 12,
                    "total_tokens": 21
                }
            }
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/spend/calculate",
            body=maybe_transform(
                {
                    "completion_response": completion_response,
                    "messages": messages,
                    "model": model,
                },
                spend_calculate_spend_params.SpendCalculateSpendParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_logs(
        self,
        *,
        api_key: Optional[str] | NotGiven = NOT_GIVEN,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        request_id: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListLogsResponse:
        """
        View all spend logs, if request_id is provided, only logs for that request_id
        will be returned

        Example Request for all logs

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific request_id

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?request_id=chatcmpl-6dcb2540-d3d7-4e49-bb27-291f863f112e" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific api_key

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?api_key=sk-Fn8Ej39NkBQmUagFEoUWPQ" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific user_id

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?user_id=z@hanzo.ai" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          api_key: Get spend logs based on api key

          end_date: Time till which to view key spend

          request_id: request_id to get spend logs for specific request_id. If none passed then pass
              spend logs for all requests

          start_date: Time from which to start viewing key spend

          user_id: Get spend logs based on user_id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/spend/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "api_key": api_key,
                        "end_date": end_date,
                        "request_id": request_id,
                        "start_date": start_date,
                        "user_id": user_id,
                    },
                    spend_list_logs_params.SpendListLogsParams,
                ),
            ),
            cast_to=SpendListLogsResponse,
        )

    def list_tags(
        self,
        *,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListTagsResponse:
        """
        LLM Enterprise - View Spend Per Request Tag

        Example Request:

        ```
        curl -X GET "http://0.0.0.0:8000/spend/tags" -H "Authorization: Bearer sk-1234"
        ```

        Spend with Start Date and End Date

        ```
        curl -X GET "http://0.0.0.0:8000/spend/tags?start_date=2022-01-01&end_date=2022-02-01" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          end_date: Time till which to view key spend

          start_date: Time from which to start viewing key spend

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/spend/tags",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                    },
                    spend_list_tags_params.SpendListTagsParams,
                ),
            ),
            cast_to=SpendListTagsResponse,
        )


class AsyncSpendResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSpendResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSpendResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSpendResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncSpendResourceWithStreamingResponse(self)

    async def calculate_spend(
        self,
        *,
        completion_response: Optional[object] | NotGiven = NOT_GIVEN,
        messages: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        model: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Accepts all the params of completion_cost.

        Calculate spend **before** making call:

        Note: If you see a spend of $0.0 you need to set custom_pricing for your model:
        https://docs.hanzo.ai/docs/proxy/custom_pricing

        ```
        curl --location 'http://localhost:4000/spend/calculate'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "model": "anthropic.claude-v2",
            "messages": [{"role": "user", "content": "Hey, how'''s it going?"}]
        }'
        ```

        Calculate spend **after** making call:

        ```
        curl --location 'http://localhost:4000/spend/calculate'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "completion_response": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-3.5-turbo-0125",
                "system_fingerprint": "fp_44709d6fcb",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there, how may I assist you today?"
                    },
                    "logprobs": null,
                    "finish_reason": "stop"
                }]
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 12,
                    "total_tokens": 21
                }
            }
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/spend/calculate",
            body=await async_maybe_transform(
                {
                    "completion_response": completion_response,
                    "messages": messages,
                    "model": model,
                },
                spend_calculate_spend_params.SpendCalculateSpendParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_logs(
        self,
        *,
        api_key: Optional[str] | NotGiven = NOT_GIVEN,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        request_id: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListLogsResponse:
        """
        View all spend logs, if request_id is provided, only logs for that request_id
        will be returned

        Example Request for all logs

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific request_id

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?request_id=chatcmpl-6dcb2540-d3d7-4e49-bb27-291f863f112e" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific api_key

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?api_key=sk-Fn8Ej39NkBQmUagFEoUWPQ" -H "Authorization: Bearer sk-1234"
        ```

        Example Request for specific user_id

        ```
        curl -X GET "http://0.0.0.0:8000/spend/logs?user_id=z@hanzo.ai" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          api_key: Get spend logs based on api key

          end_date: Time till which to view key spend

          request_id: request_id to get spend logs for specific request_id. If none passed then pass
              spend logs for all requests

          start_date: Time from which to start viewing key spend

          user_id: Get spend logs based on user_id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/spend/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "api_key": api_key,
                        "end_date": end_date,
                        "request_id": request_id,
                        "start_date": start_date,
                        "user_id": user_id,
                    },
                    spend_list_logs_params.SpendListLogsParams,
                ),
            ),
            cast_to=SpendListLogsResponse,
        )

    async def list_tags(
        self,
        *,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListTagsResponse:
        """
        LLM Enterprise - View Spend Per Request Tag

        Example Request:

        ```
        curl -X GET "http://0.0.0.0:8000/spend/tags" -H "Authorization: Bearer sk-1234"
        ```

        Spend with Start Date and End Date

        ```
        curl -X GET "http://0.0.0.0:8000/spend/tags?start_date=2022-01-01&end_date=2022-02-01" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          end_date: Time till which to view key spend

          start_date: Time from which to start viewing key spend

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/spend/tags",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                    },
                    spend_list_tags_params.SpendListTagsParams,
                ),
            ),
            cast_to=SpendListTagsResponse,
        )


class SpendResourceWithRawResponse:
    def __init__(self, spend: SpendResource) -> None:
        self._spend = spend

        self.calculate_spend = to_raw_response_wrapper(
            spend.calculate_spend,
        )
        self.list_logs = to_raw_response_wrapper(
            spend.list_logs,
        )
        self.list_tags = to_raw_response_wrapper(
            spend.list_tags,
        )


class AsyncSpendResourceWithRawResponse:
    def __init__(self, spend: AsyncSpendResource) -> None:
        self._spend = spend

        self.calculate_spend = async_to_raw_response_wrapper(
            spend.calculate_spend,
        )
        self.list_logs = async_to_raw_response_wrapper(
            spend.list_logs,
        )
        self.list_tags = async_to_raw_response_wrapper(
            spend.list_tags,
        )


class SpendResourceWithStreamingResponse:
    def __init__(self, spend: SpendResource) -> None:
        self._spend = spend

        self.calculate_spend = to_streamed_response_wrapper(
            spend.calculate_spend,
        )
        self.list_logs = to_streamed_response_wrapper(
            spend.list_logs,
        )
        self.list_tags = to_streamed_response_wrapper(
            spend.list_tags,
        )


class AsyncSpendResourceWithStreamingResponse:
    def __init__(self, spend: AsyncSpendResource) -> None:
        self._spend = spend

        self.calculate_spend = async_to_streamed_response_wrapper(
            spend.calculate_spend,
        )
        self.list_logs = async_to_streamed_response_wrapper(
            spend.list_logs,
        )
        self.list_tags = async_to_streamed_response_wrapper(
            spend.list_tags,
        )
