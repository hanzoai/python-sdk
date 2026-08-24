"""
Hanzo IAM Client - Sync OAuth2/OIDC client for Hanzo Identity.

Supports multiple organizations.
"""

from __future__ import annotations

import base64
import os
import secrets
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import jwt

from .config import IAMConfig
from . import routes
from .models import (
    OIDC_AUTHORIZE_PATH,
    OIDC_DISCOVERY_PATH,
    OIDC_INTROSPECT_PATH,
    OIDC_JWKS_PATH,
    OIDC_TOKEN_PATH,
    OIDC_USERINFO_PATH,
    Application,
    JWTClaims,
    Organization,
    TokenResponse,
    User,
    UserInfo,
)

if TYPE_CHECKING:
    from jwt import PyJWKClient


def basic(client_id: str, client_secret: str) -> str:
    """The confidential client's own credential, as HTTP Basic (RFC 6749 2.3.1).

    IAM reads a credential from Authorization and nowhere else.
    """
    pair = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return f"Basic {pair}"


class IAMClient:
    """
    Sync OAuth2/OIDC client for Hanzo IAM.

    Supports:
    - Authorization code flow
    - Client credentials flow (M2M)
    - Token validation via JWKS
    - Token introspection
    - User management

    Example:
        client = IAMClient(
            client_id="my-app",
            client_secret="secret",
            org=Organization.HANZO,
        )

        # Get authorization URL
        url = client.get_authorization_url(
            redirect_uri="https://myapp.com/callback",
            state="random-state",
        )

        # Exchange code for tokens
        tokens = client.exchange_code(code, redirect_uri)

        # Validate token
        claims = client.validate_token(tokens.access_token)
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        org: Organization = Organization.HANZO,
        config: IAMConfig | None = None,
        bearer_token: str | None = None,
    ):
        """Initialize IAM client.

        Args:
            client_id: OAuth2 client ID (or from env)
            client_secret: OAuth2 client secret (or from env)
            org: Organization enum (determines IAM URL)
            config: Full configuration (overrides other args)
            bearer_token: Bearer token for admin API auth (alternative to client_id/secret)
        """
        if config:
            self._config = config
        else:
            env_config = IAMConfig.from_env(org)
            self._config = IAMConfig(
                server_url=env_config.server_url,
                client_id=client_id or env_config.client_id,
                client_secret=client_secret or env_config.client_secret,
                organization=env_config.organization,
                application=env_config.application,
                certificate=env_config.certificate,
            )

        self._bearer_token = bearer_token
        self._http: httpx.Client | None = None
        self._jwks_client: PyJWKClient | None = None
        self._openid_config: dict | None = None


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
    # OIDC Discovery
    # =========================================================================

    def get_openid_configuration(self) -> dict:
        """Get OpenID Connect discovery document.

        Returns:
            OIDC configuration with endpoints, supported features, etc.
        """
        if self._openid_config is None:
            response = self.http.get(OIDC_DISCOVERY_PATH)
            response.raise_for_status()
            self._openid_config = routes.decode(response)
        return self._openid_config

    def get_jwks(self) -> dict:
        """Get JSON Web Key Set for token verification.

        Returns:
            JWKS with public keys for JWT verification.
        """
        response = self.http.get(OIDC_JWKS_PATH)
        response.raise_for_status()
        return routes.decode(response)

    # =========================================================================
    # Authorization Code Flow
    # =========================================================================

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: str = "openid profile email",
        response_type: str = "code",
        nonce: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        """Build authorization URL for OAuth2 code flow.

        Args:
            redirect_uri: Callback URL after authorization
            state: CSRF protection state (generated if not provided)
            scope: OAuth2 scopes (default: openid profile email)
            response_type: OAuth2 response type (default: code)
            nonce: OIDC nonce for ID token validation
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE method (S256 or plain)

        Returns:
            Authorization URL to redirect user to.
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state,
        }

        if nonce:
            params["nonce"] = nonce
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"

        base_url = self._config.server_url.rstrip("/")
        return f"{base_url}{OIDC_AUTHORIZE_PATH}?{urlencode(params)}"

    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect_uri used in authorization
            code_verifier: PKCE code verifier (if using PKCE)

        Returns:
            TokenResponse with access_token, refresh_token, id_token, etc.
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        response = self.http.post(
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous token response

        Returns:
            New TokenResponse with fresh tokens.
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": refresh_token,
        }

        response = self.http.post(
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

    # =========================================================================
    # Client Credentials Flow (M2M)
    # =========================================================================

    def client_credentials(self, scope: str = "openid") -> TokenResponse:
        """Get access token using client credentials (machine-to-machine).

        Args:
            scope: Requested scopes

        Returns:
            TokenResponse with access_token.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "scope": scope,
        }

        response = self.http.post(
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

    # =========================================================================
    # Token Validation
    # =========================================================================



    def introspect_token(self, token: str) -> dict:
        """Introspect token at IAM server.

        Use this for opaque tokens or when you need authoritative validation.

        Args:
            token: Token to introspect

        Returns:
            Token metadata including active status, scopes, etc.
        """
        data = {
            "token": token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }

        response = self.http.post(
            OIDC_INTROSPECT_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return routes.decode(response)

    # =========================================================================
    # User Info
    # =========================================================================

    def get_user_info(self, access_token: str) -> UserInfo:
        """Get user info from OIDC userinfo endpoint.

        Args:
            access_token: Valid access token

        Returns:
            UserInfo with user profile data.
        """
        response = self.http.get(
            OIDC_USERINFO_PATH,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return UserInfo.model_validate(routes.decode(response))

    # =========================================================================
    # Admin Auth Helpers
    # =========================================================================

    def _admin_headers(self) -> dict:
        """The credential, in Authorization — the only place IAM reads one.

        A bearer if we hold one, otherwise the confidential client's own pair as
        HTTP Basic (RFC 6749 2.3.1).
        """
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {"Authorization": basic(self._config.client_id, self._config.client_secret)}

    # =========================================================================
    # User Management (IAM Admin API)
    # =========================================================================

    def get_user(self, user_id: str) -> User:
        """Get one user, by `name` or by `owner/name`.

        Raises routes.IAMError with status 404 when the user is absent.
        """
        owner, name = routes.owner_name(user_id, self._config.organization)
        body = routes.check(
            self.http.get(routes.row(routes.USERS, owner, name), headers=self._admin_headers())
        )
        return User.model_validate(body)

    def get_users(self, owner: str | None = None) -> list[User]:
        """List users in `owner`, or in whatever scope the server picks without one."""
        params = {"owner": owner} if owner else {}
        body = routes.check(
            self.http.get(routes.USERS, params=params, headers=self._admin_headers())
        )
        return [User.model_validate(u) for u in routes.listing(body, "users")]

    def get_user_count(self, owner: str | None = None) -> int:
        """Number of users in scope, from the list route's own total."""
        params = {"owner": owner} if owner else {}
        params["limit"] = "1"
        body = routes.check(
            self.http.get(routes.USERS, params=params, headers=self._admin_headers())
        )
        return int(body["total"])

    def create_user(self, user: User, password: str = "") -> User:
        """Create a user. The server hashes the password; it never stores it as given."""
        body = routes.check(
            self.http.post(
                routes.USERS,
                headers=self._admin_headers(),
                json=self._user_body(user, password),
            )
        )
        return User.model_validate(body)

    def update_user(self, user: User, password: str = "") -> User:
        """Replace a user row. Omitted secrets and flags are carried over by the server."""
        body = routes.check(
            self.http.put(
                routes.row(routes.USERS, user.owner, user.name),
                headers=self._admin_headers(),
                json=self._user_body(user, password),
            )
        )
        return User.model_validate(body)

    def delete_user(self, user: User) -> bool:
        """Delete a user. True once the row is gone."""
        body = routes.check(
            self.http.delete(
                routes.row(routes.USERS, user.owner, user.name), headers=self._admin_headers()
            )
        )
        return bool(body.get("deleted"))

    @staticmethod
    def _user_body(user: User, password: str) -> dict:
        """The nested write body the users routes take."""
        body = {"user": user.model_dump(by_alias=True, exclude_none=True)}
        if password:
            body["password"] = password
        return body

    # =========================================================================
    # Organizations
    # =========================================================================

    def get_organizations(self, q: str = "", limit: int = 0) -> list[dict]:
        """List organizations visible to the caller."""
        params: dict[str, str] = {}
        if q:
            params["q"] = q
        if limit:
            params["limit"] = str(limit)
        body = routes.check(
            self.http.get(routes.ORGANIZATIONS, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "organizations")

    def get_organization(self, name: str) -> dict:
        """Get one organization. Organization rows are owned by `admin`."""
        return routes.check(
            self.http.get(
                routes.row(routes.ORGANIZATIONS, "admin", name), headers=self._admin_headers()
            )
        )

    # =========================================================================
    # Providers
    # =========================================================================

    def get_providers(self, owner: str | None = None) -> list[dict]:
        """List authentication providers."""
        params = {"owner": owner} if owner else {}
        body = routes.check(
            self.http.get(routes.PROVIDERS, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "providers")

    # =========================================================================
    # Roles
    # =========================================================================

    def get_roles(self, owner: str | None = None) -> list[dict]:
        """List roles."""
        params = {"owner": owner or self._config.organization}
        body = routes.check(
            self.http.get(routes.ROLES, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "roles")

    def get_role(self, name: str, *, owner: str | None = None) -> dict:
        """Get one role, members included."""
        org = owner or self._config.organization
        return routes.check(
            self.http.get(routes.row(routes.ROLES, org, name), headers=self._admin_headers())
        )

    def put_role(self, role: dict) -> dict:
        """Replace a role row."""
        return routes.check(
            self.http.put(
                routes.row(routes.ROLES, role["owner"], role["name"]),
                headers=self._admin_headers(),
                json=role,
            )
        )

    def get_user_roles(self, username: str, *, owner: str | None = None) -> list[dict]:
        """Roles the user belongs to.

        Membership is the role's own `users` list, so this reads the roles of the
        organization and keeps the ones naming this user.
        """
        org = owner or self._config.organization
        member = f"{org}/{username}"
        return [r for r in self.get_roles(org) if member in (r.get("users") or [])]

    def add_role_for_user(
        self, username: str, role_name: str, *, owner: str | None = None
    ) -> bool:
        """Add a user to a role. True if the role changed."""
        org = owner or self._config.organization
        member = f"{org}/{username}"
        role = self.get_role(role_name, owner=org)
        members = list(role.get("users") or [])
        if member in members:
            return False
        role["users"] = members + [member]
        self.put_role(role)
        return True

    def remove_role_from_user(
        self, username: str, role_name: str, *, owner: str | None = None
    ) -> bool:
        """Remove a user from a role. True if the role changed."""
        org = owner or self._config.organization
        member = f"{org}/{username}"
        role = self.get_role(role_name, owner=org)
        members = list(role.get("users") or [])
        if member not in members:
            return False
        role["users"] = [m for m in members if m != member]
        self.put_role(role)
        return True

    # =========================================================================
    # Password
    # =========================================================================

    def set_password(
        self,
        user_owner: str,
        user_name: str,
        new_password: str,
        old_password: str = "",
    ) -> dict:
        """Set a user's password. The server hashes it; nothing stores it in the clear."""
        body = routes.check(
            self.http.put(
                routes.PASSWORD,
                headers=self._admin_headers(),
                json={
                    "organization": user_owner,
                    "username": user_name,
                    "oldPassword": old_password,
                    "password": new_password,
                },
            )
        )
        return routes.envelope(body)

    # =========================================================================
    # Applications
    # =========================================================================

    def get_application(self) -> Application:
        """Get the application this client is configured for."""
        body = routes.check(
            self.http.get(
                routes.row(
                    routes.APPLICATIONS,
                    self._config.organization,
                    self._config.application,
                ),
                headers=self._admin_headers(),
            )
        )
        return Application.model_validate(body)

    def get_applications(self, owner: str | None = None) -> list[Application]:
        """List an organization's applications."""
        body = routes.check(
            self.http.get(
                routes.APPLICATIONS, params=({"owner": owner} if owner else {}), headers=self._admin_headers()
            )
        )
        return [Application.model_validate(a) for a in routes.listing(body, "applications")]

    def update_application(self, application: Application) -> Application:
        """Replace an application row. An omitted clientSecret keeps the stored one."""
        body = routes.check(
            self.http.put(
                routes.row(routes.APPLICATIONS, application.owner, application.name),
                headers=self._admin_headers(),
                json=application.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Application.model_validate(body)

    # =========================================================================
    # Login
    # =========================================================================

    def login(self, username: str, password: str) -> dict:
        """Sign in as a user and return what the sign-in answered."""
        body = routes.check(
            self.http.post(
                routes.LOGIN,
                json={
                    "type": "code",
                    "username": username,
                    "password": password,
                    "organization": self._config.organization,
                    "application": self._config.application,
                },
            )
        )
        return routes.envelope(body)

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._http:
            self._http.close()
            self._http = None
        self._jwks_client = None

    def __enter__(self) -> IAMClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()


