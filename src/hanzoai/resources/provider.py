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
from ..types.provider_list_budgets_response import ProviderListBudgetsResponse

__all__ = ["ProviderResource", "AsyncProviderResource"]


class ProviderResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ProviderResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ProviderResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProviderResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ProviderResourceWithStreamingResponse(self)

    def list_budgets(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ProviderListBudgetsResponse:
        """
        Provider Budget Routing - Get Budget, Spend Details
        https://docs.hanzo.ai/docs/proxy/provider_budget_routing

        Use this endpoint to check current budget, spend and budget reset time for a
        provider

        Example Request

        ```bash
        curl -X GET http://localhost:4000/provider/budgets     -H "Content-Type: application/json"     -H "Authorization: Bearer sk-1234"
        ```

        Example Response

        ```json
        {
          "providers": {
            "openai": {
              "budget_limit": 1e-12,
              "time_period": "1d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "azure": {
              "budget_limit": 100.0,
              "time_period": "1d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "anthropic": {
              "budget_limit": 100.0,
              "time_period": "10d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "vertex_ai": {
              "budget_limit": 100.0,
              "time_period": "12d",
              "spend": 0.0,
              "budget_reset_at": null
            }
          }
        }
        ```
        """
        return self._get(
            "/provider/budgets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProviderListBudgetsResponse,
        )


class AsyncProviderResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncProviderResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncProviderResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProviderResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncProviderResourceWithStreamingResponse(self)

    async def list_budgets(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ProviderListBudgetsResponse:
        """
        Provider Budget Routing - Get Budget, Spend Details
        https://docs.hanzo.ai/docs/proxy/provider_budget_routing

        Use this endpoint to check current budget, spend and budget reset time for a
        provider

        Example Request

        ```bash
        curl -X GET http://localhost:4000/provider/budgets     -H "Content-Type: application/json"     -H "Authorization: Bearer sk-1234"
        ```

        Example Response

        ```json
        {
          "providers": {
            "openai": {
              "budget_limit": 1e-12,
              "time_period": "1d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "azure": {
              "budget_limit": 100.0,
              "time_period": "1d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "anthropic": {
              "budget_limit": 100.0,
              "time_period": "10d",
              "spend": 0.0,
              "budget_reset_at": null
            },
            "vertex_ai": {
              "budget_limit": 100.0,
              "time_period": "12d",
              "spend": 0.0,
              "budget_reset_at": null
            }
          }
        }
        ```
        """
        return await self._get(
            "/provider/budgets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProviderListBudgetsResponse,
        )


class ProviderResourceWithRawResponse:
    def __init__(self, provider: ProviderResource) -> None:
        self._provider = provider

        self.list_budgets = to_raw_response_wrapper(
            provider.list_budgets,
        )


class AsyncProviderResourceWithRawResponse:
    def __init__(self, provider: AsyncProviderResource) -> None:
        self._provider = provider

        self.list_budgets = async_to_raw_response_wrapper(
            provider.list_budgets,
        )


class ProviderResourceWithStreamingResponse:
    def __init__(self, provider: ProviderResource) -> None:
        self._provider = provider

        self.list_budgets = to_streamed_response_wrapper(
            provider.list_budgets,
        )


class AsyncProviderResourceWithStreamingResponse:
    def __init__(self, provider: AsyncProviderResource) -> None:
        self._provider = provider

        self.list_budgets = async_to_streamed_response_wrapper(
            provider.list_budgets,
        )
