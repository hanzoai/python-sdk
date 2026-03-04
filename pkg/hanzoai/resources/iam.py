# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List, Optional

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

__all__ = ["IAMResource", "AsyncIAMResource"]


class IAMResource(SyncAPIResource):
    """Hanzo IAM — identity, access, and organization management.

    Wraps the Casdoor-compatible API at hanzo.id/api/ behind the /iam/ gateway
    prefix.  Auth endpoints accept explicit params; CRUD endpoints for users,
    organizations, applications, roles, permissions, groups, tokens, sessions,
    and invitations accept full object dicts matching the Casdoor schema.
    """

    @cached_property
    def with_raw_response(self) -> IAMResourceWithRawResponse:
        return IAMResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IAMResourceWithStreamingResponse:
        return IAMResourceWithStreamingResponse(self)

    # ── Auth ────────────────────────────────────────────────────────────

    def signup(
        self,
        *,
        application: str,
        organization: str,
        username: str,
        password: str,
        name: str | NotGiven = NOT_GIVEN,
        email: str | NotGiven = NOT_GIVEN,
        phone: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign up a new user."""
        return self._post(
            "/iam/api/signup",
            body={
                "application": application,
                "organization": organization,
                "username": username,
                "password": password,
                "name": name,
                "email": email,
                "phone": phone,
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
        application: str,
        organization: str,
        username: str,
        password: str,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Log in and obtain a session token."""
        return self._post(
            "/iam/api/login",
            body={
                "application": application,
                "organization": organization,
                "username": username,
                "password": password,
                "type": type,
            },
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
        """Get the current authenticated account."""
        return self._get(
            "/iam/api/get-account",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_userinfo(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get OIDC userinfo for the current session."""
        return self._get(
            "/iam/api/userinfo",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def set_password(
        self,
        *,
        user_owner: str,
        user_name: str,
        old_password: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Set or change a user's password."""
        return self._post(
            "/iam/api/set-password",
            body={
                "userOwner": user_owner,
                "userName": user_name,
                "oldPassword": old_password,
                "newPassword": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def send_verification_code(
        self,
        *,
        dest: str,
        type: str,
        application_id: str | NotGiven = NOT_GIVEN,
        method: str | NotGiven = NOT_GIVEN,
        check_user: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send an email or SMS verification code."""
        return self._post(
            "/iam/api/send-verification-code",
            body={
                "dest": dest,
                "type": type,
                "applicationId": application_id,
                "method": method,
                "checkUser": check_user,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def verify_code(
        self,
        *,
        dest: str,
        type: str,
        code: str,
        application_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify an email or SMS code."""
        return self._post(
            "/iam/api/verify-code",
            body={
                "dest": dest,
                "type": type,
                "code": code,
                "applicationId": application_id,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Users ───────────────────────────────────────────────────────────

    def list_users(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all users in an organization."""
        return self._get(
            "/iam/api/get-users",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_user(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a user by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def get_user_count(
        self,
        *,
        owner: str,
        is_online: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get the count of users in an organization."""
        return self._get(
            "/iam/api/get-user-count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner, "isOnline": is_online},
            ),
            cast_to=object,
        )

    def add_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new user."""
        return self._post(
            "/iam/api/add-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing user."""
        return self._post(
            "/iam/api/update-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a user."""
        return self._post(
            "/iam/api/delete-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Organizations ───────────────────────────────────────────────────

    def list_organizations(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all organizations."""
        return self._get(
            "/iam/api/get-organizations",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_organization(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an organization by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-organization",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def add_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new organization."""
        return self._post(
            "/iam/api/add-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing organization."""
        return self._post(
            "/iam/api/update-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an organization."""
        return self._post(
            "/iam/api/delete-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Applications ────────────────────────────────────────────────────

    def list_applications(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all applications."""
        return self._get(
            "/iam/api/get-applications",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_application(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an application by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-application",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def add_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new application."""
        return self._post(
            "/iam/api/add-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing application."""
        return self._post(
            "/iam/api/update-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an application."""
        return self._post(
            "/iam/api/delete-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Roles ───────────────────────────────────────────────────────────

    def list_roles(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all roles."""
        return self._get(
            "/iam/api/get-roles",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_role(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a role by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-role",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def add_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new role."""
        return self._post(
            "/iam/api/add-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing role."""
        return self._post(
            "/iam/api/update-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a role."""
        return self._post(
            "/iam/api/delete-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Permissions ─────────────────────────────────────────────────────

    def list_permissions(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all permissions."""
        return self._get(
            "/iam/api/get-permissions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_permission(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a permission by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-permission",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def add_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new permission."""
        return self._post(
            "/iam/api/add-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing permission."""
        return self._post(
            "/iam/api/update-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a permission."""
        return self._post(
            "/iam/api/delete-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def enforce(
        self,
        *,
        permission_id: str,
        model_name: str,
        resource_id: str,
        action: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Check if a permission is allowed (Casbin enforce)."""
        return self._post(
            "/iam/api/enforce",
            body={
                "id": permission_id,
                "v0": model_name,
                "v1": resource_id,
                "v2": action,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def batch_enforce(
        self,
        *,
        permission_id: str,
        requests: List[List[str]],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Batch check multiple permission rules."""
        return self._post(
            "/iam/api/batch-enforce",
            body={
                "id": permission_id,
                "requests": requests,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Groups ──────────────────────────────────────────────────────────

    def list_groups(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all groups."""
        return self._get(
            "/iam/api/get-groups",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_group(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a group by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-group",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    def add_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new group."""
        return self._post(
            "/iam/api/add-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing group."""
        return self._post(
            "/iam/api/update-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a group."""
        return self._post(
            "/iam/api/delete-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Providers ───────────────────────────────────────────────────────

    def list_providers(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all identity providers."""
        return self._get(
            "/iam/api/get-providers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def get_provider(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an identity provider by id (format: ``owner/name``)."""
        return self._get(
            "/iam/api/get-provider",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    # ── Tokens ──────────────────────────────────────────────────────────

    def list_tokens(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all tokens."""
        return self._get(
            "/iam/api/get-tokens",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def add_token(
        self,
        *,
        token: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new token."""
        return self._post(
            "/iam/api/add-token",
            body=token,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_token(
        self,
        *,
        token: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a token."""
        return self._post(
            "/iam/api/delete-token",
            body=token,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Sessions ────────────────────────────────────────────────────────

    def list_sessions(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all sessions."""
        return self._get(
            "/iam/api/get-sessions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def delete_session(
        self,
        *,
        session: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a session."""
        return self._post(
            "/iam/api/delete-session",
            body=session,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Invitations ─────────────────────────────────────────────────────

    def list_invitations(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all invitations."""
        return self._get(
            "/iam/api/get-invitations",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    def add_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new invitation."""
        return self._post(
            "/iam/api/add-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def send_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send an invitation email."""
        return self._post(
            "/iam/api/send-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an invitation."""
        return self._post(
            "/iam/api/delete-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Records / Audit ─────────────────────────────────────────────────

    def list_records(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit records."""
        return self._get(
            "/iam/api/get-records",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    # ── System ──────────────────────────────────────────────────────────

    def get_system_info(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get IAM system information."""
        return self._get(
            "/iam/api/get-system-info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Health check."""
        return self._get(
            "/iam/api/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── MFA ─────────────────────────────────────────────────────────────

    def mfa_initiate(
        self,
        *,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Initiate MFA setup (returns secret/QR code)."""
        return self._post(
            "/iam/api/mfa/setup/initiate",
            body={"mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def mfa_verify(
        self,
        *,
        passcode: str,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify an MFA passcode during setup."""
        return self._post(
            "/iam/api/mfa/setup/verify",
            body={"passcode": passcode, "mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def mfa_enable(
        self,
        *,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enable MFA for the current user."""
        return self._post(
            "/iam/api/mfa/setup/enable",
            body={"mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_mfa(
        self,
        *,
        owner: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete MFA configuration for a user."""
        return self._post(
            "/iam/api/delete-mfa",
            body={"owner": owner, "name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ════════════════════════════════════════════════════════════════════════
#  Async resource
# ════════════════════════════════════════════════════════════════════════


class AsyncIAMResource(AsyncAPIResource):
    """Hanzo IAM — identity, access, and organization management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncIAMResourceWithRawResponse:
        return AsyncIAMResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIAMResourceWithStreamingResponse:
        return AsyncIAMResourceWithStreamingResponse(self)

    # ── Auth ────────────────────────────────────────────────────────────

    async def signup(
        self,
        *,
        application: str,
        organization: str,
        username: str,
        password: str,
        name: str | NotGiven = NOT_GIVEN,
        email: str | NotGiven = NOT_GIVEN,
        phone: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign up a new user."""
        return await self._post(
            "/iam/api/signup",
            body={
                "application": application,
                "organization": organization,
                "username": username,
                "password": password,
                "name": name,
                "email": email,
                "phone": phone,
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
        application: str,
        organization: str,
        username: str,
        password: str,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Log in and obtain a session token."""
        return await self._post(
            "/iam/api/login",
            body={
                "application": application,
                "organization": organization,
                "username": username,
                "password": password,
                "type": type,
            },
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
        """Get the current authenticated account."""
        return await self._get(
            "/iam/api/get-account",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_userinfo(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get OIDC userinfo for the current session."""
        return await self._get(
            "/iam/api/userinfo",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def set_password(
        self,
        *,
        user_owner: str,
        user_name: str,
        old_password: str,
        new_password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Set or change a user's password."""
        return await self._post(
            "/iam/api/set-password",
            body={
                "userOwner": user_owner,
                "userName": user_name,
                "oldPassword": old_password,
                "newPassword": new_password,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def send_verification_code(
        self,
        *,
        dest: str,
        type: str,
        application_id: str | NotGiven = NOT_GIVEN,
        method: str | NotGiven = NOT_GIVEN,
        check_user: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send an email or SMS verification code."""
        return await self._post(
            "/iam/api/send-verification-code",
            body={
                "dest": dest,
                "type": type,
                "applicationId": application_id,
                "method": method,
                "checkUser": check_user,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def verify_code(
        self,
        *,
        dest: str,
        type: str,
        code: str,
        application_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify an email or SMS code."""
        return await self._post(
            "/iam/api/verify-code",
            body={
                "dest": dest,
                "type": type,
                "code": code,
                "applicationId": application_id,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Users ───────────────────────────────────────────────────────────

    async def list_users(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all users in an organization."""
        return await self._get(
            "/iam/api/get-users",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_user(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a user by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def get_user_count(
        self,
        *,
        owner: str,
        is_online: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get the count of users in an organization."""
        return await self._get(
            "/iam/api/get-user-count",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner, "isOnline": is_online},
            ),
            cast_to=object,
        )

    async def add_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new user."""
        return await self._post(
            "/iam/api/add-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing user."""
        return await self._post(
            "/iam/api/update-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_user(
        self,
        *,
        user: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a user."""
        return await self._post(
            "/iam/api/delete-user",
            body=user,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Organizations ───────────────────────────────────────────────────

    async def list_organizations(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all organizations."""
        return await self._get(
            "/iam/api/get-organizations",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_organization(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an organization by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-organization",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def add_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new organization."""
        return await self._post(
            "/iam/api/add-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing organization."""
        return await self._post(
            "/iam/api/update-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_organization(
        self,
        *,
        organization: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an organization."""
        return await self._post(
            "/iam/api/delete-organization",
            body=organization,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Applications ────────────────────────────────────────────────────

    async def list_applications(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all applications."""
        return await self._get(
            "/iam/api/get-applications",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_application(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an application by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-application",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def add_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new application."""
        return await self._post(
            "/iam/api/add-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing application."""
        return await self._post(
            "/iam/api/update-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_application(
        self,
        *,
        application: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an application."""
        return await self._post(
            "/iam/api/delete-application",
            body=application,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Roles ───────────────────────────────────────────────────────────

    async def list_roles(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all roles."""
        return await self._get(
            "/iam/api/get-roles",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_role(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a role by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-role",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def add_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new role."""
        return await self._post(
            "/iam/api/add-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing role."""
        return await self._post(
            "/iam/api/update-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_role(
        self,
        *,
        role: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a role."""
        return await self._post(
            "/iam/api/delete-role",
            body=role,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Permissions ─────────────────────────────────────────────────────

    async def list_permissions(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all permissions."""
        return await self._get(
            "/iam/api/get-permissions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_permission(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a permission by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-permission",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def add_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new permission."""
        return await self._post(
            "/iam/api/add-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing permission."""
        return await self._post(
            "/iam/api/update-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_permission(
        self,
        *,
        permission: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a permission."""
        return await self._post(
            "/iam/api/delete-permission",
            body=permission,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def enforce(
        self,
        *,
        permission_id: str,
        model_name: str,
        resource_id: str,
        action: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Check if a permission is allowed (Casbin enforce)."""
        return await self._post(
            "/iam/api/enforce",
            body={
                "id": permission_id,
                "v0": model_name,
                "v1": resource_id,
                "v2": action,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def batch_enforce(
        self,
        *,
        permission_id: str,
        requests: List[List[str]],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Batch check multiple permission rules."""
        return await self._post(
            "/iam/api/batch-enforce",
            body={
                "id": permission_id,
                "requests": requests,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Groups ──────────────────────────────────────────────────────────

    async def list_groups(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all groups."""
        return await self._get(
            "/iam/api/get-groups",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_group(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a group by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-group",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    async def add_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new group."""
        return await self._post(
            "/iam/api/add-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an existing group."""
        return await self._post(
            "/iam/api/update-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_group(
        self,
        *,
        group: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a group."""
        return await self._post(
            "/iam/api/delete-group",
            body=group,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Providers ───────────────────────────────────────────────────────

    async def list_providers(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all identity providers."""
        return await self._get(
            "/iam/api/get-providers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def get_provider(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an identity provider by id (format: ``owner/name``)."""
        return await self._get(
            "/iam/api/get-provider",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"id": id},
            ),
            cast_to=object,
        )

    # ── Tokens ──────────────────────────────────────────────────────────

    async def list_tokens(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all tokens."""
        return await self._get(
            "/iam/api/get-tokens",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def add_token(
        self,
        *,
        token: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new token."""
        return await self._post(
            "/iam/api/add-token",
            body=token,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_token(
        self,
        *,
        token: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a token."""
        return await self._post(
            "/iam/api/delete-token",
            body=token,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Sessions ────────────────────────────────────────────────────────

    async def list_sessions(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all sessions."""
        return await self._get(
            "/iam/api/get-sessions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def delete_session(
        self,
        *,
        session: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a session."""
        return await self._post(
            "/iam/api/delete-session",
            body=session,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Invitations ─────────────────────────────────────────────────────

    async def list_invitations(
        self,
        *,
        owner: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all invitations."""
        return await self._get(
            "/iam/api/get-invitations",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    async def add_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a new invitation."""
        return await self._post(
            "/iam/api/add-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def send_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Send an invitation email."""
        return await self._post(
            "/iam/api/send-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_invitation(
        self,
        *,
        invitation: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an invitation."""
        return await self._post(
            "/iam/api/delete-invitation",
            body=invitation,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Records / Audit ─────────────────────────────────────────────────

    async def list_records(
        self,
        *,
        owner: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit records."""
        return await self._get(
            "/iam/api/get-records",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"owner": owner},
            ),
            cast_to=object,
        )

    # ── System ──────────────────────────────────────────────────────────

    async def get_system_info(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get IAM system information."""
        return await self._get(
            "/iam/api/get-system-info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Health check."""
        return await self._get(
            "/iam/api/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── MFA ─────────────────────────────────────────────────────────────

    async def mfa_initiate(
        self,
        *,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Initiate MFA setup (returns secret/QR code)."""
        return await self._post(
            "/iam/api/mfa/setup/initiate",
            body={"mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def mfa_verify(
        self,
        *,
        passcode: str,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify an MFA passcode during setup."""
        return await self._post(
            "/iam/api/mfa/setup/verify",
            body={"passcode": passcode, "mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def mfa_enable(
        self,
        *,
        mfa_type: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enable MFA for the current user."""
        return await self._post(
            "/iam/api/mfa/setup/enable",
            body={"mfaType": mfa_type},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_mfa(
        self,
        *,
        owner: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete MFA configuration for a user."""
        return await self._post(
            "/iam/api/delete-mfa",
            body={"owner": owner, "name": name},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ════════════════════════════════════════════════════════════════════════
#  Raw / Streaming response wrappers
# ════════════════════════════════════════════════════════════════════════

# All 49 methods wrapped for each of the four wrapper classes.

_SYNC_METHODS = [
    "signup", "login", "get_account", "get_userinfo", "set_password",
    "send_verification_code", "verify_code",
    "list_users", "get_user", "get_user_count", "add_user", "update_user",
    "delete_user",
    "list_organizations", "get_organization", "add_organization",
    "update_organization", "delete_organization",
    "list_applications", "get_application", "add_application",
    "update_application", "delete_application",
    "list_roles", "get_role", "add_role", "update_role", "delete_role",
    "list_permissions", "get_permission", "add_permission",
    "update_permission", "delete_permission", "enforce", "batch_enforce",
    "list_groups", "get_group", "add_group", "update_group", "delete_group",
    "list_providers", "get_provider",
    "list_tokens", "add_token", "delete_token",
    "list_sessions", "delete_session",
    "list_invitations", "add_invitation", "send_invitation",
    "delete_invitation",
    "list_records",
    "get_system_info", "health",
    "mfa_initiate", "mfa_verify", "mfa_enable", "delete_mfa",
]


class IAMResourceWithRawResponse:
    def __init__(self, iam: IAMResource) -> None:
        self._iam = iam
        for name in _SYNC_METHODS:
            setattr(self, name, to_raw_response_wrapper(getattr(iam, name)))


class AsyncIAMResourceWithRawResponse:
    def __init__(self, iam: AsyncIAMResource) -> None:
        self._iam = iam
        for name in _SYNC_METHODS:
            setattr(self, name, async_to_raw_response_wrapper(getattr(iam, name)))


class IAMResourceWithStreamingResponse:
    def __init__(self, iam: IAMResource) -> None:
        self._iam = iam
        for name in _SYNC_METHODS:
            setattr(self, name, to_streamed_response_wrapper(getattr(iam, name)))


class AsyncIAMResourceWithStreamingResponse:
    def __init__(self, iam: AsyncIAMResource) -> None:
        self._iam = iam
        for name in _SYNC_METHODS:
            setattr(self, name, async_to_streamed_response_wrapper(getattr(iam, name)))
