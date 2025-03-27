# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Literal

import httpx

from .model import (
    ModelResource,
    AsyncModelResource,
    ModelResourceWithRawResponse,
    AsyncModelResourceWithRawResponse,
    ModelResourceWithStreamingResponse,
    AsyncModelResourceWithStreamingResponse,
)
from ...types import (
    team_list_params,
    team_block_params,
    team_create_params,
    team_delete_params,
    team_update_params,
    team_unblock_params,
    team_add_member_params,
    team_remove_member_params,
    team_retrieve_info_params,
    team_update_member_params,
    team_list_available_params,
)
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import (
    maybe_transform,
    strip_not_given,
    async_maybe_transform,
)
from .callback import (
    CallbackResource,
    AsyncCallbackResource,
    CallbackResourceWithRawResponse,
    AsyncCallbackResourceWithRawResponse,
    CallbackResourceWithStreamingResponse,
    AsyncCallbackResourceWithStreamingResponse,
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
from ...types.member_param import MemberParam
from ...types.team_create_response import TeamCreateResponse
from ...types.team_add_member_response import TeamAddMemberResponse
from ...types.team_update_member_response import TeamUpdateMemberResponse

__all__ = ["TeamResource", "AsyncTeamResource"]


class TeamResource(SyncAPIResource):
    @cached_property
    def model(self) -> ModelResource:
        return ModelResource(self._client)

    @cached_property
    def callback(self) -> CallbackResource:
        return CallbackResource(self._client)

    @cached_property
    def with_raw_response(self) -> TeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return TeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return TeamResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        admins: Iterable[object] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        members: Iterable[object] | NotGiven = NOT_GIVEN,
        members_with_roles: Iterable[MemberParam] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_aliases: Optional[object] | NotGiven = NOT_GIVEN,
        models: Iterable[object] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        tags: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        team_alias: Optional[str] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamCreateResponse:
        """Allow users to create a new team.

        Apply user permissions to their team.

        👉
        [Detailed Doc on setting team budgets](https://docs.hanzo.ai/docs/proxy/team_budgets)

        Parameters:

        - team_alias: Optional[str] - User defined team alias
        - team_id: Optional[str] - The team id of the user. If none passed, we'll
          generate it.
        - members_with_roles: List[{"role": "admin" or "user", "user_id":
          "<user-id>"}] - A list of users and their roles in the team. Get user_id when
          making a new user via `/user/new`.
        - metadata: Optional[dict] - Metadata for team, store information for team.
          Example metadata = {"extra_info": "some info"}
        - tpm_limit: Optional[int] - The TPM (Tokens Per Minute) limit for this team -
          all keys with this team_id will have at max this TPM limit
        - rpm_limit: Optional[int] - The RPM (Requests Per Minute) limit for this team -
          all keys associated with this team_id will have at max this RPM limit
        - max_budget: Optional[float] - The maximum budget allocated to the team - all
          keys for this team_id will have at max this max_budget
        - budget_duration: Optional[str] - The duration of the budget for the team. Doc
          [here](https://docs.hanzo.ai/docs/proxy/team_budgets)
        - models: Optional[list] - A list of models associated with the team - all keys
          for this team_id will have at most, these models. If empty, assumes all models
          are allowed.
        - blocked: bool - Flag indicating if the team is blocked or not - will stop all
          calls from keys with this team_id.
        - members: Optional[List] - Control team members via `/team/member/add` and
          `/team/member/delete`.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: Optional[str] - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)
        - guardrails: Optional[List[str]] - Guardrails for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/guardrails) Returns:
        - team_id: (str) Unique team id - used for tracking spend across multiple keys
          for same team id.

        \\__deprecated_params:

        - admins: list - A list of user_id's for the admin role
        - users: list - A list of user_id's for the user role

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/new'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
          "team_alias": "my-new-team_2",
          "members_with_roles": [{"role": "admin", "user_id": "user-1234"},
            {"role": "user", "user_id": "user-2434"}]
        }'

        ```

        ```
        curl --location 'http://0.0.0.0:4000/team/new'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
                   "team_alias": "QA Prod Bot",
                   "max_budget": 0.000000001,
                   "budget_duration": "1d"
               }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return self._post(
            "/team/new",
            body=maybe_transform(
                {
                    "admins": admins,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "guardrails": guardrails,
                    "max_budget": max_budget,
                    "members": members,
                    "members_with_roles": members_with_roles,
                    "metadata": metadata,
                    "model_aliases": model_aliases,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "tags": tags,
                    "team_alias": team_alias,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                },
                team_create_params.TeamCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamCreateResponse,
        )

    def update(
        self,
        *,
        team_id: str,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_aliases: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        tags: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        team_alias: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Use `/team/member_add` AND `/team/member/delete` to add/remove new team members

        You can now update team budget / rate limits via /team/update

        Parameters:

        - team_id: str - The team id of the user. Required param.
        - team_alias: Optional[str] - User defined team alias
        - metadata: Optional[dict] - Metadata for team, store information for team.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - tpm_limit: Optional[int] - The TPM (Tokens Per Minute) limit for this team -
          all keys with this team_id will have at max this TPM limit
        - rpm_limit: Optional[int] - The RPM (Requests Per Minute) limit for this team -
          all keys associated with this team_id will have at max this RPM limit
        - max_budget: Optional[float] - The maximum budget allocated to the team - all
          keys for this team_id will have at max this max_budget
        - budget_duration: Optional[str] - The duration of the budget for the team. Doc
          [here](https://docs.hanzo.ai/docs/proxy/team_budgets)
        - models: Optional[list] - A list of models associated with the team - all keys
          for this team_id will have at most, these models. If empty, assumes all models
          are allowed.
        - blocked: bool - Flag indicating if the team is blocked or not - will stop all
          calls from keys with this team_id.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: Optional[str] - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)
        - guardrails: Optional[List[str]] - Guardrails for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/guardrails) Example - update team TPM
          Limit

        ```
        curl --location 'http://0.0.0.0:4000/team/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_id": "8d916b1c-510d-4894-a334-1c16a93344f5",
            "tpm_limit": 100
        }'
        ```

        Example - Update Team `max_budget` budget

        ```
        curl --location 'http://0.0.0.0:4000/team/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_id": "8d916b1c-510d-4894-a334-1c16a93344f5",
            "max_budget": 10
        }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return self._post(
            "/team/update",
            body=maybe_transform(
                {
                    "team_id": team_id,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "guardrails": guardrails,
                    "max_budget": max_budget,
                    "metadata": metadata,
                    "model_aliases": model_aliases,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "tags": tags,
                    "team_alias": team_alias,
                    "tpm_limit": tpm_limit,
                },
                team_update_params.TeamUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        ```
        curl --location --request GET 'http://0.0.0.0:4000/team/list'         --header 'Authorization: Bearer sk-1234'
        ```

        Parameters:

        - user_id: str - Optional. If passed will only return teams that the user_id is
          a member of.
        - organization_id: str - Optional. If passed will only return teams that belong
          to the organization_id. Pass 'default_organization' to get all teams without
          organization_id.

        Args:
          user_id: Only return teams which this 'user_id' belongs to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/team/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "organization_id": organization_id,
                        "user_id": user_id,
                    },
                    team_list_params.TeamListParams,
                ),
            ),
            cast_to=object,
        )

    def delete(
        self,
        *,
        team_ids: List[str],
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        delete team and associated team keys

        Parameters:

        - team_ids: List[str] - Required. List of team IDs to delete. Example:
          ["team-1234", "team-5678"]

        ```
        curl --location 'http://0.0.0.0:4000/team/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_ids": ["8d916b1c-510d-4894-a334-1c16a93344f5"]
        }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return self._post(
            "/team/delete",
            body=maybe_transform({"team_ids": team_ids}, team_delete_params.TeamDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def add_member(
        self,
        *,
        member: team_add_member_params.Member,
        team_id: str,
        max_budget_in_team: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamAddMemberResponse:
        """
        [BETA]

        Add new members (either via user_email or user_id) to a team

        If user doesn't exist, new user row will also be added to User Table

        Only proxy_admin or admin of team, allowed to access this endpoint.

        ```

        curl -X POST 'http://0.0.0.0:4000/team/member_add'     -H 'Authorization: Bearer sk-1234'     -H 'Content-Type: application/json'     -d '{"team_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849", "member": {"role": "user", "user_id": "dev247652@hanzo.ai"}}'

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/member_add",
            body=maybe_transform(
                {
                    "member": member,
                    "team_id": team_id,
                    "max_budget_in_team": max_budget_in_team,
                },
                team_add_member_params.TeamAddMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamAddMemberResponse,
        )

    def block(
        self,
        *,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Blocks all calls from keys with this team id.

        Parameters:

        - team_id: str - Required. The unique identifier of the team to block.

        Example:

        ```
        curl --location 'http://0.0.0.0:4000/team/block'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234"
        }'
        ```

        Returns:

        - The updated team record with blocked=True

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/block",
            body=maybe_transform({"team_id": team_id}, team_block_params.TeamBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def disable_logging(
        self,
        team_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Disable all logging callbacks for a team

        Parameters:

        - team_id (str, required): The unique identifier for the team

        Example curl:

        ```
        curl -X POST 'http://localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/disable_logging'         -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        return self._post(
            f"/team/{team_id}/disable_logging",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_available(
        self,
        *,
        response_model: object | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        List Available Teams

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/team/available",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"response_model": response_model}, team_list_available_params.TeamListAvailableParams
                ),
            ),
            cast_to=object,
        )

    def remove_member(
        self,
        *,
        team_id: str,
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
        [BETA]

        delete members (either via user_email or user_id) from a team

        If user doesn't exist, an exception will be raised

        ```
        curl -X POST 'http://0.0.0.0:8000/team/member_delete'
        -H 'Authorization: Bearer sk-1234'
        -H 'Content-Type: application/json'
        -d '{
            "team_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849",
            "user_id": "dev247652@hanzo.ai"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/member_delete",
            body=maybe_transform(
                {
                    "team_id": team_id,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                team_remove_member_params.TeamRemoveMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve_info(
        self,
        *,
        team_id: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """get info on team + related keys

        Parameters:

        - team_id: str - Required.

        The unique identifier of the team to get info on.

        ```
        curl --location 'http://localhost:4000/team/info?team_id=your_team_id_here'     --header 'Authorization: Bearer your_api_key_here'
        ```

        Args:
          team_id: Team ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/team/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"team_id": team_id}, team_retrieve_info_params.TeamRetrieveInfoParams),
            ),
            cast_to=object,
        )

    def unblock(
        self,
        *,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Blocks all calls from keys with this team id.

        Parameters:

        - team_id: str - Required. The unique identifier of the team to unblock.

        Example:

        ```
        curl --location 'http://0.0.0.0:4000/team/unblock'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/unblock",
            body=maybe_transform({"team_id": team_id}, team_unblock_params.TeamUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update_member(
        self,
        *,
        team_id: str,
        max_budget_in_team: Optional[float] | NotGiven = NOT_GIVEN,
        role: Optional[Literal["admin", "user"]] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamUpdateMemberResponse:
        """
        [BETA]

        Update team member budgets and team member role

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/member_update",
            body=maybe_transform(
                {
                    "team_id": team_id,
                    "max_budget_in_team": max_budget_in_team,
                    "role": role,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                team_update_member_params.TeamUpdateMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamUpdateMemberResponse,
        )


class AsyncTeamResource(AsyncAPIResource):
    @cached_property
    def model(self) -> AsyncModelResource:
        return AsyncModelResource(self._client)

    @cached_property
    def callback(self) -> AsyncCallbackResource:
        return AsyncCallbackResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncTeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncTeamResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        admins: Iterable[object] | NotGiven = NOT_GIVEN,
        blocked: bool | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        members: Iterable[object] | NotGiven = NOT_GIVEN,
        members_with_roles: Iterable[MemberParam] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_aliases: Optional[object] | NotGiven = NOT_GIVEN,
        models: Iterable[object] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        tags: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        team_alias: Optional[str] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamCreateResponse:
        """Allow users to create a new team.

        Apply user permissions to their team.

        👉
        [Detailed Doc on setting team budgets](https://docs.hanzo.ai/docs/proxy/team_budgets)

        Parameters:

        - team_alias: Optional[str] - User defined team alias
        - team_id: Optional[str] - The team id of the user. If none passed, we'll
          generate it.
        - members_with_roles: List[{"role": "admin" or "user", "user_id":
          "<user-id>"}] - A list of users and their roles in the team. Get user_id when
          making a new user via `/user/new`.
        - metadata: Optional[dict] - Metadata for team, store information for team.
          Example metadata = {"extra_info": "some info"}
        - tpm_limit: Optional[int] - The TPM (Tokens Per Minute) limit for this team -
          all keys with this team_id will have at max this TPM limit
        - rpm_limit: Optional[int] - The RPM (Requests Per Minute) limit for this team -
          all keys associated with this team_id will have at max this RPM limit
        - max_budget: Optional[float] - The maximum budget allocated to the team - all
          keys for this team_id will have at max this max_budget
        - budget_duration: Optional[str] - The duration of the budget for the team. Doc
          [here](https://docs.hanzo.ai/docs/proxy/team_budgets)
        - models: Optional[list] - A list of models associated with the team - all keys
          for this team_id will have at most, these models. If empty, assumes all models
          are allowed.
        - blocked: bool - Flag indicating if the team is blocked or not - will stop all
          calls from keys with this team_id.
        - members: Optional[List] - Control team members via `/team/member/add` and
          `/team/member/delete`.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: Optional[str] - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)
        - guardrails: Optional[List[str]] - Guardrails for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/guardrails) Returns:
        - team_id: (str) Unique team id - used for tracking spend across multiple keys
          for same team id.

        \\__deprecated_params:

        - admins: list - A list of user_id's for the admin role
        - users: list - A list of user_id's for the user role

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/new'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
          "team_alias": "my-new-team_2",
          "members_with_roles": [{"role": "admin", "user_id": "user-1234"},
            {"role": "user", "user_id": "user-2434"}]
        }'

        ```

        ```
        curl --location 'http://0.0.0.0:4000/team/new'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
                   "team_alias": "QA Prod Bot",
                   "max_budget": 0.000000001,
                   "budget_duration": "1d"
               }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return await self._post(
            "/team/new",
            body=await async_maybe_transform(
                {
                    "admins": admins,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "guardrails": guardrails,
                    "max_budget": max_budget,
                    "members": members,
                    "members_with_roles": members_with_roles,
                    "metadata": metadata,
                    "model_aliases": model_aliases,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "tags": tags,
                    "team_alias": team_alias,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                },
                team_create_params.TeamCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamCreateResponse,
        )

    async def update(
        self,
        *,
        team_id: str,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_aliases: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        tags: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        team_alias: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Use `/team/member_add` AND `/team/member/delete` to add/remove new team members

        You can now update team budget / rate limits via /team/update

        Parameters:

        - team_id: str - The team id of the user. Required param.
        - team_alias: Optional[str] - User defined team alias
        - metadata: Optional[dict] - Metadata for team, store information for team.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - tpm_limit: Optional[int] - The TPM (Tokens Per Minute) limit for this team -
          all keys with this team_id will have at max this TPM limit
        - rpm_limit: Optional[int] - The RPM (Requests Per Minute) limit for this team -
          all keys associated with this team_id will have at max this RPM limit
        - max_budget: Optional[float] - The maximum budget allocated to the team - all
          keys for this team_id will have at max this max_budget
        - budget_duration: Optional[str] - The duration of the budget for the team. Doc
          [here](https://docs.hanzo.ai/docs/proxy/team_budgets)
        - models: Optional[list] - A list of models associated with the team - all keys
          for this team_id will have at most, these models. If empty, assumes all models
          are allowed.
        - blocked: bool - Flag indicating if the team is blocked or not - will stop all
          calls from keys with this team_id.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - organization_id: Optional[str] - The organization id of the team. Default is
          None. Create via `/organization/new`.
        - model_aliases: Optional[dict] - Model aliases for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/team_based_routing#create-team-with-model-alias)
        - guardrails: Optional[List[str]] - Guardrails for the team.
          [Docs](https://docs.hanzo.ai/docs/proxy/guardrails) Example - update team TPM
          Limit

        ```
        curl --location 'http://0.0.0.0:4000/team/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_id": "8d916b1c-510d-4894-a334-1c16a93344f5",
            "tpm_limit": 100
        }'
        ```

        Example - Update Team `max_budget` budget

        ```
        curl --location 'http://0.0.0.0:4000/team/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_id": "8d916b1c-510d-4894-a334-1c16a93344f5",
            "max_budget": 10
        }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return await self._post(
            "/team/update",
            body=await async_maybe_transform(
                {
                    "team_id": team_id,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "guardrails": guardrails,
                    "max_budget": max_budget,
                    "metadata": metadata,
                    "model_aliases": model_aliases,
                    "models": models,
                    "organization_id": organization_id,
                    "rpm_limit": rpm_limit,
                    "tags": tags,
                    "team_alias": team_alias,
                    "tpm_limit": tpm_limit,
                },
                team_update_params.TeamUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        ```
        curl --location --request GET 'http://0.0.0.0:4000/team/list'         --header 'Authorization: Bearer sk-1234'
        ```

        Parameters:

        - user_id: str - Optional. If passed will only return teams that the user_id is
          a member of.
        - organization_id: str - Optional. If passed will only return teams that belong
          to the organization_id. Pass 'default_organization' to get all teams without
          organization_id.

        Args:
          user_id: Only return teams which this 'user_id' belongs to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/team/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "organization_id": organization_id,
                        "user_id": user_id,
                    },
                    team_list_params.TeamListParams,
                ),
            ),
            cast_to=object,
        )

    async def delete(
        self,
        *,
        team_ids: List[str],
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        delete team and associated team keys

        Parameters:

        - team_ids: List[str] - Required. List of team IDs to delete. Example:
          ["team-1234", "team-5678"]

        ```
        curl --location 'http://0.0.0.0:4000/team/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "team_ids": ["8d916b1c-510d-4894-a334-1c16a93344f5"]
        }'
        ```

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return await self._post(
            "/team/delete",
            body=await async_maybe_transform({"team_ids": team_ids}, team_delete_params.TeamDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def add_member(
        self,
        *,
        member: team_add_member_params.Member,
        team_id: str,
        max_budget_in_team: Optional[float] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamAddMemberResponse:
        """
        [BETA]

        Add new members (either via user_email or user_id) to a team

        If user doesn't exist, new user row will also be added to User Table

        Only proxy_admin or admin of team, allowed to access this endpoint.

        ```

        curl -X POST 'http://0.0.0.0:4000/team/member_add'     -H 'Authorization: Bearer sk-1234'     -H 'Content-Type: application/json'     -d '{"team_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849", "member": {"role": "user", "user_id": "dev247652@hanzo.ai"}}'

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/member_add",
            body=await async_maybe_transform(
                {
                    "member": member,
                    "team_id": team_id,
                    "max_budget_in_team": max_budget_in_team,
                },
                team_add_member_params.TeamAddMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamAddMemberResponse,
        )

    async def block(
        self,
        *,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Blocks all calls from keys with this team id.

        Parameters:

        - team_id: str - Required. The unique identifier of the team to block.

        Example:

        ```
        curl --location 'http://0.0.0.0:4000/team/block'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234"
        }'
        ```

        Returns:

        - The updated team record with blocked=True

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/block",
            body=await async_maybe_transform({"team_id": team_id}, team_block_params.TeamBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def disable_logging(
        self,
        team_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Disable all logging callbacks for a team

        Parameters:

        - team_id (str, required): The unique identifier for the team

        Example curl:

        ```
        curl -X POST 'http://localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/disable_logging'         -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        return await self._post(
            f"/team/{team_id}/disable_logging",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_available(
        self,
        *,
        response_model: object | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        List Available Teams

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/team/available",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"response_model": response_model}, team_list_available_params.TeamListAvailableParams
                ),
            ),
            cast_to=object,
        )

    async def remove_member(
        self,
        *,
        team_id: str,
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
        [BETA]

        delete members (either via user_email or user_id) from a team

        If user doesn't exist, an exception will be raised

        ```
        curl -X POST 'http://0.0.0.0:8000/team/member_delete'
        -H 'Authorization: Bearer sk-1234'
        -H 'Content-Type: application/json'
        -d '{
            "team_id": "45e3e396-ee08-4a61-a88e-16b3ce7e0849",
            "user_id": "dev247652@hanzo.ai"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/member_delete",
            body=await async_maybe_transform(
                {
                    "team_id": team_id,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                team_remove_member_params.TeamRemoveMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve_info(
        self,
        *,
        team_id: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """get info on team + related keys

        Parameters:

        - team_id: str - Required.

        The unique identifier of the team to get info on.

        ```
        curl --location 'http://localhost:4000/team/info?team_id=your_team_id_here'     --header 'Authorization: Bearer your_api_key_here'
        ```

        Args:
          team_id: Team ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/team/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"team_id": team_id}, team_retrieve_info_params.TeamRetrieveInfoParams
                ),
            ),
            cast_to=object,
        )

    async def unblock(
        self,
        *,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Blocks all calls from keys with this team id.

        Parameters:

        - team_id: str - Required. The unique identifier of the team to unblock.

        Example:

        ```
        curl --location 'http://0.0.0.0:4000/team/unblock'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/unblock",
            body=await async_maybe_transform({"team_id": team_id}, team_unblock_params.TeamUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update_member(
        self,
        *,
        team_id: str,
        max_budget_in_team: Optional[float] | NotGiven = NOT_GIVEN,
        role: Optional[Literal["admin", "user"]] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TeamUpdateMemberResponse:
        """
        [BETA]

        Update team member budgets and team member role

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/member_update",
            body=await async_maybe_transform(
                {
                    "team_id": team_id,
                    "max_budget_in_team": max_budget_in_team,
                    "role": role,
                    "user_email": user_email,
                    "user_id": user_id,
                },
                team_update_member_params.TeamUpdateMemberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamUpdateMemberResponse,
        )


class TeamResourceWithRawResponse:
    def __init__(self, team: TeamResource) -> None:
        self._team = team

        self.create = to_raw_response_wrapper(
            team.create,
        )
        self.update = to_raw_response_wrapper(
            team.update,
        )
        self.list = to_raw_response_wrapper(
            team.list,
        )
        self.delete = to_raw_response_wrapper(
            team.delete,
        )
        self.add_member = to_raw_response_wrapper(
            team.add_member,
        )
        self.block = to_raw_response_wrapper(
            team.block,
        )
        self.disable_logging = to_raw_response_wrapper(
            team.disable_logging,
        )
        self.list_available = to_raw_response_wrapper(
            team.list_available,
        )
        self.remove_member = to_raw_response_wrapper(
            team.remove_member,
        )
        self.retrieve_info = to_raw_response_wrapper(
            team.retrieve_info,
        )
        self.unblock = to_raw_response_wrapper(
            team.unblock,
        )
        self.update_member = to_raw_response_wrapper(
            team.update_member,
        )

    @cached_property
    def model(self) -> ModelResourceWithRawResponse:
        return ModelResourceWithRawResponse(self._team.model)

    @cached_property
    def callback(self) -> CallbackResourceWithRawResponse:
        return CallbackResourceWithRawResponse(self._team.callback)


class AsyncTeamResourceWithRawResponse:
    def __init__(self, team: AsyncTeamResource) -> None:
        self._team = team

        self.create = async_to_raw_response_wrapper(
            team.create,
        )
        self.update = async_to_raw_response_wrapper(
            team.update,
        )
        self.list = async_to_raw_response_wrapper(
            team.list,
        )
        self.delete = async_to_raw_response_wrapper(
            team.delete,
        )
        self.add_member = async_to_raw_response_wrapper(
            team.add_member,
        )
        self.block = async_to_raw_response_wrapper(
            team.block,
        )
        self.disable_logging = async_to_raw_response_wrapper(
            team.disable_logging,
        )
        self.list_available = async_to_raw_response_wrapper(
            team.list_available,
        )
        self.remove_member = async_to_raw_response_wrapper(
            team.remove_member,
        )
        self.retrieve_info = async_to_raw_response_wrapper(
            team.retrieve_info,
        )
        self.unblock = async_to_raw_response_wrapper(
            team.unblock,
        )
        self.update_member = async_to_raw_response_wrapper(
            team.update_member,
        )

    @cached_property
    def model(self) -> AsyncModelResourceWithRawResponse:
        return AsyncModelResourceWithRawResponse(self._team.model)

    @cached_property
    def callback(self) -> AsyncCallbackResourceWithRawResponse:
        return AsyncCallbackResourceWithRawResponse(self._team.callback)


class TeamResourceWithStreamingResponse:
    def __init__(self, team: TeamResource) -> None:
        self._team = team

        self.create = to_streamed_response_wrapper(
            team.create,
        )
        self.update = to_streamed_response_wrapper(
            team.update,
        )
        self.list = to_streamed_response_wrapper(
            team.list,
        )
        self.delete = to_streamed_response_wrapper(
            team.delete,
        )
        self.add_member = to_streamed_response_wrapper(
            team.add_member,
        )
        self.block = to_streamed_response_wrapper(
            team.block,
        )
        self.disable_logging = to_streamed_response_wrapper(
            team.disable_logging,
        )
        self.list_available = to_streamed_response_wrapper(
            team.list_available,
        )
        self.remove_member = to_streamed_response_wrapper(
            team.remove_member,
        )
        self.retrieve_info = to_streamed_response_wrapper(
            team.retrieve_info,
        )
        self.unblock = to_streamed_response_wrapper(
            team.unblock,
        )
        self.update_member = to_streamed_response_wrapper(
            team.update_member,
        )

    @cached_property
    def model(self) -> ModelResourceWithStreamingResponse:
        return ModelResourceWithStreamingResponse(self._team.model)

    @cached_property
    def callback(self) -> CallbackResourceWithStreamingResponse:
        return CallbackResourceWithStreamingResponse(self._team.callback)


class AsyncTeamResourceWithStreamingResponse:
    def __init__(self, team: AsyncTeamResource) -> None:
        self._team = team

        self.create = async_to_streamed_response_wrapper(
            team.create,
        )
        self.update = async_to_streamed_response_wrapper(
            team.update,
        )
        self.list = async_to_streamed_response_wrapper(
            team.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            team.delete,
        )
        self.add_member = async_to_streamed_response_wrapper(
            team.add_member,
        )
        self.block = async_to_streamed_response_wrapper(
            team.block,
        )
        self.disable_logging = async_to_streamed_response_wrapper(
            team.disable_logging,
        )
        self.list_available = async_to_streamed_response_wrapper(
            team.list_available,
        )
        self.remove_member = async_to_streamed_response_wrapper(
            team.remove_member,
        )
        self.retrieve_info = async_to_streamed_response_wrapper(
            team.retrieve_info,
        )
        self.unblock = async_to_streamed_response_wrapper(
            team.unblock,
        )
        self.update_member = async_to_streamed_response_wrapper(
            team.update_member,
        )

    @cached_property
    def model(self) -> AsyncModelResourceWithStreamingResponse:
        return AsyncModelResourceWithStreamingResponse(self._team.model)

    @cached_property
    def callback(self) -> AsyncCallbackResourceWithStreamingResponse:
        return AsyncCallbackResourceWithStreamingResponse(self._team.callback)
