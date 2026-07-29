"""
Hanzo IAM admin client — the entity verbs, against the ISSUER.

SCOPE. This is the ADMIN surface only: the v1 verb aliases (`get-users`,
`get-organizations`, `update-application`, …) that IAM serves from
`internal/compat`. It does NOT speak OIDC. The protocol surface — authorize URL,
code redemption, refresh — belongs to `hanzo_iam.oauth`, and judging a token
belongs to `hanzo_iam.tokens.verify`. Each of those had a second implementation
here, under different credential rules: this client posted `client_secret` where
`oauth` proves possession with PKCE, so "what authenticates this exchange" had
two answers depending on which module a caller reached for. One owner each now.

HOST. It talks to the ISSUER directly (hanzo.id / zoo.id / lux.id), never
through an aggregator. Routing IAM through `api.hanzo.ai` would put a third
party inside a credential exchange, re-point the audience, and — because the
cloud IAM edge forwards under ONE shared confidential client — answer every
tenant with the edge credential's organization. See tests/test_no_aggregator.py.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from .config import IAMConfig
from .models import IAM_ROUTE_PREFIX, Application, User
from .response import unwrap


class IAMClient:
    """Sync admin client for Hanzo IAM.

    Example:
        with IAMClient(config=IAMConfig.from_env()) as client:
            users = client.get_users(owner="acme")
    """

    def __init__(self, config: IAMConfig, bearer_token: str | None = None):
        """Initialize IAM client.

        Args:
            config: Full configuration. Build it directly, or read the
                environment with ``IAMConfig.from_env()`` — that is the ONE
                env reader. This constructor used to accept `client_id`,
                `client_secret` and `org` as well and merge them over a
                second, private env reader with different defaults; three
                ways to say the same thing, disagreeing about the tenant.
            bearer_token: Bearer token for admin API auth. When present it is
                the credential; the client_id/secret pair is not sent.
        """
        self._config = config
        self._bearer_token = bearer_token
        self._http: httpx.Client | None = None

    @property
    def http(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http is None:
            self._http = httpx.Client(
                base_url=self._config.server_url.rstrip("/"),
                timeout=30.0,
                headers={
                    "User-Agent": "hanzo-iam-python/1.0",
                    "Content-Type": "application/json",
                },
            )
        return self._http

    @property
    def config(self) -> IAMConfig:
        """Get client configuration."""
        return self._config

    # =========================================================================
    # Credential
    # =========================================================================

    def _auth_headers(self) -> dict[str, str]:
        """Return the Authorization header for an admin API call.

        A bearer token, or the confidential-client pair as RFC 6749 2.3.1
        client_secret_basic. Never a query parameter: iam's Guard reads a
        credential from `Authorization` only (Basic resolves the application,
        Bearer resolves the user), and a secret in a URL is disclosed to every
        access log and proxy on the path. The previous form was both — it
        leaked the secret AND did not authenticate.
        """
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        pair = f"{self._config.client_id}:{self._config.client_secret}".encode()
        return {"Authorization": f"Basic {base64.b64encode(pair).decode()}"}

    def _get(self, verb: str, **params: str) -> Any:
        """GET one admin verb and return its value, or raise IAMError."""
        return unwrap(
            self.http.get(
                f"{IAM_ROUTE_PREFIX}/{verb}", params=params, headers=self._auth_headers()
            ),
            verb,
        )

    def _post(self, verb: str, payload: dict[str, Any]) -> Any:
        """POST one admin verb and return its value, or raise IAMError."""
        return unwrap(
            self.http.post(
                f"{IAM_ROUTE_PREFIX}/{verb}", headers=self._auth_headers(), json=payload
            ),
            verb,
        )

    # =========================================================================
    # Users
    # =========================================================================

    def get_user(self, user_id: str) -> User:
        """Get user by ID or username, within the configured organization."""
        return User.model_validate(
            self._get("get-user", id=f"{self._config.organization}/{user_id}")
        )

    def get_users(self, owner: str | None = None) -> list[User]:
        """Get all users in an organization.

        Args:
            owner: Organization to read (defaults to config.organization).
                Its neighbours here all took an owner; this one alone bound
                the config's org with no way to name a tenant, so the same
                surface answered "may I name a tenant?" two different ways.
                iam decides whether the caller may read that owner —
                a named owner is honoured or refused, never silently
                reinterpreted.
        """
        rows = self._get("get-users", owner=owner or self._config.organization) or []
        return [User.model_validate(u) for u in rows]

    def create_user(self, user: User) -> Any:
        """Create a new user."""
        return self._post("add-user", user.model_dump(by_alias=True, exclude_none=True))

    def update_user(self, user: User) -> Any:
        """Update an existing user."""
        return self._post(
            "update-user", user.model_dump(by_alias=True, exclude_none=True)
        )

    def delete_user(self, user: User) -> Any:
        """Delete a user."""
        return self._post(
            "delete-user", user.model_dump(by_alias=True, exclude_none=True)
        )

    def set_password(self, user_owner: str, user_name: str, new_password: str) -> Any:
        """Set a user's password.

        `old_password` is NOT a parameter. It used to be, and it was sent to a
        route that never verified it — accepting a value and ignoring it is
        worse than refusing it, because the caller believes a check happened.
        Self-service password change (which does need the old one) is the
        browser flow, not this admin verb.
        """
        return self._post(
            "set-password",
            {
                "userOwner": user_owner,
                "userName": user_name,
                "newPassword": new_password,
            },
        )

    # =========================================================================
    # Organizations
    # =========================================================================

    def get_organizations(self, owner: str = "admin") -> list[dict[str, Any]]:
        """Get all organizations.

        Args:
            owner: Owner of the organization rows (default: admin, the org
                that holds them). Named, not pinned — same as get_providers
                and get_applications.
        """
        return self._get("get-organizations", owner=owner) or []

    def get_organization(self, name: str) -> Any:
        """Get organization by name."""
        return self._get("get-organization", id=f"admin/{name}")

    # =========================================================================
    # Providers / Roles
    # =========================================================================

    def get_providers(self, owner: str = "admin") -> list[dict[str, Any]]:
        """Get all providers."""
        return self._get("get-providers", owner=owner) or []

    def get_roles(self, owner: str | None = None) -> list[dict[str, Any]]:
        """Get all roles in an organization (defaults to config.organization)."""
        return self._get("get-roles", owner=owner or self._config.organization) or []

    # =========================================================================
    # Applications
    # =========================================================================

    def get_application(self) -> Application:
        """Get the configured application."""
        return Application.model_validate(
            self._get(
                "get-application",
                id=f"{self._config.organization}/{self._config.application}",
            )
        )

    def get_applications(self, owner: str = "admin") -> list[Application]:
        """Get all applications."""
        rows = self._get("get-applications", owner=owner) or []
        return [Application.model_validate(a) for a in rows]

    def update_application(self, application: Application) -> Any:
        """Update an application."""
        return self._post(
            "update-application",
            application.model_dump(by_alias=True, exclude_none=True),
        )

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._http:
            self._http.close()
            self._http = None

    def __enter__(self) -> IAMClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
