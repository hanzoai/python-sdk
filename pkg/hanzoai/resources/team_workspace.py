# Hanzo AI SDK

from __future__ import annotations

from typing import List, Optional

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

__all__ = ["TeamWorkspaceResource", "AsyncTeamWorkspaceResource"]


class TeamWorkspaceResource(SyncAPIResource):
    """Hanzo Team collaborative workspace platform.

    Backed by the Team account-service (Huly/Santeam-derived).
    Provides account management, workspace CRUD, member invitations,
    OTP/MFA, social login, and admin statistics.

    All endpoints use the ``/team/`` path prefix. The SDK gateway
    translates REST calls to the underlying JSON-RPC account service.
    """

    @cached_property
    def with_raw_response(self) -> TeamWorkspaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return TeamWorkspaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TeamWorkspaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return TeamWorkspaceResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------ #
    # Accounts
    # ------------------------------------------------------------------ #

    def create_account(
        self,
        *,
        email: str,
        password: str,
        first: str,
        last: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new Team workspace account.

        Args:
          email: Account email address.
          password: Account password (hashed server-side).
          first: First name.
          last: Last name.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/accounts",
            body={
                "email": email,
                "password": password,
                "first": first,
                "last": last,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def login(
        self,
        *,
        email: str,
        password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Authenticate and obtain a session token.

        Args:
          email: Account email address.
          password: Account password.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/accounts/login",
            body={"email": email, "password": password},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_account(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get the current account info (requires auth token in header).

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._get(
            "/team/accounts/me",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def change_password(
        self,
        *,
        old_password: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Change the current account password.

        Args:
          old_password: Current password for verification.
          new_password: New password to set.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/accounts/password",
            body={
                "old_password": old_password,
                "new_password": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def request_password_recovery(
        self,
        *,
        email: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Request a password recovery email.

        Args:
          email: Email address associated with the account.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/accounts/password/recovery",
            body={"email": email},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def confirm_password_recovery(
        self,
        *,
        recovery_token: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Confirm password recovery with a token and set a new password.

        Args:
          recovery_token: Token received via recovery email.
          new_password: New password to set.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/accounts/password/recovery/confirm",
            body={
                "token": recovery_token,
                "new_password": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Workspaces
    # ------------------------------------------------------------------ #

    def create_workspace(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new collaborative workspace.

        Args:
          name: Display name for the workspace.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/workspaces",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_workspaces(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all workspaces accessible to the current account.

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._get(
            "/team/workspaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get detailed information for a single workspace.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._get(
            f"/team/workspaces/{workspace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_workspace(
        self,
        workspace_id: str,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update workspace metadata.

        Args:
          workspace_id: Unique workspace identifier.
          name: New display name for the workspace.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._patch(
            f"/team/workspaces/{workspace_id}",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a workspace permanently.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._delete(
            f"/team/workspaces/{workspace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Members
    # ------------------------------------------------------------------ #

    def invite_member(
        self,
        workspace_id: str,
        *,
        email: str,
        role: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Invite a user to a workspace by email.

        Args:
          workspace_id: Unique workspace identifier.
          email: Email of the user to invite.
          role: Role to assign (e.g. ``"admin"``, ``"member"``, ``"guest"``).
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            f"/team/workspaces/{workspace_id}/members",
            body={"email": email, "role": role},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def join_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Join a workspace the current account has been invited to.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            f"/team/workspaces/{workspace_id}/join",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def leave_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Leave a workspace.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            f"/team/workspaces/{workspace_id}/leave",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # OTP / MFA
    # ------------------------------------------------------------------ #

    def send_otp(
        self,
        *,
        email: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send a one-time password to the given email for verification.

        Args:
          email: Email address to send the OTP to.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/otp/send",
            body={"email": email},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def verify_otp(
        self,
        *,
        email: str,
        code: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify a one-time password.

        Args:
          email: Email address the OTP was sent to.
          code: The OTP code to verify.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/otp/verify",
            body={"email": email, "code": code},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Social login
    # ------------------------------------------------------------------ #

    def add_social_id(
        self,
        *,
        provider: str,
        social_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Link a social login provider to the current account.

        Args:
          provider: Social provider name (e.g. ``"google"``, ``"github"``).
          social_id: Provider-specific user identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._post(
            "/team/social",
            body={"provider": provider, "social_id": social_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_social_id(
        self,
        provider: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unlink a social login provider from the current account.

        Args:
          provider: Social provider name to remove (e.g. ``"google"``, ``"github"``).
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._delete(
            f"/team/social/{provider}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Admin
    # ------------------------------------------------------------------ #

    def statistics(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get Team platform server statistics.

        Maps to ``GET /api/v1/statistics`` on the account service.

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return self._get(
            "/team/statistics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncTeamWorkspaceResource(AsyncAPIResource):
    """Async variant of :class:`TeamWorkspaceResource`.

    Hanzo Team collaborative workspace platform.
    Backed by the Team account-service (Huly/Santeam-derived).
    """

    @cached_property
    def with_raw_response(self) -> AsyncTeamWorkspaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTeamWorkspaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTeamWorkspaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncTeamWorkspaceResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------ #
    # Accounts
    # ------------------------------------------------------------------ #

    async def create_account(
        self,
        *,
        email: str,
        password: str,
        first: str,
        last: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new Team workspace account.

        Args:
          email: Account email address.
          password: Account password (hashed server-side).
          first: First name.
          last: Last name.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/accounts",
            body={
                "email": email,
                "password": password,
                "first": first,
                "last": last,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def login(
        self,
        *,
        email: str,
        password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Authenticate and obtain a session token.

        Args:
          email: Account email address.
          password: Account password.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/accounts/login",
            body={"email": email, "password": password},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_account(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get the current account info (requires auth token in header).

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._get(
            "/team/accounts/me",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def change_password(
        self,
        *,
        old_password: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Change the current account password.

        Args:
          old_password: Current password for verification.
          new_password: New password to set.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/accounts/password",
            body={
                "old_password": old_password,
                "new_password": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def request_password_recovery(
        self,
        *,
        email: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Request a password recovery email.

        Args:
          email: Email address associated with the account.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/accounts/password/recovery",
            body={"email": email},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def confirm_password_recovery(
        self,
        *,
        recovery_token: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Confirm password recovery with a token and set a new password.

        Args:
          recovery_token: Token received via recovery email.
          new_password: New password to set.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/accounts/password/recovery/confirm",
            body={
                "token": recovery_token,
                "new_password": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Workspaces
    # ------------------------------------------------------------------ #

    async def create_workspace(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new collaborative workspace.

        Args:
          name: Display name for the workspace.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/workspaces",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_workspaces(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all workspaces accessible to the current account.

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._get(
            "/team/workspaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get detailed information for a single workspace.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._get(
            f"/team/workspaces/{workspace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_workspace(
        self,
        workspace_id: str,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update workspace metadata.

        Args:
          workspace_id: Unique workspace identifier.
          name: New display name for the workspace.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._patch(
            f"/team/workspaces/{workspace_id}",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a workspace permanently.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._delete(
            f"/team/workspaces/{workspace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Members
    # ------------------------------------------------------------------ #

    async def invite_member(
        self,
        workspace_id: str,
        *,
        email: str,
        role: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Invite a user to a workspace by email.

        Args:
          workspace_id: Unique workspace identifier.
          email: Email of the user to invite.
          role: Role to assign (e.g. ``"admin"``, ``"member"``, ``"guest"``).
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            f"/team/workspaces/{workspace_id}/members",
            body={"email": email, "role": role},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def join_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Join a workspace the current account has been invited to.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            f"/team/workspaces/{workspace_id}/join",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def leave_workspace(
        self,
        workspace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Leave a workspace.

        Args:
          workspace_id: Unique workspace identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            f"/team/workspaces/{workspace_id}/leave",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # OTP / MFA
    # ------------------------------------------------------------------ #

    async def send_otp(
        self,
        *,
        email: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send a one-time password to the given email for verification.

        Args:
          email: Email address to send the OTP to.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/otp/send",
            body={"email": email},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def verify_otp(
        self,
        *,
        email: str,
        code: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify a one-time password.

        Args:
          email: Email address the OTP was sent to.
          code: The OTP code to verify.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/otp/verify",
            body={"email": email, "code": code},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Social login
    # ------------------------------------------------------------------ #

    async def add_social_id(
        self,
        *,
        provider: str,
        social_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Link a social login provider to the current account.

        Args:
          provider: Social provider name (e.g. ``"google"``, ``"github"``).
          social_id: Provider-specific user identifier.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._post(
            "/team/social",
            body={"provider": provider, "social_id": social_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_social_id(
        self,
        provider: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unlink a social login provider from the current account.

        Args:
          provider: Social provider name to remove (e.g. ``"google"``, ``"github"``).
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._delete(
            f"/team/social/{provider}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------ #
    # Admin
    # ------------------------------------------------------------------ #

    async def statistics(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get Team platform server statistics.

        Maps to ``GET /api/v1/statistics`` on the account service.

        Args:
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        return await self._get(
            "/team/statistics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ====================================================================== #
# Raw response wrappers
# ====================================================================== #


class TeamWorkspaceResourceWithRawResponse:
    def __init__(self, team_workspace: TeamWorkspaceResource) -> None:
        self._team_workspace = team_workspace

        # Accounts
        self.create_account = to_raw_response_wrapper(
            team_workspace.create_account,
        )
        self.login = to_raw_response_wrapper(
            team_workspace.login,
        )
        self.get_account = to_raw_response_wrapper(
            team_workspace.get_account,
        )
        self.change_password = to_raw_response_wrapper(
            team_workspace.change_password,
        )
        self.request_password_recovery = to_raw_response_wrapper(
            team_workspace.request_password_recovery,
        )
        self.confirm_password_recovery = to_raw_response_wrapper(
            team_workspace.confirm_password_recovery,
        )

        # Workspaces
        self.create_workspace = to_raw_response_wrapper(
            team_workspace.create_workspace,
        )
        self.list_workspaces = to_raw_response_wrapper(
            team_workspace.list_workspaces,
        )
        self.get_workspace = to_raw_response_wrapper(
            team_workspace.get_workspace,
        )
        self.update_workspace = to_raw_response_wrapper(
            team_workspace.update_workspace,
        )
        self.delete_workspace = to_raw_response_wrapper(
            team_workspace.delete_workspace,
        )

        # Members
        self.invite_member = to_raw_response_wrapper(
            team_workspace.invite_member,
        )
        self.join_workspace = to_raw_response_wrapper(
            team_workspace.join_workspace,
        )
        self.leave_workspace = to_raw_response_wrapper(
            team_workspace.leave_workspace,
        )

        # OTP
        self.send_otp = to_raw_response_wrapper(
            team_workspace.send_otp,
        )
        self.verify_otp = to_raw_response_wrapper(
            team_workspace.verify_otp,
        )

        # Social
        self.add_social_id = to_raw_response_wrapper(
            team_workspace.add_social_id,
        )
        self.remove_social_id = to_raw_response_wrapper(
            team_workspace.remove_social_id,
        )

        # Admin
        self.statistics = to_raw_response_wrapper(
            team_workspace.statistics,
        )


class AsyncTeamWorkspaceResourceWithRawResponse:
    def __init__(self, team_workspace: AsyncTeamWorkspaceResource) -> None:
        self._team_workspace = team_workspace

        # Accounts
        self.create_account = async_to_raw_response_wrapper(
            team_workspace.create_account,
        )
        self.login = async_to_raw_response_wrapper(
            team_workspace.login,
        )
        self.get_account = async_to_raw_response_wrapper(
            team_workspace.get_account,
        )
        self.change_password = async_to_raw_response_wrapper(
            team_workspace.change_password,
        )
        self.request_password_recovery = async_to_raw_response_wrapper(
            team_workspace.request_password_recovery,
        )
        self.confirm_password_recovery = async_to_raw_response_wrapper(
            team_workspace.confirm_password_recovery,
        )

        # Workspaces
        self.create_workspace = async_to_raw_response_wrapper(
            team_workspace.create_workspace,
        )
        self.list_workspaces = async_to_raw_response_wrapper(
            team_workspace.list_workspaces,
        )
        self.get_workspace = async_to_raw_response_wrapper(
            team_workspace.get_workspace,
        )
        self.update_workspace = async_to_raw_response_wrapper(
            team_workspace.update_workspace,
        )
        self.delete_workspace = async_to_raw_response_wrapper(
            team_workspace.delete_workspace,
        )

        # Members
        self.invite_member = async_to_raw_response_wrapper(
            team_workspace.invite_member,
        )
        self.join_workspace = async_to_raw_response_wrapper(
            team_workspace.join_workspace,
        )
        self.leave_workspace = async_to_raw_response_wrapper(
            team_workspace.leave_workspace,
        )

        # OTP
        self.send_otp = async_to_raw_response_wrapper(
            team_workspace.send_otp,
        )
        self.verify_otp = async_to_raw_response_wrapper(
            team_workspace.verify_otp,
        )

        # Social
        self.add_social_id = async_to_raw_response_wrapper(
            team_workspace.add_social_id,
        )
        self.remove_social_id = async_to_raw_response_wrapper(
            team_workspace.remove_social_id,
        )

        # Admin
        self.statistics = async_to_raw_response_wrapper(
            team_workspace.statistics,
        )


# ====================================================================== #
# Streaming response wrappers
# ====================================================================== #


class TeamWorkspaceResourceWithStreamingResponse:
    def __init__(self, team_workspace: TeamWorkspaceResource) -> None:
        self._team_workspace = team_workspace

        # Accounts
        self.create_account = to_streamed_response_wrapper(
            team_workspace.create_account,
        )
        self.login = to_streamed_response_wrapper(
            team_workspace.login,
        )
        self.get_account = to_streamed_response_wrapper(
            team_workspace.get_account,
        )
        self.change_password = to_streamed_response_wrapper(
            team_workspace.change_password,
        )
        self.request_password_recovery = to_streamed_response_wrapper(
            team_workspace.request_password_recovery,
        )
        self.confirm_password_recovery = to_streamed_response_wrapper(
            team_workspace.confirm_password_recovery,
        )

        # Workspaces
        self.create_workspace = to_streamed_response_wrapper(
            team_workspace.create_workspace,
        )
        self.list_workspaces = to_streamed_response_wrapper(
            team_workspace.list_workspaces,
        )
        self.get_workspace = to_streamed_response_wrapper(
            team_workspace.get_workspace,
        )
        self.update_workspace = to_streamed_response_wrapper(
            team_workspace.update_workspace,
        )
        self.delete_workspace = to_streamed_response_wrapper(
            team_workspace.delete_workspace,
        )

        # Members
        self.invite_member = to_streamed_response_wrapper(
            team_workspace.invite_member,
        )
        self.join_workspace = to_streamed_response_wrapper(
            team_workspace.join_workspace,
        )
        self.leave_workspace = to_streamed_response_wrapper(
            team_workspace.leave_workspace,
        )

        # OTP
        self.send_otp = to_streamed_response_wrapper(
            team_workspace.send_otp,
        )
        self.verify_otp = to_streamed_response_wrapper(
            team_workspace.verify_otp,
        )

        # Social
        self.add_social_id = to_streamed_response_wrapper(
            team_workspace.add_social_id,
        )
        self.remove_social_id = to_streamed_response_wrapper(
            team_workspace.remove_social_id,
        )

        # Admin
        self.statistics = to_streamed_response_wrapper(
            team_workspace.statistics,
        )


class AsyncTeamWorkspaceResourceWithStreamingResponse:
    def __init__(self, team_workspace: AsyncTeamWorkspaceResource) -> None:
        self._team_workspace = team_workspace

        # Accounts
        self.create_account = async_to_streamed_response_wrapper(
            team_workspace.create_account,
        )
        self.login = async_to_streamed_response_wrapper(
            team_workspace.login,
        )
        self.get_account = async_to_streamed_response_wrapper(
            team_workspace.get_account,
        )
        self.change_password = async_to_streamed_response_wrapper(
            team_workspace.change_password,
        )
        self.request_password_recovery = async_to_streamed_response_wrapper(
            team_workspace.request_password_recovery,
        )
        self.confirm_password_recovery = async_to_streamed_response_wrapper(
            team_workspace.confirm_password_recovery,
        )

        # Workspaces
        self.create_workspace = async_to_streamed_response_wrapper(
            team_workspace.create_workspace,
        )
        self.list_workspaces = async_to_streamed_response_wrapper(
            team_workspace.list_workspaces,
        )
        self.get_workspace = async_to_streamed_response_wrapper(
            team_workspace.get_workspace,
        )
        self.update_workspace = async_to_streamed_response_wrapper(
            team_workspace.update_workspace,
        )
        self.delete_workspace = async_to_streamed_response_wrapper(
            team_workspace.delete_workspace,
        )

        # Members
        self.invite_member = async_to_streamed_response_wrapper(
            team_workspace.invite_member,
        )
        self.join_workspace = async_to_streamed_response_wrapper(
            team_workspace.join_workspace,
        )
        self.leave_workspace = async_to_streamed_response_wrapper(
            team_workspace.leave_workspace,
        )

        # OTP
        self.send_otp = async_to_streamed_response_wrapper(
            team_workspace.send_otp,
        )
        self.verify_otp = async_to_streamed_response_wrapper(
            team_workspace.verify_otp,
        )

        # Social
        self.add_social_id = async_to_streamed_response_wrapper(
            team_workspace.add_social_id,
        )
        self.remove_social_id = async_to_streamed_response_wrapper(
            team_workspace.remove_social_id,
        )

        # Admin
        self.statistics = async_to_streamed_response_wrapper(
            team_workspace.statistics,
        )
