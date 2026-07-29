"""
Hanzo IAM Client - the sync OAuth2/OIDC + admin client for Hanzo Identity.

This is the ONE IAM HTTP client in this package. It talks to the ISSUER
directly (hanzo.id / zoo.id / lux.id) — token exchange and JWKS must not be
proxied through an aggregator, because that puts a third party inside a
credential exchange and re-points the audience.

Judging a token is NOT here: hanzo_iam.tokens.verify is the one verifier.
"""

from __future__ import annotations

import base64
import secrets
from urllib.parse import urlencode

import httpx

from .config import IAMConfig
from .models import (
    IAM_ROUTE_PREFIX,
    OIDC_AUTHORIZE_PATH,
    OIDC_DISCOVERY_PATH,
    OIDC_INTROSPECT_PATH,
    OIDC_JWKS_PATH,
    OIDC_TOKEN_PATH,
    OIDC_USERINFO_PATH,
    Application,
    TokenResponse,
    User,
    UserInfo,
)


class IAMClient:
    """
    Sync OAuth2/OIDC client for Hanzo IAM.

    Supports:
    - Authorization code flow
    - Client credentials flow (M2M)
    - Token introspection
    - User management

    Example:
        client = IAMClient(config=IAMConfig.from_env())

        # Get authorization URL
        url = client.get_authorization_url(
            redirect_uri="https://myapp.com/callback",
            state="random-state",
        )

        # Exchange code for tokens
        tokens = client.exchange_code(code, redirect_uri)

        # Judge the token — hanzo_iam.tokens.verify, not the client
        result = verify(tokens.access_token, jwks_uri=..., issuer=...)
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
            self._openid_config = response.json()
        return self._openid_config

    def get_jwks(self) -> dict:
        """Get JSON Web Key Set for token verification.

        Returns:
            JWKS with public keys for JWT verification.
        """
        response = self.http.get(OIDC_JWKS_PATH)
        response.raise_for_status()
        return response.json()

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
        return TokenResponse.model_validate(response.json())

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
        return TokenResponse.model_validate(response.json())

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
        return TokenResponse.model_validate(response.json())

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
        return response.json()

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
        return UserInfo.model_validate(response.json())

    # =========================================================================
    # Admin Auth Helpers
    # =========================================================================

    def _auth_headers(self) -> dict:
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

    # =========================================================================
    # User Management (IAM Admin API)
    # =========================================================================

    def get_user(self, user_id: str) -> User:
        """Get user by ID.

        Args:
            user_id: User ID or username

        Returns:
            User object with full profile.
        """
        params = {
            "id": f"{self._config.organization}/{user_id}",
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-user",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user"))

        return User.model_validate(data.get("data", data))

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

        Returns:
            List of User objects.
        """
        params = {
            "owner": owner or self._config.organization,
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-users",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get users"))

        users_data = data.get("data", data) or []
        return [User.model_validate(u) for u in users_data]

    def get_application(self) -> Application:
        """Get current application configuration.

        Returns:
            Application configuration including OAuth2 settings.
        """
        params = {
            "id": f"{self._config.organization}/{self._config.application}",
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-application",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get application"))

        return Application.model_validate(data.get("data", data))

    # =========================================================================
    # User Management (Admin API)
    # =========================================================================

    def create_user(self, user: User) -> dict:
        """Create a new user.

        Args:
            user: User object to create.

        Returns:
            API response data.
        """
        return self._modify_user("add-user", user)

    def update_user(self, user: User) -> dict:
        """Update an existing user.

        Args:
            user: User object with updated fields.

        Returns:
            API response data.
        """
        return self._modify_user("update-user", user)

    def delete_user(self, user: User) -> dict:
        """Delete a user.

        Args:
            user: User object to delete.

        Returns:
            API response data.
        """
        return self._modify_user("delete-user", user)

    def _modify_user(self, action: str, user: User) -> dict:
        """Modify user via IAM admin API."""
        response = self.http.post(
            f"{IAM_ROUTE_PREFIX}/{action}",
            headers=self._auth_headers(),
            json=user.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", f"Failed to {action}"))

        return data

    # =========================================================================
    # Organization Management
    # =========================================================================

    def get_organizations(self, owner: str = "admin") -> list[dict]:
        """Get all organizations.

        Args:
            owner: Owner of the organization rows (default: admin, the org
                that holds them). Named, not pinned — same as get_providers
                and get_applications.

        Returns:
            List of organization dicts.
        """
        params = {
            "owner": owner,
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-organizations",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get organizations"))

        return data.get("data", data) or []

    def get_organization(self, name: str) -> dict:
        """Get organization by name.

        Args:
            name: Organization name.

        Returns:
            Organization data dict.
        """
        params = {
            "id": f"admin/{name}",
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-organization",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get organization"))

        return data.get("data", data)

    # =========================================================================
    # Provider Management
    # =========================================================================

    def get_providers(self, owner: str = "admin") -> list[dict]:
        """Get all providers.

        Args:
            owner: Owner of providers (default: admin).

        Returns:
            List of provider dicts.
        """
        params = {
            "owner": owner,
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-providers",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get providers"))

        return data.get("data", data) or []

    # =========================================================================
    # Role Management
    # =========================================================================

    def get_roles(self, owner: str | None = None) -> list[dict]:
        """Get all roles in organization.

        Args:
            owner: Organization name (defaults to config.organization).

        Returns:
            List of role dicts.
        """
        params = {
            "owner": owner or self._config.organization,
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-roles",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get roles"))

        return data.get("data", data) or []

    # =========================================================================
    # Password Management
    # =========================================================================

    def set_password(
        self,
        user_owner: str,
        user_name: str,
        new_password: str,
        old_password: str = "",
    ) -> dict:
        """Set or reset a user's password.

        Args:
            user_owner: Organization that owns the user.
            user_name: Username.
            new_password: New password to set.
            old_password: Current password (empty for admin reset).

        Returns:
            API response data.
        """
        payload = {
            "userOwner": user_owner,
            "userName": user_name,
            "oldPassword": old_password,
            "newPassword": new_password,
        }

        response = self.http.post(
            f"{IAM_ROUTE_PREFIX}/set-password",
            headers=self._auth_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to set password"))

        return data

    # =========================================================================
    # Application Management
    # =========================================================================

    def get_applications(self, owner: str = "admin") -> list[Application]:
        """Get all applications.

        Args:
            owner: Owner of applications (default: admin).

        Returns:
            List of Application objects.
        """
        params = {
            "owner": owner,
        }

        response = self.http.get(
            f"{IAM_ROUTE_PREFIX}/get-applications",
            params=params,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get applications"))

        apps_data = data.get("data", data) or []
        return [Application.model_validate(a) for a in apps_data]

    def update_application(self, application: Application) -> dict:
        """Update an application.

        Args:
            application: Application object with updated fields.

        Returns:
            API response data.
        """
        response = self.http.post(
            f"{IAM_ROUTE_PREFIX}/update-application",
            headers=self._auth_headers(),
            json=application.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to update application"))

        return data

    # =========================================================================
    # Login (Masquerade)
    # =========================================================================

    def login(self, username: str, password: str) -> dict:
        """Login as a user (email/password).

        Args:
            username: Email or username.
            password: User password.

        Returns:
            Login response with access code or token.
        """
        payload = {
            "type": "code",
            "username": username,
            "password": password,
            "organization": self._config.organization,
            "application": self._config.application,
        }

        response = self.http.post(f"{IAM_ROUTE_PREFIX}/login", json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            raise ValueError(data.get("msg", "Login failed"))

        return data

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

    def __exit__(self, *args) -> None:
        self.close()
