# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import (
    maybe_transform,
    async_maybe_transform,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.global_ import spend_list_tags_params, spend_retrieve_report_params
from ...types.global_.spend_list_tags_response import SpendListTagsResponse
from ...types.global_.spend_retrieve_report_response import SpendRetrieveReportResponse

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

    def list_tags(
        self,
        *,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        tags: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListTagsResponse:
        """LLM Enterprise - View Spend Per Request Tag.

        Used by LLM UI

        Example Request:

        ```
        curl -X GET "http://0.0.0.0:4000/spend/tags" -H "Authorization: Bearer sk-1234"
        ```

        Spend with Start Date and End Date

        ```
        curl -X GET "http://0.0.0.0:4000/spend/tags?start_date=2022-01-01&end_date=2022-02-01" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          end_date: Time till which to view key spend

          start_date: Time from which to start viewing key spend

          tags: comman separated tags to filter on

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/global/spend/tags",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "tags": tags,
                    },
                    spend_list_tags_params.SpendListTagsParams,
                ),
            ),
            cast_to=SpendListTagsResponse,
        )

    def reset(
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
        ADMIN ONLY / MASTER KEY Only Endpoint

        Globally reset spend for All API Keys and Teams, maintain LLM_SpendLogs

        1. LLM_SpendLogs will maintain the logs on spend, no data gets deleted from
           there
        2. LLM_VerificationTokens spend will be set = 0
        3. LLM_TeamTable spend will be set = 0
        """
        return self._post(
            "/global/spend/reset",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve_report(
        self,
        *,
        api_key: Optional[str] | NotGiven = NOT_GIVEN,
        customer_id: Optional[str] | NotGiven = NOT_GIVEN,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        group_by: Optional[Literal["team", "customer", "api_key"]] | NotGiven = NOT_GIVEN,
        internal_user_id: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendRetrieveReportResponse:
        """Get Daily Spend per Team, based on specific startTime and endTime.

        Per team,
        view usage by each key, model [ { "group-by-day": "2024-05-10", "teams": [ {
        "team_name": "team-1" "spend": 10, "keys": [ "key": "1213", "usage": {
        "model-1": { "cost": 12.50, "input_tokens": 1000, "output_tokens": 5000,
        "requests": 100 }, "audio-modelname1": { "cost": 25.50, "seconds": 25,
        "requests": 50 }, } } ] ] }

        Args:
          api_key: View spend for a specific api_key. Example api_key='sk-1234

          customer_id: View spend for a specific customer_id. Example customer_id='1234. Can be used in
              conjunction with team_id as well.

          end_date: Time till which to view spend

          group_by: Group spend by internal team or customer or api_key

          internal_user_id: View spend for a specific internal_user_id. Example internal_user_id='1234

          start_date: Time from which to start viewing spend

          team_id: View spend for a specific team_id. Example team_id='1234

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/global/spend/report",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "api_key": api_key,
                        "customer_id": customer_id,
                        "end_date": end_date,
                        "group_by": group_by,
                        "internal_user_id": internal_user_id,
                        "start_date": start_date,
                        "team_id": team_id,
                    },
                    spend_retrieve_report_params.SpendRetrieveReportParams,
                ),
            ),
            cast_to=SpendRetrieveReportResponse,
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

    async def list_tags(
        self,
        *,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        tags: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendListTagsResponse:
        """LLM Enterprise - View Spend Per Request Tag.

        Used by LLM UI

        Example Request:

        ```
        curl -X GET "http://0.0.0.0:4000/spend/tags" -H "Authorization: Bearer sk-1234"
        ```

        Spend with Start Date and End Date

        ```
        curl -X GET "http://0.0.0.0:4000/spend/tags?start_date=2022-01-01&end_date=2022-02-01" -H "Authorization: Bearer sk-1234"
        ```

        Args:
          end_date: Time till which to view key spend

          start_date: Time from which to start viewing key spend

          tags: comman separated tags to filter on

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/global/spend/tags",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "tags": tags,
                    },
                    spend_list_tags_params.SpendListTagsParams,
                ),
            ),
            cast_to=SpendListTagsResponse,
        )

    async def reset(
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
        ADMIN ONLY / MASTER KEY Only Endpoint

        Globally reset spend for All API Keys and Teams, maintain LLM_SpendLogs

        1. LLM_SpendLogs will maintain the logs on spend, no data gets deleted from
           there
        2. LLM_VerificationTokens spend will be set = 0
        3. LLM_TeamTable spend will be set = 0
        """
        return await self._post(
            "/global/spend/reset",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve_report(
        self,
        *,
        api_key: Optional[str] | NotGiven = NOT_GIVEN,
        customer_id: Optional[str] | NotGiven = NOT_GIVEN,
        end_date: Optional[str] | NotGiven = NOT_GIVEN,
        group_by: Optional[Literal["team", "customer", "api_key"]] | NotGiven = NOT_GIVEN,
        internal_user_id: Optional[str] | NotGiven = NOT_GIVEN,
        start_date: Optional[str] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> SpendRetrieveReportResponse:
        """Get Daily Spend per Team, based on specific startTime and endTime.

        Per team,
        view usage by each key, model [ { "group-by-day": "2024-05-10", "teams": [ {
        "team_name": "team-1" "spend": 10, "keys": [ "key": "1213", "usage": {
        "model-1": { "cost": 12.50, "input_tokens": 1000, "output_tokens": 5000,
        "requests": 100 }, "audio-modelname1": { "cost": 25.50, "seconds": 25,
        "requests": 50 }, } } ] ] }

        Args:
          api_key: View spend for a specific api_key. Example api_key='sk-1234

          customer_id: View spend for a specific customer_id. Example customer_id='1234. Can be used in
              conjunction with team_id as well.

          end_date: Time till which to view spend

          group_by: Group spend by internal team or customer or api_key

          internal_user_id: View spend for a specific internal_user_id. Example internal_user_id='1234

          start_date: Time from which to start viewing spend

          team_id: View spend for a specific team_id. Example team_id='1234

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/global/spend/report",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "api_key": api_key,
                        "customer_id": customer_id,
                        "end_date": end_date,
                        "group_by": group_by,
                        "internal_user_id": internal_user_id,
                        "start_date": start_date,
                        "team_id": team_id,
                    },
                    spend_retrieve_report_params.SpendRetrieveReportParams,
                ),
            ),
            cast_to=SpendRetrieveReportResponse,
        )


class SpendResourceWithRawResponse:
    def __init__(self, spend: SpendResource) -> None:
        self._spend = spend

        self.list_tags = to_raw_response_wrapper(
            spend.list_tags,
        )
        self.reset = to_raw_response_wrapper(
            spend.reset,
        )
        self.retrieve_report = to_raw_response_wrapper(
            spend.retrieve_report,
        )


class AsyncSpendResourceWithRawResponse:
    def __init__(self, spend: AsyncSpendResource) -> None:
        self._spend = spend

        self.list_tags = async_to_raw_response_wrapper(
            spend.list_tags,
        )
        self.reset = async_to_raw_response_wrapper(
            spend.reset,
        )
        self.retrieve_report = async_to_raw_response_wrapper(
            spend.retrieve_report,
        )


class SpendResourceWithStreamingResponse:
    def __init__(self, spend: SpendResource) -> None:
        self._spend = spend

        self.list_tags = to_streamed_response_wrapper(
            spend.list_tags,
        )
        self.reset = to_streamed_response_wrapper(
            spend.reset,
        )
        self.retrieve_report = to_streamed_response_wrapper(
            spend.retrieve_report,
        )


class AsyncSpendResourceWithStreamingResponse:
    def __init__(self, spend: AsyncSpendResource) -> None:
        self._spend = spend

        self.list_tags = async_to_streamed_response_wrapper(
            spend.list_tags,
        )
        self.reset = async_to_streamed_response_wrapper(
            spend.reset,
        )
        self.retrieve_report = async_to_streamed_response_wrapper(
            spend.retrieve_report,
        )
