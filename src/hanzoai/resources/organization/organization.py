# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Literal

import httpx

from .info import (
    InfoResource,
    AsyncInfoResource,
    InfoResourceWithRawResponse,
    AsyncInfoResourceWithRawResponse,
    InfoResourceWithStreamingResponse,
    AsyncInfoResourceWithStreamingResponse,
)
from ...types import (
    organization_create_params,
    organization_delete_params,
    organization_update_params,
    organization_add_member_params,
    organization_delete_member_params,
    organization_update_member_params,
)
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
from ...types.organization_list_response import OrganizationListResponse
from ...types.organization_create_response import OrganizationCreateResponse
from ...types.organization_delete_response import OrganizationDeleteResponse
from ...types.organization_update_response import OrganizationUpdateResponse
from ...types.organization_add_member_response import OrganizationAddMemberResponse
from ...types.organization_update_member_response import OrganizationUpdateMemberResponse

__all__ = ["OrganizationResource", "AsyncOrganizationResource"]


class OrganizationResource(SyncAPIResource):
    @cached_property
    def info(self) -> InfoResource:
        return InfoResource(self._client)

    @cached_property
    def with_raw_response(self) -> OrganizationResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return OrganizationResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OrganizationResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return OrganizationResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        organization_alias: str,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        models: Iterable[object] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationCreateResponse:
        """
        Allow orgs to own teams

        Set org level budgets + model access.

        Only admins can create orgs.

        # Parameters

        - organization_alias: _str_ - The name of the organization.
        - models: _List_ - The models the organization has access to.
        - budget_id: _Optional[str]_ - The id for a budget (tpm/rpm/max budget) for the
          organization.

        ### IF NO BUDGET ID - CREATE ONE WITH THESE PARAMS

        - max_budget: _Optional[float]_ - Max budget for org
        - tpm_limit: _Optional[int]_ - Max tpm limit for org
        - rpm_limit: _Optional[int]_ - Max rpm limit for org
        - max_parallel_requests: _Optional[int]_ - [Not Implemented Yet] Max parallel
          requests for org
        - soft_budget: _Optional[float]_ - [Not Implemented Yet] Get a slack alert when
          this soft budget is reached. Don't block requests.
        - model_max_budget: _Optional[dict]_ - Max budget for a specific model
        - budget_duration: _Optional[str]_ - Frequency of reseting org budget
        - metadata: _Optional[dict]_ - Metadata for organization, store information for
          organization. Example metadata - {"extra_info": "some info"}
        - blocked: _bool_ - Flag indicating if the org is blocked or not - will stop all
          calls from keys with this org_id.
        - tags: _Optional[List[str]]_ - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: _Optional[str]_ - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)

        Case 1: Create new org **without** a budget_id

        ```bash
        curl --location 'http://0.0.0.0:4000/organization/new'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "organization_alias": "my-secret-org",
            "models": ["model1", "model2"],
            "max_budget": 100
        }'


        ```

        Case 2: Create new org **with** a budget_id

        ```bash
        curl --location 'http://0.0.0.0:4000/organization/new'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "organization_alias": "my-secret-org",
            "models": ["model1", "model2"],
            "budget_id": "428eeaa8-f3ac-4e85-a8fb-7dc8d7aa8689"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/organization/new",
            body=maybe_transform(
                {
                    "organization_alias": organization_alias,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                organization_create_params.OrganizationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationCreateResponse,
        )

    def update(
        self,
        *,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[List[str]] | NotGiven = NOT_GIVEN,
        organization_alias: Optional[str] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        updated_by: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationUpdateResponse:
        """
        Update an organization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/organization/update",
            body=maybe_transform(
                {
                    "budget_id": budget_id,
                    "metadata": metadata,
                    "models": models,
                    "organization_alias": organization_alias,
                    "organization_id": organization_id,
                    "spend": spend,
                    "updated_by": updated_by,
                },
                organization_update_params.OrganizationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationUpdateResponse,
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
    ) -> OrganizationListResponse:
        """
        ```
        curl --location --request GET 'http://0.0.0.0:4000/organization/list'         --header 'Authorization: Bearer sk-1234'
        ```
        """
        return self._get(
            "/organization/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationListResponse,
        )

    def delete(
        self,
        *,
        organization_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationDeleteResponse:
        """
        Delete an organization

        # Parameters:

        - organization_ids: List[str] - The organization ids to delete.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._delete(
            "/organization/delete",
            body=maybe_transform(
                {"organization_ids": organization_ids}, organization_delete_params.OrganizationDeleteParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationDeleteResponse,
        )

    def add_member(
        self,
        *,
        member: organization_add_member_params.Member,
        organization_id: str,
        max_budget_in_organization: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationAddMemberResponse:
        """
        [BETA]

        Add new members (either via user_email or user_id) to an organization

        If user doesn't exist, new user row will also be added to User Table

        Only proxy_admin or org_admin of organization, allowed to access this endpoint.

        # Parameters:

        - organization_id: str (required)
        - member: Union[List[Member], Member] (required)
          - role: Literal[LLMUserRoles] (required)
          - user_id: Optional[str]
          - user_email: Optional[str]

        Note: Either user_id or user_email must be provided for each member.

        Example:

        ```
        curl -X POST 'http://0.0.0.0:4000/organization/member_add'     -H 'Authorization: Bearer sk-1234'     -H 'Content-Type: application/json'     -d '{
            "organization_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849",
            "member": {
                "role": "internal_user",
                "user_id": "dev247652@hanzo.ai"
            },
            "max_budget_in_organization": 100.0
        }'
        ```

        The following is executed in this function:

        1. Check if organization exists
        2. Creates a new Internal User if the user_id or user_email is not found in
           LLM_UserTable
        3. Add Internal User to the `LLM_OrganizationMembership` table

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/organization/member_add",
            body=maybe_transform(
                {
                    "member": member,
                    "organization_id": organization_id,
                    "max_budget_in_organization": max_budget_in_organization,
                },
                organization_add_member_params.OrganizationAddMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationAddMemberResponse,
        )

    def delete_member(
        self,
        *,
        organization_id: str,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a member from an organization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._delete(
            "/organization/member_delete",
            body=maybe_transform(
                {
                    "organization_id": organization_id,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                organization_delete_member_params.OrganizationDeleteMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update_member(
        self,
        *,
        organization_id: str,
        max_budget_in_organization: Optional[float] | NotGiven = NOT_GIVEN,
        role: Optional[
            Literal[
                "proxy_admin",
                "proxy_admin_viewer",
                "org_admin",
                "internal_user",
                "internal_user_viewer",
                "team",
                "customer",
            ]
        ]
        | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationUpdateMemberResponse:
        """
        Update a member's role in an organization

        Args:
          role: Admin Roles: PROXY_ADMIN: admin over the platform PROXY_ADMIN_VIEW_ONLY: can
              login, view all own keys, view all spend ORG_ADMIN: admin over a specific
              organization, can create teams, users only within their organization

              Internal User Roles: INTERNAL_USER: can login, view/create/delete their own
              keys, view their spend INTERNAL_USER_VIEW_ONLY: can login, view their own keys,
              view their own spend

              Team Roles: TEAM: used for JWT auth

              Customer Roles: CUSTOMER: External users -> these are customers

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/organization/member_update",
            body=maybe_transform(
                {
                    "organization_id": organization_id,
                    "max_budget_in_organization": max_budget_in_organization,
                    "role": role,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                organization_update_member_params.OrganizationUpdateMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationUpdateMemberResponse,
        )


class AsyncOrganizationResource(AsyncAPIResource):
    @cached_property
    def info(self) -> AsyncInfoResource:
        return AsyncInfoResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncOrganizationResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncOrganizationResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOrganizationResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncOrganizationResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        organization_alias: str,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        models: Iterable[object] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationCreateResponse:
        """
        Allow orgs to own teams

        Set org level budgets + model access.

        Only admins can create orgs.

        # Parameters

        - organization_alias: _str_ - The name of the organization.
        - models: _List_ - The models the organization has access to.
        - budget_id: _Optional[str]_ - The id for a budget (tpm/rpm/max budget) for the
          organization.

        ### IF NO BUDGET ID - CREATE ONE WITH THESE PARAMS

        - max_budget: _Optional[float]_ - Max budget for org
        - tpm_limit: _Optional[int]_ - Max tpm limit for org
        - rpm_limit: _Optional[int]_ - Max rpm limit for org
        - max_parallel_requests: _Optional[int]_ - [Not Implemented Yet] Max parallel
          requests for org
        - soft_budget: _Optional[float]_ - [Not Implemented Yet] Get a slack alert when
          this soft budget is reached. Don't block requests.
        - model_max_budget: _Optional[dict]_ - Max budget for a specific model
        - budget_duration: _Optional[str]_ - Frequency of reseting org budget
        - metadata: _Optional[dict]_ - Metadata for organization, store information for
          organization. Example metadata - {"extra_info": "some info"}
        - blocked: _bool_ - Flag indicating if the org is blocked or not - will stop all
          calls from keys with this org_id.
        - tags: _Optional[List[str]]_ - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: _Optional[str]_ - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)

        Case 1: Create new org **without** a budget_id

        ```bash
        curl --location 'http://0.0.0.0:4000/organization/new'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "organization_alias": "my-secret-org",
            "models": ["model1", "model2"],
            "max_budget": 100
        }'


        ```

        Case 2: Create new org **with** a budget_id

        ```bash
        curl --location 'http://0.0.0.0:4000/organization/new'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data '{
            "organization_alias": "my-secret-org",
            "models": ["model1", "model2"],
            "budget_id": "428eeaa8-f3ac-4e85-a8fb-7dc8d7aa8689"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/organization/new",
            body=await async_maybe_transform(
                {
                    "organization_alias": organization_alias,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "soft_budget": soft_budget,
                    "tpm_limit": tpm_limit,
                },
                organization_create_params.OrganizationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationCreateResponse,
        )

    async def update(
        self,
        *,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[List[str]] | NotGiven = NOT_GIVEN,
        organization_alias: Optional[str] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        updated_by: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationUpdateResponse:
        """
        Update an organization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/organization/update",
            body=await async_maybe_transform(
                {
                    "budget_id": budget_id,
                    "metadata": metadata,
                    "models": models,
                    "organization_alias": organization_alias,
                    "organization_id": organization_id,
                    "spend": spend,
                    "updated_by": updated_by,
                },
                organization_update_params.OrganizationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationUpdateResponse,
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
    ) -> OrganizationListResponse:
        """
        ```
        curl --location --request GET 'http://0.0.0.0:4000/organization/list'         --header 'Authorization: Bearer sk-1234'
        ```
        """
        return await self._get(
            "/organization/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationListResponse,
        )

    async def delete(
        self,
        *,
        organization_ids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationDeleteResponse:
        """
        Delete an organization

        # Parameters:

        - organization_ids: List[str] - The organization ids to delete.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._delete(
            "/organization/delete",
            body=await async_maybe_transform(
                {"organization_ids": organization_ids}, organization_delete_params.OrganizationDeleteParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationDeleteResponse,
        )

    async def add_member(
        self,
        *,
        member: organization_add_member_params.Member,
        organization_id: str,
        max_budget_in_organization: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationAddMemberResponse:
        """
        [BETA]

        Add new members (either via user_email or user_id) to an organization

        If user doesn't exist, new user row will also be added to User Table

        Only proxy_admin or org_admin of organization, allowed to access this endpoint.

        # Parameters:

        - organization_id: str (required)
        - member: Union[List[Member], Member] (required)
          - role: Literal[LLMUserRoles] (required)
          - user_id: Optional[str]
          - user_email: Optional[str]

        Note: Either user_id or user_email must be provided for each member.

        Example:

        ```
        curl -X POST 'http://0.0.0.0:4000/organization/member_add'     -H 'Authorization: Bearer sk-1234'     -H 'Content-Type: application/json'     -d '{
            "organization_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849",
            "member": {
                "role": "internal_user",
                "user_id": "dev247652@hanzo.ai"
            },
            "max_budget_in_organization": 100.0
        }'
        ```

        The following is executed in this function:

        1. Check if organization exists
        2. Creates a new Internal User if the user_id or user_email is not found in
           LLM_UserTable
        3. Add Internal User to the `LLM_OrganizationMembership` table

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/organization/member_add",
            body=await async_maybe_transform(
                {
                    "member": member,
                    "organization_id": organization_id,
                    "max_budget_in_organization": max_budget_in_organization,
                },
                organization_add_member_params.OrganizationAddMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationAddMemberResponse,
        )

    async def delete_member(
        self,
        *,
        organization_id: str,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a member from an organization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._delete(
            "/organization/member_delete",
            body=await async_maybe_transform(
                {
                    "organization_id": organization_id,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                organization_delete_member_params.OrganizationDeleteMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update_member(
        self,
        *,
        organization_id: str,
        max_budget_in_organization: Optional[float] | NotGiven = NOT_GIVEN,
        role: Optional[
            Literal[
                "proxy_admin",
                "proxy_admin_viewer",
                "org_admin",
                "internal_user",
                "internal_user_viewer",
                "team",
                "customer",
            ]
        ]
        | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> OrganizationUpdateMemberResponse:
        """
        Update a member's role in an organization

        Args:
          role: Admin Roles: PROXY_ADMIN: admin over the platform PROXY_ADMIN_VIEW_ONLY: can
              login, view all own keys, view all spend ORG_ADMIN: admin over a specific
              organization, can create teams, users only within their organization

              Internal User Roles: INTERNAL_USER: can login, view/create/delete their own
              keys, view their spend INTERNAL_USER_VIEW_ONLY: can login, view their own keys,
              view their own spend

              Team Roles: TEAM: used for JWT auth

              Customer Roles: CUSTOMER: External users -> these are customers

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/organization/member_update",
            body=await async_maybe_transform(
                {
                    "organization_id": organization_id,
                    "max_budget_in_organization": max_budget_in_organization,
                    "role": role,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                organization_update_member_params.OrganizationUpdateMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationUpdateMemberResponse,
        )


class OrganizationResourceWithRawResponse:
    def __init__(self, organization: OrganizationResource) -> None:
        self._organization = organization

        self.create = to_raw_response_wrapper(
            organization.create,
        )
        self.update = to_raw_response_wrapper(
            organization.update,
        )
        self.list = to_raw_response_wrapper(
            organization.list,
        )
        self.delete = to_raw_response_wrapper(
            organization.delete,
        )
        self.add_member = to_raw_response_wrapper(
            organization.add_member,
        )
        self.delete_member = to_raw_response_wrapper(
            organization.delete_member,
        )
        self.update_member = to_raw_response_wrapper(
            organization.update_member,
        )

    @cached_property
    def info(self) -> InfoResourceWithRawResponse:
        return InfoResourceWithRawResponse(self._organization.info)


class AsyncOrganizationResourceWithRawResponse:
    def __init__(self, organization: AsyncOrganizationResource) -> None:
        self._organization = organization

        self.create = async_to_raw_response_wrapper(
            organization.create,
        )
        self.update = async_to_raw_response_wrapper(
            organization.update,
        )
        self.list = async_to_raw_response_wrapper(
            organization.list,
        )
        self.delete = async_to_raw_response_wrapper(
            organization.delete,
        )
        self.add_member = async_to_raw_response_wrapper(
            organization.add_member,
        )
        self.delete_member = async_to_raw_response_wrapper(
            organization.delete_member,
        )
        self.update_member = async_to_raw_response_wrapper(
            organization.update_member,
        )

    @cached_property
    def info(self) -> AsyncInfoResourceWithRawResponse:
        return AsyncInfoResourceWithRawResponse(self._organization.info)


class OrganizationResourceWithStreamingResponse:
    def __init__(self, organization: OrganizationResource) -> None:
        self._organization = organization

        self.create = to_streamed_response_wrapper(
            organization.create,
        )
        self.update = to_streamed_response_wrapper(
            organization.update,
        )
        self.list = to_streamed_response_wrapper(
            organization.list,
        )
        self.delete = to_streamed_response_wrapper(
            organization.delete,
        )
        self.add_member = to_streamed_response_wrapper(
            organization.add_member,
        )
        self.delete_member = to_streamed_response_wrapper(
            organization.delete_member,
        )
        self.update_member = to_streamed_response_wrapper(
            organization.update_member,
        )

    @cached_property
    def info(self) -> InfoResourceWithStreamingResponse:
        return InfoResourceWithStreamingResponse(self._organization.info)


class AsyncOrganizationResourceWithStreamingResponse:
    def __init__(self, organization: AsyncOrganizationResource) -> None:
        self._organization = organization

        self.create = async_to_streamed_response_wrapper(
            organization.create,
        )
        self.update = async_to_streamed_response_wrapper(
            organization.update,
        )
        self.list = async_to_streamed_response_wrapper(
            organization.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            organization.delete,
        )
        self.add_member = async_to_streamed_response_wrapper(
            organization.add_member,
        )
        self.delete_member = async_to_streamed_response_wrapper(
            organization.delete_member,
        )
        self.update_member = async_to_streamed_response_wrapper(
            organization.update_member,
        )

    @cached_property
    def info(self) -> AsyncInfoResourceWithStreamingResponse:
        return AsyncInfoResourceWithStreamingResponse(self._organization.info)
