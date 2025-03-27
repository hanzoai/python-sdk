# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    user_list_params,
    user_create_params,
    user_delete_params,
    user_update_params,
    user_retrieve_info_params,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import (
    maybe_transform,
    strip_not_given,
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
from ..types.user_create_response import UserCreateResponse

__all__ = ["UserResource", "AsyncUserResource"]


class UserResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return UserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return UserResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        auto_create_key: bool | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        send_invite_email: Optional[bool] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        teams: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_alias: Optional[str] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]
        | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserCreateResponse:
        """Use this to create a new INTERNAL user with a budget.

        Internal Users can access
        LLM Admin UI to make keys, request access to models. This creates a new user and
        generates a new api key for the new user. The new api key is returned.

        Returns user id, budget + new key.

        Parameters:

        - user_id: Optional[str] - Specify a user id. If not set, a unique id will be
          generated.
        - user_alias: Optional[str] - A descriptive name for you to know who this user
          id refers to.
        - teams: Optional[list] - specify a list of team id's a user belongs to.
        - user_email: Optional[str] - Specify a user email.
        - send_invite_email: Optional[bool] - Specify if an invite email should be sent.
        - user_role: Optional[str] - Specify a user role - "proxy_admin",
          "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team",
          "customer". Info about each role here:
          `https://github.com/hanzoai/llm/llm/proxy/_types.py#L20`
        - max_budget: Optional[float] - Specify max budget for a given user.
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d"), months ("1mo").
        - models: Optional[list] - Model_name's a user is allowed to call. (if empty,
          key is allowed to call all models). Set to ['no-default-models'] to block all
          model access. Restricting user to only team-based model access.
        - tpm_limit: Optional[int] - Specify tpm limit for a given user (Tokens per
          minute)
        - rpm_limit: Optional[int] - Specify rpm limit for a given user (Requests per
          minute)
        - auto_create_key: bool - Default=True. Flag used for returning a key as part of
          the /user/new response
        - aliases: Optional[dict] - Model aliases for the user -
          [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases)
        - config: Optional[dict] - [DEPRECATED PARAM] User-specific config.
        - allowed_cache_controls: Optional[list] - List of allowed cache control values.
          Example - ["no-cache", "no-store"]. See all values -
          https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request-
        - blocked: Optional[bool] - [Not Implemented Yet] Whether the user is blocked.
        - guardrails: Optional[List[str]] - [Not Implemented Yet] List of active
          guardrails for the user
        - permissions: Optional[dict] - [Not Implemented Yet] User-specific permissions,
          eg. turning off pii masking.
        - metadata: Optional[dict] - Metadata for user, store information for user.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - max_parallel_requests: Optional[int] - Rate limit a user based on the number
          of parallel requests. Raises 429 error, if user's parallel requests > x.
        - soft_budget: Optional[float] - Get alerts when user crosses given budget,
          doesn't block requests.
        - model_max_budget: Optional[dict] - Model-specific max budget for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-budgets-to-keys)
        - model_rpm_limit: Optional[float] - Model-specific rpm limit for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys)
        - model_tpm_limit: Optional[float] - Model-specific tpm limit for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys)
        - spend: Optional[float] - Amount spent by user. Default is 0. Will be updated
          by proxy whenever user is used. You can set duration as seconds ("30s"),
          minutes ("30m"), hours ("30h"), days ("30d"), months ("1mo").
        - team_id: Optional[str] - [DEPRECATED PARAM] The team id of the user. Default
          is None.
        - duration: Optional[str] - Duration for the key auto-created on `/user/new`.
          Default is None.
        - key_alias: Optional[str] - Alias for the key auto-created on `/user/new`.
          Default is None.

        Returns:

        - key: (str) The generated api key for the user
        - expires: (datetime) Datetime object for when key expires.
        - user_id: (str) Unique user id - used for tracking spend across multiple keys
          for same user id.
        - max_budget: (float|None) Max budget for given user.

        Usage Example

        ```shell
         curl -X POST "http://localhost:4000/user/new"      -H "Content-Type: application/json"      -H "Authorization: Bearer sk-1234"      -d '{
             "username": "new_user",
             "email": "new_user@example.com"
         }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/user/new",
            body=maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "auto_create_key": auto_create_key,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "config": config,
                    "duration": duration,
                    "guardrails": guardrails,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "send_invite_email": send_invite_email,
                    "spend": spend,
                    "team_id": team_id,
                    "teams": teams,
                    "tpm_limit": tpm_limit,
                    "user_alias": user_alias,
                    "user_email": user_email,
                    "user_id": user_id,
                    "user_role": user_role,
                },
                user_create_params.UserCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserCreateResponse,
        )

    def update(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        password: Optional[str] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]
        | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Example curl

        ```
        curl --location 'http://0.0.0.0:4000/user/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "user_id": "test-llm-user-4",
            "user_role": "proxy_admin_viewer"
        }'
        ```

        Parameters: - user_id: Optional[str] - Specify a user id. If not set, a unique
        id will be generated. - user_email: Optional[str] - Specify a user email. -
        password: Optional[str] - Specify a user password. - user_alias: Optional[str] -
        A descriptive name for you to know who this user id refers to. - teams:
        Optional[list] - specify a list of team id's a user belongs to. -
        send_invite_email: Optional[bool] - Specify if an invite email should be sent. -
        user_role: Optional[str] - Specify a user role - "proxy_admin",
        "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team",
        "customer". Info about each role here:
        `https://github.com/hanzoai/llm/llm/proxy/_types.py#L20` - max_budget:
        Optional[float] - Specify max budget for a given user. - budget_duration:
        Optional[str] - Budget is reset at the end of specified duration. If not set,
        budget is never reset. You can set duration as seconds ("30s"), minutes ("30m"),
        hours ("30h"), days ("30d"), months ("1mo"). - models: Optional[list] -
        Model_name's a user is allowed to call. (if empty, key is allowed to call all
        models) - tpm_limit: Optional[int] - Specify tpm limit for a given user (Tokens
        per minute) - rpm_limit: Optional[int] - Specify rpm limit for a given user
        (Requests per minute) - auto_create_key: bool - Default=True. Flag used for
        returning a key as part of the /user/new response - aliases: Optional[dict] -
        Model aliases for the user -
        [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases) - config:
        Optional[dict] - [DEPRECATED PARAM] User-specific config. -
        allowed_cache_controls: Optional[list] - List of allowed cache control values.
        Example - ["no-cache", "no-store"]. See all values -
        https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request- -
        blocked: Optional[bool] - [Not Implemented Yet] Whether the user is blocked. -
        guardrails: Optional[List[str]] - [Not Implemented Yet] List of active
        guardrails for the user - permissions: Optional[dict] - [Not Implemented Yet]
        User-specific permissions, eg. turning off pii masking. - metadata:
        Optional[dict] - Metadata for user, store information for user. Example metadata
        = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai" } -
        max_parallel_requests: Optional[int] - Rate limit a user based on the number of
        parallel requests. Raises 429 error, if user's parallel requests > x. -
        soft_budget: Optional[float] - Get alerts when user crosses given budget,
        doesn't block requests. - model_max_budget: Optional[dict] - Model-specific max
        budget for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-budgets-to-keys) -
        model_rpm_limit: Optional[float] - Model-specific rpm limit for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys) -
        model_tpm_limit: Optional[float] - Model-specific tpm limit for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys) -
        spend: Optional[float] - Amount spent by user. Default is 0. Will be updated by
        proxy whenever user is used. You can set duration as seconds ("30s"), minutes
        ("30m"), hours ("30h"), days ("30d"), months ("1mo"). - team_id: Optional[str] -
        [DEPRECATED PARAM] The team id of the user. Default is None. - duration:
        Optional[str] - [NOT IMPLEMENTED]. - key_alias: Optional[str] - [NOT
        IMPLEMENTED].

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/user/update",
            body=maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "config": config,
                    "duration": duration,
                    "guardrails": guardrails,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "password": password,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "spend": spend,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_email": user_email,
                    "user_id": user_id,
                    "user_role": user_role,
                },
                user_update_params.UserUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        page: int | NotGiven = NOT_GIVEN,
        page_size: int | NotGiven = NOT_GIVEN,
        role: Optional[str] | NotGiven = NOT_GIVEN,
        user_ids: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get a paginated list of users, optionally filtered by role.

        Used by the UI to populate the user lists.

        Parameters: role: Optional[str] Filter users by role. Can be one of: -
        proxy_admin - proxy_admin_viewer - internal_user - internal_user_viewer
        user_ids: Optional[str] Get list of users by user_ids. Comma separated list of
        user_ids. page: int The page number to return page_size: int The number of items
        per page

        Currently - admin-only endpoint.

        Example curl:

        ```
        http://0.0.0.0:4000/user/list?user_ids=default_user_id,693c1a4a-1cc0-4c7c-afe8-b5d2c8d52e17
        ```

        Args:
          page: Page number

          page_size: Number of items per page

          role: Filter users by role

          user_ids: Get list of users by user_ids

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/user/get_users",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "role": role,
                        "user_ids": user_ids,
                    },
                    user_list_params.UserListParams,
                ),
            ),
            cast_to=object,
        )

    def delete(
        self,
        *,
        user_ids: List[str],
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        delete user and associated user keys

        ```
        curl --location 'http://0.0.0.0:4000/user/delete'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data-raw '{
            "user_ids": ["45e3e396-ee08-4a61-a88e-16b3ce7e0849"]
        }'
        ```

        Parameters:

        - user_ids: List[str] - The list of user id's to be deleted.

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
            "/user/delete",
            body=maybe_transform({"user_ids": user_ids}, user_delete_params.UserDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve_info(
        self,
        *,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [10/07/2024] Note: To get all users (+pagination), use `/user/list` endpoint.

        Use this to get user information. (user row + all user key info)

        Example request

        ```
        curl -X GET 'http://localhost:4000/user/info?user_id=dev7%40hanzo.ai'     --header 'Authorization: Bearer sk-1234'
        ```

        Args:
          user_id: User ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/user/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"user_id": user_id}, user_retrieve_info_params.UserRetrieveInfoParams),
            ),
            cast_to=object,
        )


class AsyncUserResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncUserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncUserResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        auto_create_key: bool | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        send_invite_email: Optional[bool] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        teams: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_alias: Optional[str] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]
        | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserCreateResponse:
        """Use this to create a new INTERNAL user with a budget.

        Internal Users can access
        LLM Admin UI to make keys, request access to models. This creates a new user and
        generates a new api key for the new user. The new api key is returned.

        Returns user id, budget + new key.

        Parameters:

        - user_id: Optional[str] - Specify a user id. If not set, a unique id will be
          generated.
        - user_alias: Optional[str] - A descriptive name for you to know who this user
          id refers to.
        - teams: Optional[list] - specify a list of team id's a user belongs to.
        - user_email: Optional[str] - Specify a user email.
        - send_invite_email: Optional[bool] - Specify if an invite email should be sent.
        - user_role: Optional[str] - Specify a user role - "proxy_admin",
          "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team",
          "customer". Info about each role here:
          `https://github.com/hanzoai/llm/llm/proxy/_types.py#L20`
        - max_budget: Optional[float] - Specify max budget for a given user.
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d"), months ("1mo").
        - models: Optional[list] - Model_name's a user is allowed to call. (if empty,
          key is allowed to call all models). Set to ['no-default-models'] to block all
          model access. Restricting user to only team-based model access.
        - tpm_limit: Optional[int] - Specify tpm limit for a given user (Tokens per
          minute)
        - rpm_limit: Optional[int] - Specify rpm limit for a given user (Requests per
          minute)
        - auto_create_key: bool - Default=True. Flag used for returning a key as part of
          the /user/new response
        - aliases: Optional[dict] - Model aliases for the user -
          [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases)
        - config: Optional[dict] - [DEPRECATED PARAM] User-specific config.
        - allowed_cache_controls: Optional[list] - List of allowed cache control values.
          Example - ["no-cache", "no-store"]. See all values -
          https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request-
        - blocked: Optional[bool] - [Not Implemented Yet] Whether the user is blocked.
        - guardrails: Optional[List[str]] - [Not Implemented Yet] List of active
          guardrails for the user
        - permissions: Optional[dict] - [Not Implemented Yet] User-specific permissions,
          eg. turning off pii masking.
        - metadata: Optional[dict] - Metadata for user, store information for user.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - max_parallel_requests: Optional[int] - Rate limit a user based on the number
          of parallel requests. Raises 429 error, if user's parallel requests > x.
        - soft_budget: Optional[float] - Get alerts when user crosses given budget,
          doesn't block requests.
        - model_max_budget: Optional[dict] - Model-specific max budget for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-budgets-to-keys)
        - model_rpm_limit: Optional[float] - Model-specific rpm limit for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys)
        - model_tpm_limit: Optional[float] - Model-specific tpm limit for user.
          [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys)
        - spend: Optional[float] - Amount spent by user. Default is 0. Will be updated
          by proxy whenever user is used. You can set duration as seconds ("30s"),
          minutes ("30m"), hours ("30h"), days ("30d"), months ("1mo").
        - team_id: Optional[str] - [DEPRECATED PARAM] The team id of the user. Default
          is None.
        - duration: Optional[str] - Duration for the key auto-created on `/user/new`.
          Default is None.
        - key_alias: Optional[str] - Alias for the key auto-created on `/user/new`.
          Default is None.

        Returns:

        - key: (str) The generated api key for the user
        - expires: (datetime) Datetime object for when key expires.
        - user_id: (str) Unique user id - used for tracking spend across multiple keys
          for same user id.
        - max_budget: (float|None) Max budget for given user.

        Usage Example

        ```shell
         curl -X POST "http://localhost:4000/user/new"      -H "Content-Type: application/json"      -H "Authorization: Bearer sk-1234"      -d '{
             "username": "new_user",
             "email": "new_user@example.com"
         }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/user/new",
            body=await async_maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "auto_create_key": auto_create_key,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "config": config,
                    "duration": duration,
                    "guardrails": guardrails,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "send_invite_email": send_invite_email,
                    "spend": spend,
                    "team_id": team_id,
                    "teams": teams,
                    "tpm_limit": tpm_limit,
                    "user_alias": user_alias,
                    "user_email": user_email,
                    "user_id": user_id,
                    "user_role": user_role,
                },
                user_create_params.UserCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserCreateResponse,
        )

    async def update(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        password: Optional[str] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_email: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]
        | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Example curl

        ```
        curl --location 'http://0.0.0.0:4000/user/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "user_id": "test-llm-user-4",
            "user_role": "proxy_admin_viewer"
        }'
        ```

        Parameters: - user_id: Optional[str] - Specify a user id. If not set, a unique
        id will be generated. - user_email: Optional[str] - Specify a user email. -
        password: Optional[str] - Specify a user password. - user_alias: Optional[str] -
        A descriptive name for you to know who this user id refers to. - teams:
        Optional[list] - specify a list of team id's a user belongs to. -
        send_invite_email: Optional[bool] - Specify if an invite email should be sent. -
        user_role: Optional[str] - Specify a user role - "proxy_admin",
        "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team",
        "customer". Info about each role here:
        `https://github.com/hanzoai/llm/llm/proxy/_types.py#L20` - max_budget:
        Optional[float] - Specify max budget for a given user. - budget_duration:
        Optional[str] - Budget is reset at the end of specified duration. If not set,
        budget is never reset. You can set duration as seconds ("30s"), minutes ("30m"),
        hours ("30h"), days ("30d"), months ("1mo"). - models: Optional[list] -
        Model_name's a user is allowed to call. (if empty, key is allowed to call all
        models) - tpm_limit: Optional[int] - Specify tpm limit for a given user (Tokens
        per minute) - rpm_limit: Optional[int] - Specify rpm limit for a given user
        (Requests per minute) - auto_create_key: bool - Default=True. Flag used for
        returning a key as part of the /user/new response - aliases: Optional[dict] -
        Model aliases for the user -
        [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases) - config:
        Optional[dict] - [DEPRECATED PARAM] User-specific config. -
        allowed_cache_controls: Optional[list] - List of allowed cache control values.
        Example - ["no-cache", "no-store"]. See all values -
        https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request- -
        blocked: Optional[bool] - [Not Implemented Yet] Whether the user is blocked. -
        guardrails: Optional[List[str]] - [Not Implemented Yet] List of active
        guardrails for the user - permissions: Optional[dict] - [Not Implemented Yet]
        User-specific permissions, eg. turning off pii masking. - metadata:
        Optional[dict] - Metadata for user, store information for user. Example metadata
        = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai" } -
        max_parallel_requests: Optional[int] - Rate limit a user based on the number of
        parallel requests. Raises 429 error, if user's parallel requests > x. -
        soft_budget: Optional[float] - Get alerts when user crosses given budget,
        doesn't block requests. - model_max_budget: Optional[dict] - Model-specific max
        budget for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-budgets-to-keys) -
        model_rpm_limit: Optional[float] - Model-specific rpm limit for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys) -
        model_tpm_limit: Optional[float] - Model-specific tpm limit for user.
        [Docs](https://docs.hanzo.ai/docs/proxy/users#add-model-specific-limits-to-keys) -
        spend: Optional[float] - Amount spent by user. Default is 0. Will be updated by
        proxy whenever user is used. You can set duration as seconds ("30s"), minutes
        ("30m"), hours ("30h"), days ("30d"), months ("1mo"). - team_id: Optional[str] -
        [DEPRECATED PARAM] The team id of the user. Default is None. - duration:
        Optional[str] - [NOT IMPLEMENTED]. - key_alias: Optional[str] - [NOT
        IMPLEMENTED].

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/user/update",
            body=await async_maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "config": config,
                    "duration": duration,
                    "guardrails": guardrails,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "password": password,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "spend": spend,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_email": user_email,
                    "user_id": user_id,
                    "user_role": user_role,
                },
                user_update_params.UserUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        page: int | NotGiven = NOT_GIVEN,
        page_size: int | NotGiven = NOT_GIVEN,
        role: Optional[str] | NotGiven = NOT_GIVEN,
        user_ids: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get a paginated list of users, optionally filtered by role.

        Used by the UI to populate the user lists.

        Parameters: role: Optional[str] Filter users by role. Can be one of: -
        proxy_admin - proxy_admin_viewer - internal_user - internal_user_viewer
        user_ids: Optional[str] Get list of users by user_ids. Comma separated list of
        user_ids. page: int The page number to return page_size: int The number of items
        per page

        Currently - admin-only endpoint.

        Example curl:

        ```
        http://0.0.0.0:4000/user/list?user_ids=default_user_id,693c1a4a-1cc0-4c7c-afe8-b5d2c8d52e17
        ```

        Args:
          page: Page number

          page_size: Number of items per page

          role: Filter users by role

          user_ids: Get list of users by user_ids

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/user/get_users",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "role": role,
                        "user_ids": user_ids,
                    },
                    user_list_params.UserListParams,
                ),
            ),
            cast_to=object,
        )

    async def delete(
        self,
        *,
        user_ids: List[str],
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        delete user and associated user keys

        ```
        curl --location 'http://0.0.0.0:4000/user/delete'
        --header 'Authorization: Bearer sk-1234'
        --header 'Content-Type: application/json'
        --data-raw '{
            "user_ids": ["45e3e396-ee08-4a61-a88e-16b3ce7e0849"]
        }'
        ```

        Parameters:

        - user_ids: List[str] - The list of user id's to be deleted.

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
            "/user/delete",
            body=await async_maybe_transform({"user_ids": user_ids}, user_delete_params.UserDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve_info(
        self,
        *,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        [10/07/2024] Note: To get all users (+pagination), use `/user/list` endpoint.

        Use this to get user information. (user row + all user key info)

        Example request

        ```
        curl -X GET 'http://localhost:4000/user/info?user_id=dev7%40hanzo.ai'     --header 'Authorization: Bearer sk-1234'
        ```

        Args:
          user_id: User ID in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/user/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"user_id": user_id}, user_retrieve_info_params.UserRetrieveInfoParams
                ),
            ),
            cast_to=object,
        )


class UserResourceWithRawResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.create = to_raw_response_wrapper(
            user.create,
        )
        self.update = to_raw_response_wrapper(
            user.update,
        )
        self.list = to_raw_response_wrapper(
            user.list,
        )
        self.delete = to_raw_response_wrapper(
            user.delete,
        )
        self.retrieve_info = to_raw_response_wrapper(
            user.retrieve_info,
        )


class AsyncUserResourceWithRawResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.create = async_to_raw_response_wrapper(
            user.create,
        )
        self.update = async_to_raw_response_wrapper(
            user.update,
        )
        self.list = async_to_raw_response_wrapper(
            user.list,
        )
        self.delete = async_to_raw_response_wrapper(
            user.delete,
        )
        self.retrieve_info = async_to_raw_response_wrapper(
            user.retrieve_info,
        )


class UserResourceWithStreamingResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.create = to_streamed_response_wrapper(
            user.create,
        )
        self.update = to_streamed_response_wrapper(
            user.update,
        )
        self.list = to_streamed_response_wrapper(
            user.list,
        )
        self.delete = to_streamed_response_wrapper(
            user.delete,
        )
        self.retrieve_info = to_streamed_response_wrapper(
            user.retrieve_info,
        )


class AsyncUserResourceWithStreamingResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.create = async_to_streamed_response_wrapper(
            user.create,
        )
        self.update = async_to_streamed_response_wrapper(
            user.update,
        )
        self.list = async_to_streamed_response_wrapper(
            user.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            user.delete,
        )
        self.retrieve_info = async_to_streamed_response_wrapper(
            user.retrieve_info,
        )
