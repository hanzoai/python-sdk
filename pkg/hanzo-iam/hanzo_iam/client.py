"""
Hanzo IAM Client - Sync OAuth2/OIDC client for Hanzo Identity.

Compatible with Casdoor API. Supports multiple organizations.
"""

from __future__ import annotations

import os
import secrets
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import jwt

from .models import (
    Application,
    IAMConfig,
    JWTClaims,
    Organization,
    TokenResponse,
    User,
    UserInfo,
)

if TYPE_CHECKING:
    from jwt import PyJWKClient


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
            env_config = self._config_from_env(org)
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

    @staticmethod
    def _config_from_env(org: Organization = Organization.HANZO) -> IAMConfig:
        """Read configuration from environment variables.

        Checks for HANZO_IAM_* vars first, then {ORG}_IAM_* vars.

        Environment variables:
            HANZO_IAM_URL / {ORG}_IAM_URL - IAM server URL
            HANZO_IAM_CLIENT_ID / {ORG}_IAM_CLIENT_ID - OAuth2 client ID
            HANZO_IAM_CLIENT_SECRET / {ORG}_IAM_CLIENT_SECRET - OAuth2 client secret
            HANZO_IAM_ORG / {ORG}_IAM_ORG - Organization name
            HANZO_IAM_APP / {ORG}_IAM_APP - Application name
            HANZO_IAM_CERT / {ORG}_IAM_CERT - JWT verification certificate
        """
        org_prefix = org.value.upper()

        def get_env(key: str, default: str = "") -> str:
            """Get env var with fallback chain: IAM_ -> HANZO_IAM_ -> {ORG}_IAM_."""
            return (os.getenv(f"IAM_{key}")
                    or os.getenv(f"HANZO_IAM_{key}")
                    or os.getenv(f"{org_prefix}_IAM_{key}", default))

        return IAMConfig(
            server_url=get_env("URL", org.iam_url),
            client_id=get_env("CLIENT_ID"),
            client_secret=get_env("CLIENT_SECRET"),
            organization=get_env("ORG", org.value),
            application=get_env("APP", "app"),
            certificate=get_env("CERT"),
        )

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
            response = self.http.get("/.well-known/openid-configuration")
            response.raise_for_status()
            self._openid_config = response.json()
        return self._openid_config

    def get_jwks(self) -> dict:
        """Get JSON Web Key Set for token verification.

        Returns:
            JWKS with public keys for JWT verification.
        """
        response = self.http.get("/.well-known/jwks")
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
        return f"{base_url}/login/oauth/authorize?{urlencode(params)}"

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
            "/api/login/oauth/access_token",
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
            "/api/login/oauth/refresh_token",
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
            "/api/login/oauth/access_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    # =========================================================================
    # Token Validation
    # =========================================================================

    def validate_token(
        self,
        token: str,
        verify_exp: bool = True,
        verify_aud: bool = True,
    ) -> JWTClaims:
        """Validate JWT token using JWKS.

        Args:
            token: JWT access token or ID token
            verify_exp: Verify expiration (default: True)
            verify_aud: Verify audience matches client_id (default: True)

        Returns:
            JWTClaims with decoded token claims.

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired.
        """
        # Initialize JWKS client if needed
        if self._jwks_client is None:
            jwks_url = f"{self._config.server_url.rstrip('/')}/.well-known/jwks"
            self._jwks_client = jwt.PyJWKClient(jwks_url)

        # Get signing key from JWKS
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)

        # Build verification options
        options = {
            "verify_exp": verify_exp,
            "verify_aud": verify_aud,
        }

        audience = self._config.client_id if verify_aud else None

        # Decode and validate
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            options=options,
        )

        return JWTClaims.model_validate(claims)

    def validate_token_with_cert(
        self,
        token: str,
        verify_exp: bool = True,
    ) -> JWTClaims:
        """Validate JWT token using configured certificate.

        Use this when you have the public certificate configured.

        Args:
            token: JWT access token or ID token
            verify_exp: Verify expiration (default: True)

        Returns:
            JWTClaims with decoded token claims.
        """
        if not self._config.certificate:
            raise ValueError("Certificate not configured. Use validate_token() with JWKS instead.")

        options = {"verify_exp": verify_exp}

        claims = jwt.decode(
            token,
            self._config.certificate,
            algorithms=["RS256"],
            options=options,
        )

        return JWTClaims.model_validate(claims)

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
            "/api/login/oauth/introspect",
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
            "/api/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return UserInfo.model_validate(response.json())

    # =========================================================================
    # Admin Auth Helpers
    # =========================================================================

    def _admin_params(self) -> dict:
        """Return query params for admin API auth (empty if using bearer token)."""
        if self._bearer_token:
            return {}
        return {
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
        }

    def _admin_headers(self) -> dict:
        """Return extra headers for admin API auth (Authorization if bearer token)."""
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    # =========================================================================
    # User Management (Casdoor Admin API)
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-user", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user"))

        return User.model_validate(data.get("data", data))

    def get_users(self) -> list[User]:
        """Get all users in organization.

        Returns:
            List of User objects.
        """
        params = {
            "owner": self._config.organization,
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-users", params=params, headers=self._admin_headers(),
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-application", params=params, headers=self._admin_headers(),
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
        """Modify user via Casdoor admin API."""
        response = self.http.post(
            f"/api/{action}",
            params=self._admin_params(),
            headers=self._admin_headers(),
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

    def get_organizations(self) -> list[dict]:
        """Get all organizations.

        Returns:
            List of organization dicts.
        """
        params = {
            "owner": "admin",
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-organizations", params=params, headers=self._admin_headers(),
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-organization", params=params, headers=self._admin_headers(),
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-providers", params=params, headers=self._admin_headers(),
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-roles", params=params, headers=self._admin_headers(),
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
            "/api/set-password",
            params=self._admin_params(),
            headers=self._admin_headers(),
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
            **self._admin_params(),
        }

        response = self.http.get(
            "/api/get-applications", params=params, headers=self._admin_headers(),
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
            "/api/update-application",
            params=self._admin_params(),
            headers=self._admin_headers(),
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

        response = self.http.post("/api/login", json=payload)
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
        self._jwks_client = None

    def __enter__(self) -> IAMClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()


class AsyncIAMClient:
    """
    Async OAuth2/OIDC client for Hanzo IAM.

    Same interface as IAMClient but uses async/await.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        org: Organization = Organization.HANZO,
        config: IAMConfig | None = None,
    ):
        """Initialize async IAM client."""
        if config:
            self._config = config
        else:
            env_config = IAMClient._config_from_env(org)
            self._config = IAMConfig(
                server_url=env_config.server_url,
                client_id=client_id or env_config.client_id,
                client_secret=client_secret or env_config.client_secret,
                organization=env_config.organization,
                application=env_config.application,
                certificate=env_config.certificate,
            )

        self._http: httpx.AsyncClient | None = None
        self._jwks_client: PyJWKClient | None = None
        self._openid_config: dict | None = None

    @property
    def config(self) -> IAMConfig:
        """Get client configuration."""
        return self._config

    async def _get_http(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self._config.server_url.rstrip("/"),
                timeout=30.0,
                headers={
                    "User-Agent": "hanzo-iam-python/1.0",
                    "Content-Type": "application/json",
                },
            )
        return self._http

    async def get_openid_configuration(self) -> dict:
        """Get OpenID Connect discovery document."""
        if self._openid_config is None:
            http = await self._get_http()
            response = await http.get("/.well-known/openid-configuration")
            response.raise_for_status()
            self._openid_config = response.json()
        return self._openid_config

    async def get_jwks(self) -> dict:
        """Get JSON Web Key Set."""
        http = await self._get_http()
        response = await http.get("/.well-known/jwks")
        response.raise_for_status()
        return response.json()

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
        """Build authorization URL."""
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
        return f"{base_url}/login/oauth/authorize?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/access_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token."""
        data = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": refresh_token,
        }

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/refresh_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    async def client_credentials(self, scope: str = "openid") -> TokenResponse:
        """Get access token using client credentials."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "scope": scope,
        }

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/access_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    def validate_token(
        self,
        token: str,
        verify_exp: bool = True,
        verify_aud: bool = True,
    ) -> JWTClaims:
        """Validate JWT token using JWKS (sync operation)."""
        if self._jwks_client is None:
            jwks_url = f"{self._config.server_url.rstrip('/')}/.well-known/jwks"
            self._jwks_client = jwt.PyJWKClient(jwks_url)

        signing_key = self._jwks_client.get_signing_key_from_jwt(token)

        options = {
            "verify_exp": verify_exp,
            "verify_aud": verify_aud,
        }

        audience = self._config.client_id if verify_aud else None

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            options=options,
        )

        return JWTClaims.model_validate(claims)

    async def introspect_token(self, token: str) -> dict:
        """Introspect token at IAM server."""
        data = {
            "token": token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/introspect",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()

    async def get_user_info(self, access_token: str) -> UserInfo:
        """Get user info from userinfo endpoint."""
        http = await self._get_http()
        response = await http.get(
            "/api/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return UserInfo.model_validate(response.json())

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        params = {
            "id": f"{self._config.organization}/{user_id}",
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
        }

        http = await self._get_http()
        response = await http.get("/api/get-user", params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user"))

        return User.model_validate(data.get("data", data))

    async def get_users(self) -> list[User]:
        """Get all users in organization."""
        params = {
            "owner": self._config.organization,
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
        }

        http = await self._get_http()
        response = await http.get("/api/get-users", params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get users"))

        users_data = data.get("data", data) or []
        return [User.model_validate(u) for u in users_data]

    async def get_application(self) -> Application:
        """Get current application configuration."""
        params = {
            "id": f"{self._config.organization}/{self._config.application}",
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
        }

        http = await self._get_http()
        response = await http.get("/api/get-application", params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get application"))

        return Application.model_validate(data.get("data", data))

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None
        self._jwks_client = None

    async def __aenter__(self) -> AsyncIAMClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


# Aliases for Casdoor SDK compatibility
CasdoorSDK = IAMClient
AsyncCasdoorSDK = AsyncIAMClient
