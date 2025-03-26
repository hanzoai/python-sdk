# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal

import httpx

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
from ...types.team import callback_add_params
from ..._base_client import make_request_options

__all__ = ["CallbackResource", "AsyncCallbackResource"]


class CallbackResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CallbackResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return CallbackResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CallbackResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return CallbackResourceWithStreamingResponse(self)

    def retrieve(
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
        Get the success/failure callbacks and variables for a team

        Parameters:

        - team_id (str, required): The unique identifier for the team

        Example curl:

        ```
        curl -X GET 'http://localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/callback'         -H 'Authorization: Bearer sk-1234'
        ```

        This will return the callback settings for the team with id
        dbe2f686-a686-4896-864a-4c3924458709

        Returns { "status": "success", "data": { "team_id": team_id,
        "success_callbacks": team_callback_settings_obj.success_callback,
        "failure_callbacks": team_callback_settings_obj.failure_callback,
        "callback_vars": team_callback_settings_obj.callback_vars, }, }

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        return self._get(
            f"/team/{team_id}/callback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def add(
        self,
        team_id: str,
        *,
        callback_name: str,
        callback_vars: Dict[str, str],
        callback_type: Optional[Literal["success", "failure", "success_and_failure"]] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Add a success/failure callback to a team

        Use this if if you want different teams to have different success/failure
        callbacks

        Parameters:

        - callback_name (Literal["langfuse", "langsmith", "gcs"], required): The name of
          the callback to add
        - callback_type (Literal["success", "failure", "success_and_failure"],
          required): The type of callback to add. One of:
          - "success": Callback for successful LLM calls
          - "failure": Callback for failed LLM calls
          - "success_and_failure": Callback for both successful and failed LLM calls
        - callback_vars (StandardCallbackDynamicParams, required): A dictionary of
          variables to pass to the callback
          - langfuse_public_key: The public key for the Langfuse callback
          - langfuse_secret_key: The secret key for the Langfuse callback
          - langfuse_secret: The secret for the Langfuse callback
          - langfuse_host: The host for the Langfuse callback
          - gcs_bucket_name: The name of the GCS bucket
          - gcs_path_service_account: The path to the GCS service account
          - langsmith_api_key: The API key for the Langsmith callback
          - langsmith_project: The project for the Langsmith callback
          - langsmith_base_url: The base URL for the Langsmith callback

        Example curl:

        ```
        curl -X POST 'http:/localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/callback'         -H 'Content-Type: application/json'         -H 'Authorization: Bearer sk-1234'         -d '{
            "callback_name": "langfuse",
            "callback_type": "success",
            "callback_vars": {"langfuse_public_key": "pk-lf-xxxx1", "langfuse_secret_key": "sk-xxxxx"}

        }'
        ```

        This means for the team where team_id = dbe2f686-a686-4896-864a-4c3924458709,
        all LLM calls will be logged to langfuse using the public key pk-lf-xxxx1 and
        the secret key sk-xxxxx

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return self._post(
            f"/team/{team_id}/callback",
            body=maybe_transform(
                {
                    "callback_name": callback_name,
                    "callback_vars": callback_vars,
                    "callback_type": callback_type,
                },
                callback_add_params.CallbackAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCallbackResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCallbackResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCallbackResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCallbackResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncCallbackResourceWithStreamingResponse(self)

    async def retrieve(
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
        Get the success/failure callbacks and variables for a team

        Parameters:

        - team_id (str, required): The unique identifier for the team

        Example curl:

        ```
        curl -X GET 'http://localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/callback'         -H 'Authorization: Bearer sk-1234'
        ```

        This will return the callback settings for the team with id
        dbe2f686-a686-4896-864a-4c3924458709

        Returns { "status": "success", "data": { "team_id": team_id,
        "success_callbacks": team_callback_settings_obj.success_callback,
        "failure_callbacks": team_callback_settings_obj.failure_callback,
        "callback_vars": team_callback_settings_obj.callback_vars, }, }

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        return await self._get(
            f"/team/{team_id}/callback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def add(
        self,
        team_id: str,
        *,
        callback_name: str,
        callback_vars: Dict[str, str],
        callback_type: Optional[Literal["success", "failure", "success_and_failure"]] | NotGiven = NOT_GIVEN,
        llm_changed_by: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Add a success/failure callback to a team

        Use this if if you want different teams to have different success/failure
        callbacks

        Parameters:

        - callback_name (Literal["langfuse", "langsmith", "gcs"], required): The name of
          the callback to add
        - callback_type (Literal["success", "failure", "success_and_failure"],
          required): The type of callback to add. One of:
          - "success": Callback for successful LLM calls
          - "failure": Callback for failed LLM calls
          - "success_and_failure": Callback for both successful and failed LLM calls
        - callback_vars (StandardCallbackDynamicParams, required): A dictionary of
          variables to pass to the callback
          - langfuse_public_key: The public key for the Langfuse callback
          - langfuse_secret_key: The secret key for the Langfuse callback
          - langfuse_secret: The secret for the Langfuse callback
          - langfuse_host: The host for the Langfuse callback
          - gcs_bucket_name: The name of the GCS bucket
          - gcs_path_service_account: The path to the GCS service account
          - langsmith_api_key: The API key for the Langsmith callback
          - langsmith_project: The project for the Langsmith callback
          - langsmith_base_url: The base URL for the Langsmith callback

        Example curl:

        ```
        curl -X POST 'http:/localhost:4000/team/dbe2f686-a686-4896-864a-4c3924458709/callback'         -H 'Content-Type: application/json'         -H 'Authorization: Bearer sk-1234'         -d '{
            "callback_name": "langfuse",
            "callback_type": "success",
            "callback_vars": {"langfuse_public_key": "pk-lf-xxxx1", "langfuse_secret_key": "sk-xxxxx"}

        }'
        ```

        This means for the team where team_id = dbe2f686-a686-4896-864a-4c3924458709,
        all LLM calls will be logged to langfuse using the public key pk-lf-xxxx1 and
        the secret key sk-xxxxx

        Args:
          llm_changed_by: The llm-changed-by header enables tracking of actions performed by authorized
              users on behalf of other users, providing an audit trail for accountability

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not team_id:
            raise ValueError(f"Expected a non-empty value for `team_id` but received {team_id!r}")
        extra_headers = {**strip_not_given({"llm-changed-by": llm_changed_by}), **(extra_headers or {})}
        return await self._post(
            f"/team/{team_id}/callback",
            body=await async_maybe_transform(
                {
                    "callback_name": callback_name,
                    "callback_vars": callback_vars,
                    "callback_type": callback_type,
                },
                callback_add_params.CallbackAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CallbackResourceWithRawResponse:
    def __init__(self, callback: CallbackResource) -> None:
        self._callback = callback

        self.retrieve = to_raw_response_wrapper(
            callback.retrieve,
        )
        self.add = to_raw_response_wrapper(
            callback.add,
        )


class AsyncCallbackResourceWithRawResponse:
    def __init__(self, callback: AsyncCallbackResource) -> None:
        self._callback = callback

        self.retrieve = async_to_raw_response_wrapper(
            callback.retrieve,
        )
        self.add = async_to_raw_response_wrapper(
            callback.add,
        )


class CallbackResourceWithStreamingResponse:
    def __init__(self, callback: CallbackResource) -> None:
        self._callback = callback

        self.retrieve = to_streamed_response_wrapper(
            callback.retrieve,
        )
        self.add = to_streamed_response_wrapper(
            callback.add,
        )


class AsyncCallbackResourceWithStreamingResponse:
    def __init__(self, callback: AsyncCallbackResource) -> None:
        self._callback = callback

        self.retrieve = async_to_streamed_response_wrapper(
            callback.retrieve,
        )
        self.add = async_to_streamed_response_wrapper(
            callback.add,
        )
