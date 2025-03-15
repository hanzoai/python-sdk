# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Optional

import httpx

from ..types import (
    budget_info_params,
    budget_create_params,
    budget_delete_params,
    budget_update_params,
    budget_settings_params,
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

__all__ = ["BudgetResource", "AsyncBudgetResource"]


class BudgetResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BudgetResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return BudgetResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BudgetResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return BudgetResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, budget_create_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new budget object.

        Can apply this to teams, orgs, end-users, keys.

        Parameters:

        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - budget_id: Optional[str] - The id of the budget. If not provided, a new id
          will be generated.
        - max_budget: Optional[float] - The max budget for the budget.
        - soft_budget: Optional[float] - The soft budget for the budget.
        - max_parallel_requests: Optional[int] - The max number of parallel requests for
          the budget.
        - tpm_limit: Optional[int] - The tokens per minute limit for the budget.
        - rpm_limit: Optional[int] - The requests per minute limit for the budget.
        - model_max_budget: Optional[dict] - Specify max budget for a given model.
          Example: {"openai/gpt-4o-mini": {"max_budget": 100.0, "budget_duration": "1d",
          "tpm_limit": 100000, "rpm_limit": 100000}}

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

          budget_id: The unique budget id.

          max_budget: Requests will fail if this budget (in USD) is exceeded.

          max_parallel_requests: Max concurrent requests allowed for this budget id.

          model_max_budget: Max budget for each model (e.g. {'gpt-4o': {'max_budget': '0.0000001',
              'budget_duration': '1d', 'tpm_limit': 1000, 'rpm_limit': 1000}})

          rpm_limit: Max requests per minute, allowed for this budget id.

          soft_budget: Requests will NOT fail if this is exceeded. Will fire alerting though.

          tpm_limit: Max tokens per minute, allowed for this budget id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/budget/new",
            body=maybe_transform(
                {
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                budget_create_params.BudgetCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        *,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, budget_update_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing budget object.

        Parameters:

        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - budget_id: Optional[str] - The id of the budget. If not provided, a new id
          will be generated.
        - max_budget: Optional[float] - The max budget for the budget.
        - soft_budget: Optional[float] - The soft budget for the budget.
        - max_parallel_requests: Optional[int] - The max number of parallel requests for
          the budget.
        - tpm_limit: Optional[int] - The tokens per minute limit for the budget.
        - rpm_limit: Optional[int] - The requests per minute limit for the budget.
        - model_max_budget: Optional[dict] - Specify max budget for a given model.
          Example: {"openai/gpt-4o-mini": {"max_budget": 100.0, "budget_duration": "1d",
          "tpm_limit": 100000, "rpm_limit": 100000}}

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

          budget_id: The unique budget id.

          max_budget: Requests will fail if this budget (in USD) is exceeded.

          max_parallel_requests: Max concurrent requests allowed for this budget id.

          model_max_budget: Max budget for each model (e.g. {'gpt-4o': {'max_budget': '0.0000001',
              'budget_duration': '1d', 'tpm_limit': 1000, 'rpm_limit': 1000}})

          rpm_limit: Max requests per minute, allowed for this budget id.

          soft_budget: Requests will NOT fail if this is exceeded. Will fire alerting though.

          tpm_limit: Max tokens per minute, allowed for this budget id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/budget/update",
            body=maybe_transform(
                {
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                budget_update_params.BudgetUpdateParams,
            ),
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
        """List all the created budgets in proxy db. Used on Admin UI."""
        return self._get(
            "/budget/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete budget

        Parameters:

        - id: str - The budget id to delete

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/budget/delete",
            body=maybe_transform({"id": id}, budget_delete_params.BudgetDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def info(
        self,
        *,
        budgets: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get the budget id specific information

        Parameters:

        - budgets: List[str] - The list of budget ids to get information for

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/budget/info",
            body=maybe_transform({"budgets": budgets}, budget_info_params.BudgetInfoParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def settings(
        self,
        *,
        budget_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get list of configurable params + current value for a budget item + description
        of each field

        Used on Admin UI.

        Query Parameters:

        - budget_id: str - The budget id to get information for

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/budget/settings",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"budget_id": budget_id}, budget_settings_params.BudgetSettingsParams),
            ),
            cast_to=object,
        )


class AsyncBudgetResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBudgetResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncBudgetResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBudgetResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncBudgetResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, budget_create_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new budget object.

        Can apply this to teams, orgs, end-users, keys.

        Parameters:

        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - budget_id: Optional[str] - The id of the budget. If not provided, a new id
          will be generated.
        - max_budget: Optional[float] - The max budget for the budget.
        - soft_budget: Optional[float] - The soft budget for the budget.
        - max_parallel_requests: Optional[int] - The max number of parallel requests for
          the budget.
        - tpm_limit: Optional[int] - The tokens per minute limit for the budget.
        - rpm_limit: Optional[int] - The requests per minute limit for the budget.
        - model_max_budget: Optional[dict] - Specify max budget for a given model.
          Example: {"openai/gpt-4o-mini": {"max_budget": 100.0, "budget_duration": "1d",
          "tpm_limit": 100000, "rpm_limit": 100000}}

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

          budget_id: The unique budget id.

          max_budget: Requests will fail if this budget (in USD) is exceeded.

          max_parallel_requests: Max concurrent requests allowed for this budget id.

          model_max_budget: Max budget for each model (e.g. {'gpt-4o': {'max_budget': '0.0000001',
              'budget_duration': '1d', 'tpm_limit': 1000, 'rpm_limit': 1000}})

          rpm_limit: Max requests per minute, allowed for this budget id.

          soft_budget: Requests will NOT fail if this is exceeded. Will fire alerting though.

          tpm_limit: Max tokens per minute, allowed for this budget id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/budget/new",
            body=await async_maybe_transform(
                {
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                budget_create_params.BudgetCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        *,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, budget_update_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing budget object.

        Parameters:

        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - budget_id: Optional[str] - The id of the budget. If not provided, a new id
          will be generated.
        - max_budget: Optional[float] - The max budget for the budget.
        - soft_budget: Optional[float] - The soft budget for the budget.
        - max_parallel_requests: Optional[int] - The max number of parallel requests for
          the budget.
        - tpm_limit: Optional[int] - The tokens per minute limit for the budget.
        - rpm_limit: Optional[int] - The requests per minute limit for the budget.
        - model_max_budget: Optional[dict] - Specify max budget for a given model.
          Example: {"openai/gpt-4o-mini": {"max_budget": 100.0, "budget_duration": "1d",
          "tpm_limit": 100000, "rpm_limit": 100000}}

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

          budget_id: The unique budget id.

          max_budget: Requests will fail if this budget (in USD) is exceeded.

          max_parallel_requests: Max concurrent requests allowed for this budget id.

          model_max_budget: Max budget for each model (e.g. {'gpt-4o': {'max_budget': '0.0000001',
              'budget_duration': '1d', 'tpm_limit': 1000, 'rpm_limit': 1000}})

          rpm_limit: Max requests per minute, allowed for this budget id.

          soft_budget: Requests will NOT fail if this is exceeded. Will fire alerting though.

          tpm_limit: Max tokens per minute, allowed for this budget id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/budget/update",
            body=await async_maybe_transform(
                {
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                budget_update_params.BudgetUpdateParams,
            ),
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
        """List all the created budgets in proxy db. Used on Admin UI."""
        return await self._get(
            "/budget/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete budget

        Parameters:

        - id: str - The budget id to delete

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/budget/delete",
            body=await async_maybe_transform({"id": id}, budget_delete_params.BudgetDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def info(
        self,
        *,
        budgets: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get the budget id specific information

        Parameters:

        - budgets: List[str] - The list of budget ids to get information for

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/budget/info",
            body=await async_maybe_transform({"budgets": budgets}, budget_info_params.BudgetInfoParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def settings(
        self,
        *,
        budget_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get list of configurable params + current value for a budget item + description
        of each field

        Used on Admin UI.

        Query Parameters:

        - budget_id: str - The budget id to get information for

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/budget/settings",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"budget_id": budget_id}, budget_settings_params.BudgetSettingsParams
                ),
            ),
            cast_to=object,
        )


class BudgetResourceWithRawResponse:
    def __init__(self, budget: BudgetResource) -> None:
        self._budget = budget

        self.create = to_raw_response_wrapper(
            budget.create,
        )
        self.update = to_raw_response_wrapper(
            budget.update,
        )
        self.list = to_raw_response_wrapper(
            budget.list,
        )
        self.delete = to_raw_response_wrapper(
            budget.delete,
        )
        self.info = to_raw_response_wrapper(
            budget.info,
        )
        self.settings = to_raw_response_wrapper(
            budget.settings,
        )


class AsyncBudgetResourceWithRawResponse:
    def __init__(self, budget: AsyncBudgetResource) -> None:
        self._budget = budget

        self.create = async_to_raw_response_wrapper(
            budget.create,
        )
        self.update = async_to_raw_response_wrapper(
            budget.update,
        )
        self.list = async_to_raw_response_wrapper(
            budget.list,
        )
        self.delete = async_to_raw_response_wrapper(
            budget.delete,
        )
        self.info = async_to_raw_response_wrapper(
            budget.info,
        )
        self.settings = async_to_raw_response_wrapper(
            budget.settings,
        )


class BudgetResourceWithStreamingResponse:
    def __init__(self, budget: BudgetResource) -> None:
        self._budget = budget

        self.create = to_streamed_response_wrapper(
            budget.create,
        )
        self.update = to_streamed_response_wrapper(
            budget.update,
        )
        self.list = to_streamed_response_wrapper(
            budget.list,
        )
        self.delete = to_streamed_response_wrapper(
            budget.delete,
        )
        self.info = to_streamed_response_wrapper(
            budget.info,
        )
        self.settings = to_streamed_response_wrapper(
            budget.settings,
        )


class AsyncBudgetResourceWithStreamingResponse:
    def __init__(self, budget: AsyncBudgetResource) -> None:
        self._budget = budget

        self.create = async_to_streamed_response_wrapper(
            budget.create,
        )
        self.update = async_to_streamed_response_wrapper(
            budget.update,
        )
        self.list = async_to_streamed_response_wrapper(
            budget.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            budget.delete,
        )
        self.info = async_to_streamed_response_wrapper(
            budget.info,
        )
        self.settings = async_to_streamed_response_wrapper(
            budget.settings,
        )
