# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from datetime import datetime

import httpx

from ...types import (
    key_list_params,
    key_block_params,
    key_delete_params,
    key_update_params,
    key_unblock_params,
    key_generate_params,
    key_retrieve_info_params,
    key_regenerate_by_key_params,
)
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import (
    maybe_transform,
    strip_not_given,
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
from ...types.key_list_response import KeyListResponse
from ...types.key_block_response import KeyBlockResponse
from ...types.generate_key_response import GenerateKeyResponse
from ...types.key_check_health_response import KeyCheckHealthResponse

__all__ = ["KeyResource", "AsyncKeyResource"]


class KeyResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> KeyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return KeyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KeyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return KeyResourceWithStreamingResponse(self)

    def update(
        self,
        *,
        key: str,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
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
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        temp_budget_expiry: Union[str, datetime, None] | NotGiven = NOT_GIVEN,
        temp_budget_increase: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing API key's parameters.

        Parameters:

        - key: str - The key to update
        - key_alias: Optional[str] - User-friendly key alias
        - user_id: Optional[str] - User ID associated with key
        - team_id: Optional[str] - Team ID associated with key
        - budget_id: Optional[str] - The budget id associated with the key. Created by
          calling `/budget/new`.
        - models: Optional[list] - Model_name's a user is allowed to call
        - tags: Optional[List[str]] - Tags for organizing keys (Enterprise only)
        - enforced_params: Optional[List[str]] - List of enforced params for the key
          (Enterprise only).
          [Docs](https://docs.hanzo.ai/docs/proxy/enterprise#enforce-required-params-for-llm-requests)
        - spend: Optional[float] - Amount spent by key
        - max_budget: Optional[float] - Max budget for key
        - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
          {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}
        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - soft_budget: Optional[float] - [TODO] Soft budget limit (warning vs. hard
          stop). Will trigger a slack alert when this soft budget is reached.
        - max_parallel_requests: Optional[int] - Rate limit for parallel requests
        - metadata: Optional[dict] - Metadata for key. Example {"team": "core-infra",
          "app": "app2"}
        - tpm_limit: Optional[int] - Tokens per minute limit
        - rpm_limit: Optional[int] - Requests per minute limit
        - model_rpm_limit: Optional[dict] - Model-specific RPM limits {"gpt-4": 100,
          "claude-v1": 200}
        - model_tpm_limit: Optional[dict] - Model-specific TPM limits {"gpt-4": 100000,
          "claude-v1": 200000}
        - allowed_cache_controls: Optional[list] - List of allowed cache control values
        - duration: Optional[str] - Key validity duration ("30d", "1h", etc.)
        - permissions: Optional[dict] - Key-specific permissions
        - send_invite_email: Optional[bool] - Send invite email to user_id
        - guardrails: Optional[List[str]] - List of active guardrails for the key
        - blocked: Optional[bool] - Whether the key is blocked
        - aliases: Optional[dict] - Model aliases for the key -
          [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases)
        - config: Optional[dict] - [DEPRECATED PARAM] Key-specific config.
        - temp_budget_increase: Optional[float] - Temporary budget increase for the key
          (Enterprise only).
        - temp_budget_expiry: Optional[str] - Expiry time for the temporary budget
          increase (Enterprise only).

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-1234",
            "key_alias": "my-key",
            "user_id": "user-1234",
            "team_id": "team-1234",
            "max_budget": 100,
            "metadata": {"any_key": "any-val"},
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
            "/key/update",
            body=maybe_transform(
                {
                    "key": key,
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
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
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "temp_budget_expiry": temp_budget_expiry,
                    "temp_budget_increase": temp_budget_increase,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_update_params.KeyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        include_team_keys: bool | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        page: int | NotGiven = NOT_GIVEN,
        return_full_object: bool | NotGiven = NOT_GIVEN,
        size: int | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> KeyListResponse:
        """
        List all keys for a given user / team / organization.

        Returns: { "keys": List[str] or List[UserAPIKeyAuth], "total_count": int,
        "current_page": int, "total_pages": int, }

        Args:
          include_team_keys: Include all keys for teams that user is an admin of.

          key_alias: Filter keys by key alias

          organization_id: Filter keys by organization ID

          page: Page number

          return_full_object: Return full key object

          size: Page size

          team_id: Filter keys by team ID

          user_id: Filter keys by user ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/key/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "include_team_keys": include_team_keys,
                        "key_alias": key_alias,
                        "organization_id": organization_id,
                        "page": page,
                        "return_full_object": return_full_object,
                        "size": size,
                        "team_id": team_id,
                        "user_id": user_id,
                    },
                    key_list_params.KeyListParams,
                ),
            ),
            cast_to=KeyListResponse,
        )

    def delete(
        self,
        *,
        key_aliases: Optional[List[str]] | NotGiven = NOT_GIVEN,
        keys: Optional[List[str]] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a key from the key management system.

        Parameters::

        - keys (List[str]): A list of keys or hashed keys to delete. Example {"keys":
          ["sk-QWrxEynunsNpV1zT48HIrw",
          "837e17519f44683334df5291321d97b8bf1098cd490e49e215f6fea935aa28be"]}
        - key_aliases (List[str]): A list of key aliases to delete. Can be passed
          instead of `keys`.Example {"key_aliases": ["alias1", "alias2"]}

        Returns:

        - deleted_keys (List[str]): A list of deleted keys. Example {"deleted_keys":
          ["sk-QWrxEynunsNpV1zT48HIrw",
          "837e17519f44683334df5291321d97b8bf1098cd490e49e215f6fea935aa28be"]}

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "keys": ["sk-QWrxEynunsNpV1zT48HIrw"]
        }'
        ```

        Raises: HTTPException: If an error occurs during key deletion.

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
            "/key/delete",
            body=maybe_transform(
                {
                    "key_aliases": key_aliases,
                    "keys": keys,
                },
                key_delete_params.KeyDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def block(
        self,
        *,
        key: str,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Optional[KeyBlockResponse]:
        """
        Block an Virtual key from making any requests.

        Parameters:

        - key: str - The key to block. Can be either the unhashed key (sk-...) or the
          hashed key value

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/block'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-Fn8Ej39NxjAXrvpUGKghGw"
        }'
        ```

        Note: This is an admin-only endpoint. Only proxy admins can block keys.

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
            "/key/block",
            body=maybe_transform({"key": key}, key_block_params.KeyBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyBlockResponse,
        )

    def check_health(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> KeyCheckHealthResponse:
        """
        Check the health of the key

        Checks:

        - If key based logging is configured correctly - sends a test log

        Usage

        Pass the key in the request header

        ```bash
        curl -X POST "http://localhost:4000/key/health"      -H "Authorization: Bearer sk-1234"      -H "Content-Type: application/json"
        ```

        Response when logging callbacks are setup correctly:

        ```json
        {
          "key": "healthy",
          "logging_callbacks": {
            "callbacks": ["gcs_bucket"],
            "status": "healthy",
            "details": "No logger exceptions triggered, system is healthy. Manually check if logs were sent to ['gcs_bucket']"
          }
        }
        ```

        Response when logging callbacks are not setup correctly:

        ```json
        {
          "key": "unhealthy",
          "logging_callbacks": {
            "callbacks": ["gcs_bucket"],
            "status": "unhealthy",
            "details": "Logger exceptions triggered, system is unhealthy: Failed to load vertex credentials. Check to see if credentials containing partial/invalid information."
          }
        }
        ```
        """
        return self._post(
            "/key/health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyCheckHealthResponse,
        )

    def generate(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key: Optional[str] | NotGiven = NOT_GIVEN,
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
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> GenerateKeyResponse:
        """
        Generate an API key based on the provided data.

        Docs: https://docs.hanzo.ai/docs/proxy/virtual_keys

        Parameters:

        - duration: Optional[str] - Specify the length of time the token is valid for.
          You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days
          ("30d").
        - key_alias: Optional[str] - User defined key alias
        - key: Optional[str] - User defined key value. If not set, a 16-digit unique
          sk-key is created for you.
        - team_id: Optional[str] - The team id of the key
        - user_id: Optional[str] - The user id of the key
        - budget_id: Optional[str] - The budget id associated with the key. Created by
          calling `/budget/new`.
        - models: Optional[list] - Model_name's a user is allowed to call. (if empty,
          key is allowed to call all models)
        - aliases: Optional[dict] - Any alias mappings, on top of anything in the
          config.yaml model list. -
          https://docs.hanzo.ai/docs/proxy/virtual_keys#managing-auth---upgradedowngrade-models
        - config: Optional[dict] - any key-specific configs, overrides config in
          config.yaml
        - spend: Optional[int] - Amount spent by key. Default is 0. Will be updated by
          proxy whenever key is used.
          https://docs.hanzo.ai/docs/proxy/virtual_keys#managing-auth---tracking-spend
        - send_invite_email: Optional[bool] - Whether to send an invite email to the
          user_id, with the generate key
        - max_budget: Optional[float] - Specify max budget for a given key.
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
        - max_parallel_requests: Optional[int] - Rate limit a user based on the number
          of parallel requests. Raises 429 error, if user's parallel requests > x.
        - metadata: Optional[dict] - Metadata for key, store information for key.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - guardrails: Optional[List[str]] - List of active guardrails for the key
        - permissions: Optional[dict] - key-specific permissions. Currently just used
          for turning off pii masking (if connected). Example - {"pii": false}
        - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
          {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}}. IF null or {} then
          no model specific budget.
        - model_rpm_limit: Optional[dict] - key-specific model rpm limit. Example -
          {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model
          specific rpm limit.
        - model_tpm_limit: Optional[dict] - key-specific model tpm limit. Example -
          {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model
          specific tpm limit.
        - allowed_cache_controls: Optional[list] - List of allowed cache control values.
          Example - ["no-cache", "no-store"]. See all values -
          https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request
        - blocked: Optional[bool] - Whether the key is blocked.
        - rpm_limit: Optional[int] - Specify rpm limit for a given key (Requests per
          minute)
        - tpm_limit: Optional[int] - Specify tpm limit for a given key (Tokens per
          minute)
        - soft_budget: Optional[float] - Specify soft budget for a given key. Will
          trigger a slack alert when this soft budget is reached.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - enforced_params: Optional[List[str]] - List of enforced params for the key
          (Enterprise only).
          [Docs](https://docs.hanzo.ai/docs/proxy/enterprise#enforce-required-params-for-llm-requests)

        Examples:

        1. Allow users to turn on/off pii masking

        ```bash
        curl --location 'http://0.0.0.0:4000/key/generate'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "permissions": {"allow_pii_controls": true}
        }'
        ```

        Returns:

        - key: (str) The generated api key
        - expires: (datetime) Datetime object for when key expires.
        - user_id: (str) Unique user id - used for tracking spend across multiple keys
          for same user id.

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
            "/key/generate",
            body=maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
                    "guardrails": guardrails,
                    "key": key,
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
                    "soft_budget": soft_budget,
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_generate_params.KeyGenerateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateKeyResponse,
        )

    def regenerate_by_key(
        self,
        path_key: str,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        body_key: Optional[str] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        new_master_key: Optional[str] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        send_invite_email: Optional[bool] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Optional[GenerateKeyResponse]:
        """
        Regenerate an existing API key while optionally updating its parameters.

        Parameters:

        - key: str (path parameter) - The key to regenerate
        - data: Optional[RegenerateKeyRequest] - Request body containing optional
          parameters to update
          - key_alias: Optional[str] - User-friendly key alias
          - user_id: Optional[str] - User ID associated with key
          - team_id: Optional[str] - Team ID associated with key
          - models: Optional[list] - Model_name's a user is allowed to call
          - tags: Optional[List[str]] - Tags for organizing keys (Enterprise only)
          - spend: Optional[float] - Amount spent by key
          - max_budget: Optional[float] - Max budget for key
          - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
            {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}
          - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
          - soft_budget: Optional[float] - Soft budget limit (warning vs. hard stop).
            Will trigger a slack alert when this soft budget is reached.
          - max_parallel_requests: Optional[int] - Rate limit for parallel requests
          - metadata: Optional[dict] - Metadata for key. Example {"team": "core-infra",
            "app": "app2"}
          - tpm_limit: Optional[int] - Tokens per minute limit
          - rpm_limit: Optional[int] - Requests per minute limit
          - model_rpm_limit: Optional[dict] - Model-specific RPM limits {"gpt-4": 100,
            "claude-v1": 200}
          - model_tpm_limit: Optional[dict] - Model-specific TPM limits {"gpt-4":
            100000, "claude-v1": 200000}
          - allowed_cache_controls: Optional[list] - List of allowed cache control
            values
          - duration: Optional[str] - Key validity duration ("30d", "1h", etc.)
          - permissions: Optional[dict] - Key-specific permissions
          - guardrails: Optional[List[str]] - List of active guardrails for the key
          - blocked: Optional[bool] - Whether the key is blocked

        Returns:

        - GenerateKeyResponse containing the new key and its updated parameters

        Example:

        ```bash
        curl --location --request POST 'http://localhost:4000/key/sk-1234/regenerate'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "max_budget": 100,
            "metadata": {"team": "core-infra"},
            "models": ["gpt-4", "gpt-3.5-turbo"]
        }'
        ```

        Note: This is an Enterprise feature. It requires a premium license to use.

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not path_key:
            raise ValueError(f"Expected a non-empty value for `path_key` but received {path_key!r}")
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return self._post(
            f"/key/{path_key}/regenerate",
            body=maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
                    "guardrails": guardrails,
                    "body_key": body_key,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "new_master_key": new_master_key,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "send_invite_email": send_invite_email,
                    "soft_budget": soft_budget,
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_regenerate_by_key_params.KeyRegenerateByKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateKeyResponse,
        )

    def retrieve_info(
        self,
        *,
        key: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieve information about a key.

        Parameters: key: Optional[str] = Query
        parameter representing the key in the request user_api_key_dict: UserAPIKeyAuth
        = Dependency representing the user's API key Returns: Dict containing the key
        and its associated information

        Example Curl:

        ```
        curl -X GET "http://0.0.0.0:4000/key/info?key=sk-02Wr4IAlN3NvPXvL5JVvDA" -H "Authorization: Bearer sk-1234"
        ```

        Example Curl - if no key is passed, it will use the Key Passed in Authorization
        Header

        ```
        curl -X GET "http://0.0.0.0:4000/key/info" -H "Authorization: Bearer sk-02Wr4IAlN3NvPXvL5JVvDA"
        ```

        Args:
          key: Key in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/key/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"key": key}, key_retrieve_info_params.KeyRetrieveInfoParams),
            ),
            cast_to=object,
        )

    def unblock(
        self,
        *,
        key: str,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Unblock a Virtual key to allow it to make requests again.

        Parameters:

        - key: str - The key to unblock. Can be either the unhashed key (sk-...) or the
          hashed key value

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/unblock'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-Fn8Ej39NxjAXrvpUGKghGw"
        }'
        ```

        Note: This is an admin-only endpoint. Only proxy admins can unblock keys.

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
            "/key/unblock",
            body=maybe_transform({"key": key}, key_unblock_params.KeyUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncKeyResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncKeyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncKeyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKeyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncKeyResourceWithStreamingResponse(self)

    async def update(
        self,
        *,
        key: str,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
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
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        temp_budget_expiry: Union[str, datetime, None] | NotGiven = NOT_GIVEN,
        temp_budget_increase: Optional[float] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing API key's parameters.

        Parameters:

        - key: str - The key to update
        - key_alias: Optional[str] - User-friendly key alias
        - user_id: Optional[str] - User ID associated with key
        - team_id: Optional[str] - Team ID associated with key
        - budget_id: Optional[str] - The budget id associated with the key. Created by
          calling `/budget/new`.
        - models: Optional[list] - Model_name's a user is allowed to call
        - tags: Optional[List[str]] - Tags for organizing keys (Enterprise only)
        - enforced_params: Optional[List[str]] - List of enforced params for the key
          (Enterprise only).
          [Docs](https://docs.hanzo.ai/docs/proxy/enterprise#enforce-required-params-for-llm-requests)
        - spend: Optional[float] - Amount spent by key
        - max_budget: Optional[float] - Max budget for key
        - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
          {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}
        - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
        - soft_budget: Optional[float] - [TODO] Soft budget limit (warning vs. hard
          stop). Will trigger a slack alert when this soft budget is reached.
        - max_parallel_requests: Optional[int] - Rate limit for parallel requests
        - metadata: Optional[dict] - Metadata for key. Example {"team": "core-infra",
          "app": "app2"}
        - tpm_limit: Optional[int] - Tokens per minute limit
        - rpm_limit: Optional[int] - Requests per minute limit
        - model_rpm_limit: Optional[dict] - Model-specific RPM limits {"gpt-4": 100,
          "claude-v1": 200}
        - model_tpm_limit: Optional[dict] - Model-specific TPM limits {"gpt-4": 100000,
          "claude-v1": 200000}
        - allowed_cache_controls: Optional[list] - List of allowed cache control values
        - duration: Optional[str] - Key validity duration ("30d", "1h", etc.)
        - permissions: Optional[dict] - Key-specific permissions
        - send_invite_email: Optional[bool] - Send invite email to user_id
        - guardrails: Optional[List[str]] - List of active guardrails for the key
        - blocked: Optional[bool] - Whether the key is blocked
        - aliases: Optional[dict] - Model aliases for the key -
          [Docs](https://llm.vercel.app/docs/proxy/virtual_keys#model-aliases)
        - config: Optional[dict] - [DEPRECATED PARAM] Key-specific config.
        - temp_budget_increase: Optional[float] - Temporary budget increase for the key
          (Enterprise only).
        - temp_budget_expiry: Optional[str] - Expiry time for the temporary budget
          increase (Enterprise only).

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/update'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-1234",
            "key_alias": "my-key",
            "user_id": "user-1234",
            "team_id": "team-1234",
            "max_budget": 100,
            "metadata": {"any_key": "any-val"},
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
            "/key/update",
            body=await async_maybe_transform(
                {
                    "key": key,
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
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
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "temp_budget_expiry": temp_budget_expiry,
                    "temp_budget_increase": temp_budget_increase,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_update_params.KeyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        include_team_keys: bool | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        organization_id: Optional[str] | NotGiven = NOT_GIVEN,
        page: int | NotGiven = NOT_GIVEN,
        return_full_object: bool | NotGiven = NOT_GIVEN,
        size: int | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> KeyListResponse:
        """
        List all keys for a given user / team / organization.

        Returns: { "keys": List[str] or List[UserAPIKeyAuth], "total_count": int,
        "current_page": int, "total_pages": int, }

        Args:
          include_team_keys: Include all keys for teams that user is an admin of.

          key_alias: Filter keys by key alias

          organization_id: Filter keys by organization ID

          page: Page number

          return_full_object: Return full key object

          size: Page size

          team_id: Filter keys by team ID

          user_id: Filter keys by user ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/key/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "include_team_keys": include_team_keys,
                        "key_alias": key_alias,
                        "organization_id": organization_id,
                        "page": page,
                        "return_full_object": return_full_object,
                        "size": size,
                        "team_id": team_id,
                        "user_id": user_id,
                    },
                    key_list_params.KeyListParams,
                ),
            ),
            cast_to=KeyListResponse,
        )

    async def delete(
        self,
        *,
        key_aliases: Optional[List[str]] | NotGiven = NOT_GIVEN,
        keys: Optional[List[str]] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a key from the key management system.

        Parameters::

        - keys (List[str]): A list of keys or hashed keys to delete. Example {"keys":
          ["sk-QWrxEynunsNpV1zT48HIrw",
          "837e17519f44683334df5291321d97b8bf1098cd490e49e215f6fea935aa28be"]}
        - key_aliases (List[str]): A list of key aliases to delete. Can be passed
          instead of `keys`.Example {"key_aliases": ["alias1", "alias2"]}

        Returns:

        - deleted_keys (List[str]): A list of deleted keys. Example {"deleted_keys":
          ["sk-QWrxEynunsNpV1zT48HIrw",
          "837e17519f44683334df5291321d97b8bf1098cd490e49e215f6fea935aa28be"]}

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "keys": ["sk-QWrxEynunsNpV1zT48HIrw"]
        }'
        ```

        Raises: HTTPException: If an error occurs during key deletion.

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
            "/key/delete",
            body=await async_maybe_transform(
                {
                    "key_aliases": key_aliases,
                    "keys": keys,
                },
                key_delete_params.KeyDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def block(
        self,
        *,
        key: str,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Optional[KeyBlockResponse]:
        """
        Block an Virtual key from making any requests.

        Parameters:

        - key: str - The key to block. Can be either the unhashed key (sk-...) or the
          hashed key value

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/block'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-Fn8Ej39NxjAXrvpUGKghGw"
        }'
        ```

        Note: This is an admin-only endpoint. Only proxy admins can block keys.

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
            "/key/block",
            body=await async_maybe_transform({"key": key}, key_block_params.KeyBlockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyBlockResponse,
        )

    async def check_health(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> KeyCheckHealthResponse:
        """
        Check the health of the key

        Checks:

        - If key based logging is configured correctly - sends a test log

        Usage

        Pass the key in the request header

        ```bash
        curl -X POST "http://localhost:4000/key/health"      -H "Authorization: Bearer sk-1234"      -H "Content-Type: application/json"
        ```

        Response when logging callbacks are setup correctly:

        ```json
        {
          "key": "healthy",
          "logging_callbacks": {
            "callbacks": ["gcs_bucket"],
            "status": "healthy",
            "details": "No logger exceptions triggered, system is healthy. Manually check if logs were sent to ['gcs_bucket']"
          }
        }
        ```

        Response when logging callbacks are not setup correctly:

        ```json
        {
          "key": "unhealthy",
          "logging_callbacks": {
            "callbacks": ["gcs_bucket"],
            "status": "unhealthy",
            "details": "Logger exceptions triggered, system is unhealthy: Failed to load vertex credentials. Check to see if credentials containing partial/invalid information."
          }
        }
        ```
        """
        return await self._post(
            "/key/health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyCheckHealthResponse,
        )

    async def generate(
        self,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        key: Optional[str] | NotGiven = NOT_GIVEN,
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
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> GenerateKeyResponse:
        """
        Generate an API key based on the provided data.

        Docs: https://docs.hanzo.ai/docs/proxy/virtual_keys

        Parameters:

        - duration: Optional[str] - Specify the length of time the token is valid for.
          You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days
          ("30d").
        - key_alias: Optional[str] - User defined key alias
        - key: Optional[str] - User defined key value. If not set, a 16-digit unique
          sk-key is created for you.
        - team_id: Optional[str] - The team id of the key
        - user_id: Optional[str] - The user id of the key
        - budget_id: Optional[str] - The budget id associated with the key. Created by
          calling `/budget/new`.
        - models: Optional[list] - Model_name's a user is allowed to call. (if empty,
          key is allowed to call all models)
        - aliases: Optional[dict] - Any alias mappings, on top of anything in the
          config.yaml model list. -
          https://docs.hanzo.ai/docs/proxy/virtual_keys#managing-auth---upgradedowngrade-models
        - config: Optional[dict] - any key-specific configs, overrides config in
          config.yaml
        - spend: Optional[int] - Amount spent by key. Default is 0. Will be updated by
          proxy whenever key is used.
          https://docs.hanzo.ai/docs/proxy/virtual_keys#managing-auth---tracking-spend
        - send_invite_email: Optional[bool] - Whether to send an invite email to the
          user_id, with the generate key
        - max_budget: Optional[float] - Specify max budget for a given key.
        - budget_duration: Optional[str] - Budget is reset at the end of specified
          duration. If not set, budget is never reset. You can set duration as seconds
          ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
        - max_parallel_requests: Optional[int] - Rate limit a user based on the number
          of parallel requests. Raises 429 error, if user's parallel requests > x.
        - metadata: Optional[dict] - Metadata for key, store information for key.
          Example metadata = {"team": "core-infra", "app": "app2", "email": "z@hanzo.ai"
          }
        - guardrails: Optional[List[str]] - List of active guardrails for the key
        - permissions: Optional[dict] - key-specific permissions. Currently just used
          for turning off pii masking (if connected). Example - {"pii": false}
        - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
          {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}}. IF null or {} then
          no model specific budget.
        - model_rpm_limit: Optional[dict] - key-specific model rpm limit. Example -
          {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model
          specific rpm limit.
        - model_tpm_limit: Optional[dict] - key-specific model tpm limit. Example -
          {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model
          specific tpm limit.
        - allowed_cache_controls: Optional[list] - List of allowed cache control values.
          Example - ["no-cache", "no-store"]. See all values -
          https://docs.hanzo.ai/docs/proxy/caching#turn-on--off-caching-per-request
        - blocked: Optional[bool] - Whether the key is blocked.
        - rpm_limit: Optional[int] - Specify rpm limit for a given key (Requests per
          minute)
        - tpm_limit: Optional[int] - Specify tpm limit for a given key (Tokens per
          minute)
        - soft_budget: Optional[float] - Specify soft budget for a given key. Will
          trigger a slack alert when this soft budget is reached.
        - tags: Optional[List[str]] - Tags for
          [tracking spend](https://llm.vercel.app/docs/proxy/enterprise#tracking-spend-for-custom-tags)
          and/or doing
          [tag-based routing](https://llm.vercel.app/docs/proxy/tag_routing).
        - enforced_params: Optional[List[str]] - List of enforced params for the key
          (Enterprise only).
          [Docs](https://docs.hanzo.ai/docs/proxy/enterprise#enforce-required-params-for-llm-requests)

        Examples:

        1. Allow users to turn on/off pii masking

        ```bash
        curl --location 'http://0.0.0.0:4000/key/generate'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
                "permissions": {"allow_pii_controls": true}
        }'
        ```

        Returns:

        - key: (str) The generated api key
        - expires: (datetime) Datetime object for when key expires.
        - user_id: (str) Unique user id - used for tracking spend across multiple keys
          for same user id.

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
            "/key/generate",
            body=await async_maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
                    "guardrails": guardrails,
                    "key": key,
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
                    "soft_budget": soft_budget,
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_generate_params.KeyGenerateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateKeyResponse,
        )

    async def regenerate_by_key(
        self,
        path_key: str,
        *,
        aliases: Optional[object] | NotGiven = NOT_GIVEN,
        allowed_cache_controls: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        blocked: Optional[bool] | NotGiven = NOT_GIVEN,
        budget_duration: Optional[str] | NotGiven = NOT_GIVEN,
        budget_id: Optional[str] | NotGiven = NOT_GIVEN,
        config: Optional[object] | NotGiven = NOT_GIVEN,
        duration: Optional[str] | NotGiven = NOT_GIVEN,
        enforced_params: Optional[List[str]] | NotGiven = NOT_GIVEN,
        guardrails: Optional[List[str]] | NotGiven = NOT_GIVEN,
        body_key: Optional[str] | NotGiven = NOT_GIVEN,
        key_alias: Optional[str] | NotGiven = NOT_GIVEN,
        max_budget: Optional[float] | NotGiven = NOT_GIVEN,
        max_parallel_requests: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[object] | NotGiven = NOT_GIVEN,
        model_max_budget: Optional[object] | NotGiven = NOT_GIVEN,
        model_rpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        model_tpm_limit: Optional[object] | NotGiven = NOT_GIVEN,
        models: Optional[Iterable[object]] | NotGiven = NOT_GIVEN,
        new_master_key: Optional[str] | NotGiven = NOT_GIVEN,
        permissions: Optional[object] | NotGiven = NOT_GIVEN,
        rpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        send_invite_email: Optional[bool] | NotGiven = NOT_GIVEN,
        soft_budget: Optional[float] | NotGiven = NOT_GIVEN,
        spend: Optional[float] | NotGiven = NOT_GIVEN,
        tags: Optional[List[str]] | NotGiven = NOT_GIVEN,
        team_id: Optional[str] | NotGiven = NOT_GIVEN,
        tpm_limit: Optional[int] | NotGiven = NOT_GIVEN,
        user_id: Optional[str] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Optional[GenerateKeyResponse]:
        """
        Regenerate an existing API key while optionally updating its parameters.

        Parameters:

        - key: str (path parameter) - The key to regenerate
        - data: Optional[RegenerateKeyRequest] - Request body containing optional
          parameters to update
          - key_alias: Optional[str] - User-friendly key alias
          - user_id: Optional[str] - User ID associated with key
          - team_id: Optional[str] - Team ID associated with key
          - models: Optional[list] - Model_name's a user is allowed to call
          - tags: Optional[List[str]] - Tags for organizing keys (Enterprise only)
          - spend: Optional[float] - Amount spent by key
          - max_budget: Optional[float] - Max budget for key
          - model_max_budget: Optional[Dict[str, BudgetConfig]] - Model-specific budgets
            {"gpt-4": {"budget_limit": 0.0005, "time_period": "30d"}}
          - budget_duration: Optional[str] - Budget reset period ("30d", "1h", etc.)
          - soft_budget: Optional[float] - Soft budget limit (warning vs. hard stop).
            Will trigger a slack alert when this soft budget is reached.
          - max_parallel_requests: Optional[int] - Rate limit for parallel requests
          - metadata: Optional[dict] - Metadata for key. Example {"team": "core-infra",
            "app": "app2"}
          - tpm_limit: Optional[int] - Tokens per minute limit
          - rpm_limit: Optional[int] - Requests per minute limit
          - model_rpm_limit: Optional[dict] - Model-specific RPM limits {"gpt-4": 100,
            "claude-v1": 200}
          - model_tpm_limit: Optional[dict] - Model-specific TPM limits {"gpt-4":
            100000, "claude-v1": 200000}
          - allowed_cache_controls: Optional[list] - List of allowed cache control
            values
          - duration: Optional[str] - Key validity duration ("30d", "1h", etc.)
          - permissions: Optional[dict] - Key-specific permissions
          - guardrails: Optional[List[str]] - List of active guardrails for the key
          - blocked: Optional[bool] - Whether the key is blocked

        Returns:

        - GenerateKeyResponse containing the new key and its updated parameters

        Example:

        ```bash
        curl --location --request POST 'http://localhost:4000/key/sk-1234/regenerate'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data-raw '{
            "max_budget": 100,
            "metadata": {"team": "core-infra"},
            "models": ["gpt-4", "gpt-3.5-turbo"]
        }'
        ```

        Note: This is an Enterprise feature. It requires a premium license to use.

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not path_key:
            raise ValueError(f"Expected a non-empty value for `path_key` but received {path_key!r}")
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return await self._post(
            f"/key/{path_key}/regenerate",
            body=await async_maybe_transform(
                {
                    "aliases": aliases,
                    "allowed_cache_controls": allowed_cache_controls,
                    "blocked": blocked,
                    "budget_duration": budget_duration,
                    "budget_id": budget_id,
                    "config": config,
                    "duration": duration,
                    "enforced_params": enforced_params,
                    "guardrails": guardrails,
                    "body_key": body_key,
                    "key_alias": key_alias,
                    "max_budget": max_budget,
                    "max_parallel_requests": max_parallel_requests,
                    "metadata": metadata,
                    "model_max_budget": model_max_budget,
                    "model_rpm_limit": model_rpm_limit,
                    "model_tpm_limit": model_tpm_limit,
                    "models": models,
                    "new_master_key": new_master_key,
                    "permissions": permissions,
                    "rpm_limit": rpm_limit,
                    "send_invite_email": send_invite_email,
                    "soft_budget": soft_budget,
                    "spend": spend,
                    "tags": tags,
                    "team_id": team_id,
                    "tpm_limit": tpm_limit,
                    "user_id": user_id,
                },
                key_regenerate_by_key_params.KeyRegenerateByKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateKeyResponse,
        )

    async def retrieve_info(
        self,
        *,
        key: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieve information about a key.

        Parameters: key: Optional[str] = Query
        parameter representing the key in the request user_api_key_dict: UserAPIKeyAuth
        = Dependency representing the user's API key Returns: Dict containing the key
        and its associated information

        Example Curl:

        ```
        curl -X GET "http://0.0.0.0:4000/key/info?key=sk-02Wr4IAlN3NvPXvL5JVvDA" -H "Authorization: Bearer sk-1234"
        ```

        Example Curl - if no key is passed, it will use the Key Passed in Authorization
        Header

        ```
        curl -X GET "http://0.0.0.0:4000/key/info" -H "Authorization: Bearer sk-02Wr4IAlN3NvPXvL5JVvDA"
        ```

        Args:
          key: Key in the request parameters

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/key/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"key": key}, key_retrieve_info_params.KeyRetrieveInfoParams),
            ),
            cast_to=object,
        )

    async def unblock(
        self,
        *,
        key: str,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Unblock a Virtual key to allow it to make requests again.

        Parameters:

        - key: str - The key to unblock. Can be either the unhashed key (sk-...) or the
          hashed key value

        Example:

        ```bash
        curl --location 'http://0.0.0.0:4000/key/unblock'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "key": "sk-Fn8Ej39NxjAXrvpUGKghGw"
        }'
        ```

        Note: This is an admin-only endpoint. Only proxy admins can unblock keys.

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
            "/key/unblock",
            body=await async_maybe_transform({"key": key}, key_unblock_params.KeyUnblockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class KeyResourceWithRawResponse:
    def __init__(self, key: KeyResource) -> None:
        self._key = key

        self.update = to_raw_response_wrapper(
            key.update,
        )
        self.list = to_raw_response_wrapper(
            key.list,
        )
        self.delete = to_raw_response_wrapper(
            key.delete,
        )
        self.block = to_raw_response_wrapper(
            key.block,
        )
        self.check_health = to_raw_response_wrapper(
            key.check_health,
        )
        self.generate = to_raw_response_wrapper(
            key.generate,
        )
        self.regenerate_by_key = to_raw_response_wrapper(
            key.regenerate_by_key,
        )
        self.retrieve_info = to_raw_response_wrapper(
            key.retrieve_info,
        )
        self.unblock = to_raw_response_wrapper(
            key.unblock,
        )


class AsyncKeyResourceWithRawResponse:
    def __init__(self, key: AsyncKeyResource) -> None:
        self._key = key

        self.update = async_to_raw_response_wrapper(
            key.update,
        )
        self.list = async_to_raw_response_wrapper(
            key.list,
        )
        self.delete = async_to_raw_response_wrapper(
            key.delete,
        )
        self.block = async_to_raw_response_wrapper(
            key.block,
        )
        self.check_health = async_to_raw_response_wrapper(
            key.check_health,
        )
        self.generate = async_to_raw_response_wrapper(
            key.generate,
        )
        self.regenerate_by_key = async_to_raw_response_wrapper(
            key.regenerate_by_key,
        )
        self.retrieve_info = async_to_raw_response_wrapper(
            key.retrieve_info,
        )
        self.unblock = async_to_raw_response_wrapper(
            key.unblock,
        )


class KeyResourceWithStreamingResponse:
    def __init__(self, key: KeyResource) -> None:
        self._key = key

        self.update = to_streamed_response_wrapper(
            key.update,
        )
        self.list = to_streamed_response_wrapper(
            key.list,
        )
        self.delete = to_streamed_response_wrapper(
            key.delete,
        )
        self.block = to_streamed_response_wrapper(
            key.block,
        )
        self.check_health = to_streamed_response_wrapper(
            key.check_health,
        )
        self.generate = to_streamed_response_wrapper(
            key.generate,
        )
        self.regenerate_by_key = to_streamed_response_wrapper(
            key.regenerate_by_key,
        )
        self.retrieve_info = to_streamed_response_wrapper(
            key.retrieve_info,
        )
        self.unblock = to_streamed_response_wrapper(
            key.unblock,
        )


class AsyncKeyResourceWithStreamingResponse:
    def __init__(self, key: AsyncKeyResource) -> None:
        self._key = key

        self.update = async_to_streamed_response_wrapper(
            key.update,
        )
        self.list = async_to_streamed_response_wrapper(
            key.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            key.delete,
        )
        self.block = async_to_streamed_response_wrapper(
            key.block,
        )
        self.check_health = async_to_streamed_response_wrapper(
            key.check_health,
        )
        self.generate = async_to_streamed_response_wrapper(
            key.generate,
        )
        self.regenerate_by_key = async_to_streamed_response_wrapper(
            key.regenerate_by_key,
        )
        self.retrieve_info = async_to_streamed_response_wrapper(
            key.retrieve_info,
        )
        self.unblock = async_to_streamed_response_wrapper(
            key.unblock,
        )
