# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    customer_block_params,
    customer_create_params,
    customer_delete_params,
    customer_update_params,
    customer_unblock_params,
    customer_retrieve_info_params,
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
from ..types.customer_list_response import CustomerListResponse
from ..types.customer_retrieve_info_response import CustomerRetrieveInfoResponse

__all__ = ["CustomerResource", "AsyncCustomerResource"]


class CustomerResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CustomerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return CustomerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CustomerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return CustomerResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        user_id: str,
        alias: Optional[str] | NotGiven = NOT_GIVEN,
        allowed_model_region: Optional[Literal["eu", "us"]] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        default_model: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, customer_create_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
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
        Allow creating a new Customer

        Parameters:

        - user_id: str - The unique identifier for the user.
        - alias: Optional[str] - A human-friendly alias for the user.
        - blocked: bool - Flag to allow or disallow requests for this end-user. Default
          is False.
        - max_budget: Optional[float] - The maximum budget allocated to the user. Either
          'max_budget' or 'budget_id' should be provided, not both.
        - budget_id: Optional[str] - The identifier for an existing budget allocated to
          the user. Either 'max_budget' or 'budget_id' should be provided, not both.
        - allowed_model_region: Optional[Union[Literal["eu"], Literal["us"]]] - Require
          all user requests to use models in this specific region.
        - default_model: Optional[str] - If no equivalent model in the allowed region,
          default all requests to this model.
        - metadata: Optional[dict] = Metadata for customer, store information for
          customer. Example metadata = {"data_training_opt_out": True}
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
        - tpm_limit: Optional[int] - [Not Implemented Yet] Specify tpm limit for a given
          customer (Tokens per minute)
        - rpm_limit: Optional[int] - [Not Implemented Yet] Specify rpm limit for a given
          customer (Requests per minute)
        - model_max_budget: Optional[dict] - [Not Implemented Yet] Specify max budget
          for a given model. Example: {"openai/gpt-4o-mini": {"max_budget": 100.0,
          "budget_duration": "1d"}}
        - max_parallel_requests: Optional[int] - [Not Implemented Yet] Specify max
          parallel requests for a given customer.
        - soft_budget: Optional[float] - [Not Implemented Yet] Get alerts when customer
          crosses given budget, doesn't block requests.

        - Allow specifying allowed regions
        - Allow specifying default model

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/new'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "user_id" : "z-jaff-3",
                "allowed_region": "eu",
                "budget_id": "free_tier",
                "default_model": "azure/gpt-3.5-turbo-eu" <- all calls from this user, use this model?
            }'

            # return end-user object
        ```

        NOTE: This used to be called `/end_user/new`, we will still be maintaining
        compatibility for /end_user/XXX for these endpoints

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

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
            "/customer/new",
            body=maybe_transform(
                {
                    "user_id": user_id,
                    "alias": alias,
                    "allowed_model_region": allowed_model_region,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "default_model": default_model,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                customer_create_params.CustomerCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        *,
        user_id: str,
        alias: Optional[str] | NotGiven = NOT_GIVEN,
        allowed_model_region: Optional[Literal["eu", "us"]] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        default_model: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Example curl

        Parameters:

        - user_id: str
        - alias: Optional[str] = None # human-friendly alias
        - blocked: bool = False # allow/disallow requests for this end-user
        - max_budget: Optional[float] = None
        - budget_id: Optional[str] = None # give either a budget_id or max_budget
        - allowed_model_region: Optional[AllowedModelRegion] = ( None # require all user
          requests to use models in this specific region )
        - default_model: Optional[str] = ( None # if no equivalent model in allowed
          region - default all requests to this model )

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "user_id": "test-llm-user-4",
            "budget_id": "paid_tier"
        }'

        See below for all params
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/customer/update",
            body=maybe_transform(
                {
                    "user_id": user_id,
                    "alias": alias,
                    "allowed_model_region": allowed_model_region,
                    "blocked": blocked,
                    "budget_id": budget_id,
                    "default_model": default_model,
                    "max_budget": max_budget,
                },
                customer_update_params.CustomerUpdateParams,
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
    ) -> CustomerListResponse:
        """
        [Admin-only] List all available customers

        Example curl:

        ```
        curl --location --request GET 'http://0.0.0.0:4000/customer/list'         --header 'Authorization: Bearer sk-1234'
        ```
        """
        return self._get(
            "/customer/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomerListResponse,
        )

    def delete(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete multiple end-users.

        Parameters:

        - user_ids (List[str], required): The unique `user_id`s for the users to delete

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/delete'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "user_ids" :["z-jaff-5"]
        }'

        See below for all params
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/customer/delete",
            body=maybe_transform({"user_ids": user_ids}, customer_delete_params.CustomerDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def block(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [BETA] Reject calls with this end-user id

        Parameters:

        - user_ids (List[str], required): The unique `user_id`s for the users to block

          (any /chat/completion call with this user={end-user-id} param, will be
          rejected.)

          ```
          curl -X POST "http://0.0.0.0:8000/user/block"
          -H "Authorization: Bearer sk-1234"
          -d '{
          "user_ids": [<user_id>, ...]
          }'
          ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/customer/block",
            body=maybe_transform({"user_ids": user_ids}, customer_block_params.CustomerBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve_info(
        self,
        *,
        end_user_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CustomerRetrieveInfoResponse:
        """Get information about an end-user.

        An `end_user` is a customer (external user)
        of the proxy.

        Parameters:

        - end_user_id (str, required): The unique identifier for the end-user

        Example curl:

        ```
        curl -X GET 'http://localhost:4000/customer/info?end_user_id=test-llm-user-4'         -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          end_user_id: End User ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/customer/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"end_user_id": end_user_id}, customer_retrieve_info_params.CustomerRetrieveInfoParams
                ),
            ),
            cast_to=CustomerRetrieveInfoResponse,
        )

    def unblock(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [BETA] Unblock calls with this user id

        Example

        ```
        curl -X POST "http://0.0.0.0:8000/user/unblock"
        -H "Authorization: Bearer sk-1234"
        -d '{
        "user_ids": [<user_id>, ...]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/customer/unblock",
            body=maybe_transform({"user_ids": user_ids}, customer_unblock_params.CustomerUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCustomerResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCustomerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCustomerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCustomerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncCustomerResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        user_id: str,
        alias: Optional[str] | NotGiven = NOT_GIVEN,
        allowed_model_region: Optional[Literal["eu", "us"]] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        default_model: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[Dict[str, customer_create_params.ModelMaxBudget]] | NotGiven = NOT_GIVEN,
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
        Allow creating a new Customer

        Parameters:

        - user_id: str - The unique identifier for the user.
        - alias: Optional[str] - A human-friendly alias for the user.
        - blocked: bool - Flag to allow or disallow requests for this end-user. Default
          is False.
        - max_budget: Optional[float] - The maximum budget allocated to the user. Either
          'max_budget' or 'budget_id' should be provided, not both.
        - budget_id: Optional[str] - The identifier for an existing budget allocated to
          the user. Either 'max_budget' or 'budget_id' should be provided, not both.
        - allowed_model_region: Optional[Union[Literal["eu"], Literal["us"]]] - Require
          all user requests to use models in this specific region.
        - default_model: Optional[str] - If no equivalent model in the allowed region,
          default all requests to this model.
        - metadata: Optional[dict] = Metadata for customer, store information for
          customer. Example metadata = {"data_training_opt_out": True}
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
        - tpm_limit: Optional[int] - [Not Implemented Yet] Specify tpm limit for a given
          customer (Tokens per minute)
        - rpm_limit: Optional[int] - [Not Implemented Yet] Specify rpm limit for a given
          customer (Requests per minute)
        - model_max_budget: Optional[dict] - [Not Implemented Yet] Specify max budget
          for a given model. Example: {"openai/gpt-4o-mini": {"max_budget": 100.0,
          "budget_duration": "1d"}}
        - max_parallel_requests: Optional[int] - [Not Implemented Yet] Specify max
          parallel requests for a given customer.
        - soft_budget: Optional[float] - [Not Implemented Yet] Get alerts when customer
          crosses given budget, doesn't block requests.

        - Allow specifying allowed regions
        - Allow specifying default model

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/new'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "user_id" : "z-jaff-3",
                "allowed_region": "eu",
                "budget_id": "free_tier",
                "default_model": "azure/gpt-3.5-turbo-eu" <- all calls from this user, use this model?
            }'

            # return end-user object
        ```

        NOTE: This used to be called `/end_user/new`, we will still be maintaining
        compatibility for /end_user/XXX for these endpoints

        Args:
          budget_duration: Max duration budget should be set for (e.g. '1hr', '1d', '28d')

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
            "/customer/new",
            body=await async_maybe_transform(
                {
                    "user_id": user_id,
                    "alias": alias,
                    "allowed_model_region": allowed_model_region,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "default_model": default_model,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "model_max_budget": model_max_budget,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                customer_create_params.CustomerCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        *,
        user_id: str,
        alias: Optional[str] | NotGiven = NOT_GIVEN,
        allowed_model_region: Optional[Literal["eu", "us"]] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        default_model: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Example curl

        Parameters:

        - user_id: str
        - alias: Optional[str] = None # human-friendly alias
        - blocked: bool = False # allow/disallow requests for this end-user
        - max_budget: Optional[float] = None
        - budget_id: Optional[str] = None # give either a budget_id or max_budget
        - allowed_model_region: Optional[AllowedModelRegion] = ( None # require all user
          requests to use models in this specific region )
        - default_model: Optional[str] = ( None # if no equivalent model in allowed
          region - default all requests to this model )

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "user_id": "test-llm-user-4",
            "budget_id": "paid_tier"
        }'

        See below for all params
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/customer/update",
            body=await async_maybe_transform(
                {
                    "user_id": user_id,
                    "alias": alias,
                    "allowed_model_region": allowed_model_region,
                    "blocked": blocked,
                    "budget_id": budget_id,
                    "default_model": default_model,
                    "max_budget": max_budget,
                },
                customer_update_params.CustomerUpdateParams,
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
    ) -> CustomerListResponse:
        """
        [Admin-only] List all available customers

        Example curl:

        ```
        curl --location --request GET 'http://0.0.0.0:4000/customer/list'         --header 'Authorization: Bearer sk-1234'
        ```
        """
        return await self._get(
            "/customer/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomerListResponse,
        )

    async def delete(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete multiple end-users.

        Parameters:

        - user_ids (List[str], required): The unique `user_id`s for the users to delete

        Example curl:

        ```
        curl --location 'http://0.0.0.0:4000/customer/delete'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "user_ids" :["z-jaff-5"]
        }'

        See below for all params
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/customer/delete",
            body=await async_maybe_transform({"user_ids": user_ids}, customer_delete_params.CustomerDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def block(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [BETA] Reject calls with this end-user id

        Parameters:

        - user_ids (List[str], required): The unique `user_id`s for the users to block

          (any /chat/completion call with this user={end-user-id} param, will be
          rejected.)

          ```
          curl -X POST "http://0.0.0.0:8000/user/block"
          -H "Authorization: Bearer sk-1234"
          -d '{
          "user_ids": [<user_id>, ...]
          }'
          ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/customer/block",
            body=await async_maybe_transform({"user_ids": user_ids}, customer_block_params.CustomerBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve_info(
        self,
        *,
        end_user_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CustomerRetrieveInfoResponse:
        """Get information about an end-user.

        An `end_user` is a customer (external user)
        of the proxy.

        Parameters:

        - end_user_id (str, required): The unique identifier for the end-user

        Example curl:

        ```
        curl -X GET 'http://localhost:4000/customer/info?end_user_id=test-llm-user-4'         -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          end_user_id: End User ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/customer/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"end_user_id": end_user_id}, customer_retrieve_info_params.CustomerRetrieveInfoParams
                ),
            ),
            cast_to=CustomerRetrieveInfoResponse,
        )

    async def unblock(
        self,
        *,
        user_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [BETA] Unblock calls with this user id

        Example

        ```
        curl -X POST "http://0.0.0.0:8000/user/unblock"
        -H "Authorization: Bearer sk-1234"
        -d '{
        "user_ids": [<user_id>, ...]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/customer/unblock",
            body=await async_maybe_transform({"user_ids": user_ids}, customer_unblock_params.CustomerUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CustomerResourceWithRawResponse:
    def __init__(self, customer: CustomerResource) -> None:
        self._customer = customer

        self.create = to_raw_response_wrapper(
            customer.create,
        )
        self.update = to_raw_response_wrapper(
            customer.update,
        )
        self.list = to_raw_response_wrapper(
            customer.list,
        )
        self.delete = to_raw_response_wrapper(
            customer.delete,
        )
        self.block = to_raw_response_wrapper(
            customer.block,
        )
        self.retrieve_info = to_raw_response_wrapper(
            customer.retrieve_info,
        )
        self.unblock = to_raw_response_wrapper(
            customer.unblock,
        )


class AsyncCustomerResourceWithRawResponse:
    def __init__(self, customer: AsyncCustomerResource) -> None:
        self._customer = customer

        self.create = async_to_raw_response_wrapper(
            customer.create,
        )
        self.update = async_to_raw_response_wrapper(
            customer.update,
        )
        self.list = async_to_raw_response_wrapper(
            customer.list,
        )
        self.delete = async_to_raw_response_wrapper(
            customer.delete,
        )
        self.block = async_to_raw_response_wrapper(
            customer.block,
        )
        self.retrieve_info = async_to_raw_response_wrapper(
            customer.retrieve_info,
        )
        self.unblock = async_to_raw_response_wrapper(
            customer.unblock,
        )


class CustomerResourceWithStreamingResponse:
    def __init__(self, customer: CustomerResource) -> None:
        self._customer = customer

        self.create = to_streamed_response_wrapper(
            customer.create,
        )
        self.update = to_streamed_response_wrapper(
            customer.update,
        )
        self.list = to_streamed_response_wrapper(
            customer.list,
        )
        self.delete = to_streamed_response_wrapper(
            customer.delete,
        )
        self.block = to_streamed_response_wrapper(
            customer.block,
        )
        self.retrieve_info = to_streamed_response_wrapper(
            customer.retrieve_info,
        )
        self.unblock = to_streamed_response_wrapper(
            customer.unblock,
        )


class AsyncCustomerResourceWithStreamingResponse:
    def __init__(self, customer: AsyncCustomerResource) -> None:
        self._customer = customer

        self.create = async_to_streamed_response_wrapper(
            customer.create,
        )
        self.update = async_to_streamed_response_wrapper(
            customer.update,
        )
        self.list = async_to_streamed_response_wrapper(
            customer.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            customer.delete,
        )
        self.block = async_to_streamed_response_wrapper(
            customer.block,
        )
        self.retrieve_info = async_to_streamed_response_wrapper(
            customer.retrieve_info,
        )
        self.unblock = async_to_streamed_response_wrapper(
            customer.unblock,
        )
