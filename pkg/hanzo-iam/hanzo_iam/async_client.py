"""Asynchronous IAM client for Hanzo IAM (Casdoor-based)."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx
import jwt

from hanzo_iam.models import (
    Application,
    JWTClaims,
    Organization,
    TokenResponse,
    User,
    UserInfo,
)

if TYPE_CHECKING:
    from jwt import PyJWKClient

    from hanzo_iam.config import IAMConfig


class AsyncIAMClient:
    """Asynchronous OAuth2/OIDC client for Hanzo IAM.

    Same interface as IAMClient but all I/O methods are async.

    Supports:
    - Authorization code flow
    - Client credentials flow (M2M)
    - Token validation via JWKS
    - Token introspection
    - User management

    Example:
        async with AsyncIAMClient(
            client_id="my-app",
            client_secret="secret",
            org=Organization.HANZO,
        ) as client:
            # Get tokens
            tokens = await client.exchange_code(code, redirect_uri)

            # Get user info
            user = await client.get_user_info(tokens.access_token)
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        org: Organization = Organization.HANZO,
        config: IAMConfig | None = None,
        bearer_token: str | None = None,
    ):
        """Initialize async IAM client.

        Args:
            client_id: OAuth2 client ID (or from env)
            client_secret: OAuth2 client secret (or from env)
            org: Organization enum (determines IAM URL)
            config: Full configuration (overrides other args)
            bearer_token: Bearer token for admin API auth (alternative to client_id/secret)
        """
        # Avoid circular import
        from hanzo_iam.client import IAMClient
        from hanzo_iam.models import IAMConfig as ModelConfig

        if config:
            self._config = config
        else:
            env_config = IAMClient._config_from_env(org)
            self._config = ModelConfig(
                server_url=env_config.server_url,
                client_id=client_id or env_config.client_id,
                client_secret=client_secret or env_config.client_secret,
                organization=env_config.organization,
                application=env_config.application,
                certificate=env_config.certificate,
            )

        self._bearer_token = bearer_token
        self._http: httpx.AsyncClient | None = None
        self._jwks_client: PyJWKClient | None = None
        self._openid_config: dict[str, Any] | None = None

    @property
    def config(self) -> IAMConfig:
        """Get client configuration."""
        return self._config  # type: ignore[return-value]

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

    # =========================================================================
    # Admin Auth Helpers
    # =========================================================================

    def _admin_params(self) -> dict[str, str]:
        """Return query params for admin API auth (empty if using bearer token)."""
        if self._bearer_token:
            return {}
        return {
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
        }

    def _admin_headers(self) -> dict[str, str]:
        """Return extra headers for admin API auth (Authorization if bearer token)."""
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    # =========================================================================
    # OIDC Discovery
    # =========================================================================

    async def get_openid_configuration(self) -> dict[str, Any]:
        """Get OpenID Connect discovery document.

        Returns:
            OIDC configuration with endpoints, supported features, etc.
        """
        if self._openid_config is None:
            http = await self._get_http()
            response = await http.get("/.well-known/openid-configuration")
            response.raise_for_status()
            self._openid_config = response.json()
        return self._openid_config

    async def get_jwks(self) -> dict[str, Any]:
        """Get JSON Web Key Set for token verification.

        Returns:
            JWKS with public keys for JWT verification.
        """
        http = await self._get_http()
        response = await http.get("/.well-known/jwks")
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

        This method is synchronous since it only builds a URL.

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

    async def exchange_code(
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

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/access_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
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

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/refresh_token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    # =========================================================================
    # Client Credentials Flow (M2M)
    # =========================================================================

    async def client_credentials(self, scope: str = "openid") -> TokenResponse:
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

        http = await self._get_http()
        response = await http.post(
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

        Note: JWT validation is CPU-bound, so this remains synchronous.
        The JWKS client handles caching internally.

        Args:
            token: JWT access token or ID token
            verify_exp: Verify expiration (default: True)
            verify_aud: Verify audience matches client_id (default: True)

        Returns:
            JWTClaims with decoded token claims.

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired.
        """
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
            raise ValueError(
                "Certificate not configured. Use validate_token() with JWKS instead."
            )

        options = {"verify_exp": verify_exp}

        claims = jwt.decode(
            token,
            self._config.certificate,
            algorithms=["RS256"],
            options=options,
        )

        return JWTClaims.model_validate(claims)

    async def introspect_token(self, token: str) -> dict[str, Any]:
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

        http = await self._get_http()
        response = await http.post(
            "/api/login/oauth/introspect",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # User Info
    # =========================================================================

    async def get_user_info(self, access_token: str) -> UserInfo:
        """Get user info from OIDC userinfo endpoint.

        Args:
            access_token: Valid access token

        Returns:
            UserInfo with user profile data.
        """
        http = await self._get_http()
        response = await http.get(
            "/api/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return UserInfo.model_validate(response.json())

    # =========================================================================
    # User Management (Casdoor Admin API)
    # =========================================================================

    async def get_user(self, user_id: str) -> User:
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

        http = await self._get_http()
        response = await http.get(
            "/api/get-user", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user"))

        return User.model_validate(data.get("data", data))

    async def get_users(self) -> list[User]:
        """Get all users in organization.

        Returns:
            List of User objects.
        """
        params = {
            "owner": self._config.organization,
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-users", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get users"))

        users_data = data.get("data", data) or []
        return [User.model_validate(u) for u in users_data]

    async def get_user_count(
        self,
        *,
        owner: str | None = None,
        is_online: bool | None = None,
    ) -> int:
        """Get user count in organization.

        Args:
            owner: Organization name (defaults to config.organization)
            is_online: Filter by online status

        Returns:
            Number of users.
        """
        params: dict[str, Any] = {
            "owner": owner or self._config.organization,
            **self._admin_params(),
        }
        if is_online is not None:
            params["isOnline"] = str(is_online).lower()

        http = await self._get_http()
        response = await http.get(
            "/api/get-user-count", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user count"))

        return int(data.get("data", data) if isinstance(data, dict) else data)

    async def create_user(self, user: User) -> User:
        """Create new user.

        Args:
            user: User object to create

        Returns:
            Created User object.
        """
        return await self._modify_user("add-user", user)

    async def update_user(self, user: User) -> User:
        """Update existing user.

        Args:
            user: User object with updated fields

        Returns:
            Updated User object.
        """
        return await self._modify_user("update-user", user)

    async def delete_user(self, user: User) -> User:
        """Delete user.

        Args:
            user: User object to delete

        Returns:
            Deleted User object.
        """
        return await self._modify_user("delete-user", user)

    async def _modify_user(self, action: str, user: User) -> User:
        """Modify user via API."""
        http = await self._get_http()
        response = await http.post(
            f"/api/{action}",
            params=self._admin_params(),
            headers=self._admin_headers(),
            json=user.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", f"Failed to {action}"))

        return User.model_validate(data.get("data", data))

    async def get_application(self) -> Application:
        """Get current application configuration.

        Returns:
            Application configuration including OAuth2 settings.
        """
        params = {
            "id": f"{self._config.organization}/{self._config.application}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-application", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get application"))

        return Application.model_validate(data.get("data", data))

    # =========================================================================
    # Organization
    # =========================================================================

    async def get_organizations(self) -> list[dict[str, Any]]:
        """Get all organizations.

        Returns:
            List of organization data.
        """
        params = {
            "owner": "admin",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-organizations", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get organizations"))

        return data.get("data", data) or []

    async def get_organization(self, name: str) -> dict[str, Any]:
        """Get organization by name.

        Args:
            name: Organization name

        Returns:
            Organization data.
        """
        params = {
            "id": f"admin/{name}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-organization", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get organization"))

        return data.get("data", data)

    # =========================================================================
    # Permissions / Enforcement
    # =========================================================================

    async def enforce(
        self,
        permission_id: str,
        model_id: str,
        resource_id: str,
        enforce_id: str,
        *,
        owner: str | None = None,
        request: list[str] | None = None,
    ) -> bool:
        """Check permission using Casbin.

        Args:
            permission_id: Permission identifier
            model_id: Casbin model identifier
            resource_id: Resource identifier
            enforce_id: Enforcement identifier
            owner: Organization (defaults to config.organization)
            request: Casbin request parameters [sub, obj, act, ...]

        Returns:
            True if permitted, False otherwise.
        """
        payload: dict[str, Any] = {
            "id": permission_id,
            "modelId": model_id,
            "resourceId": resource_id,
            "enforceId": enforce_id,
            "owner": owner or self._config.organization,
            **self._admin_params(),
        }
        if request:
            payload["casbinRequest"] = request

        http = await self._get_http()
        response = await http.post(
            "/api/enforce", json=payload, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("status") == "error":
            raise ValueError(data.get("msg", "Enforcement failed"))

        return bool(data.get("data", data) if isinstance(data, dict) else data)

    async def batch_enforce(
        self,
        permission_id: str,
        model_id: str,
        enforce_id: str,
        *,
        owner: str | None = None,
        requests: list[list[str]] | None = None,
    ) -> list[bool]:
        """Batch check permissions using Casbin.

        Args:
            permission_id: Permission identifier
            model_id: Casbin model identifier
            enforce_id: Enforcement identifier
            owner: Organization (defaults to config.organization)
            requests: List of Casbin requests [[sub, obj, act], ...]

        Returns:
            List of permission results.
        """
        payload: dict[str, Any] = {
            "id": permission_id,
            "modelId": model_id,
            "enforceId": enforce_id,
            "owner": owner or self._config.organization,
            **self._admin_params(),
        }
        if requests:
            payload["casbinRequest"] = requests

        http = await self._get_http()
        response = await http.post(
            "/api/batch-enforce", json=payload, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("status") == "error":
            raise ValueError(data.get("msg", "Batch enforcement failed"))

        results = data.get("data", data) if isinstance(data, dict) else data
        return [bool(r) for r in results]

    # =========================================================================
    # Roles
    # =========================================================================

    async def get_roles(self, *, owner: str | None = None) -> list[dict[str, Any]]:
        """Get all roles in organization.

        Args:
            owner: Organization name (defaults to config.organization)

        Returns:
            List of role data.
        """
        params = {
            "owner": owner or self._config.organization,
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-roles", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get roles"))

        return data.get("data", data) or []

    async def get_role(
        self,
        role_name: str,
        *,
        owner: str | None = None,
    ) -> dict[str, Any]:
        """Get role by name.

        Args:
            role_name: Role name
            owner: Organization name (defaults to config.organization)

        Returns:
            Role data.
        """
        org = owner or self._config.organization
        params = {
            "id": f"{org}/{role_name}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-role", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get role"))

        return data.get("data", data)

    async def get_user_roles(
        self,
        username: str,
        *,
        owner: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get roles for user.

        Args:
            username: Username
            owner: Organization name (defaults to config.organization)

        Returns:
            List of role data.
        """
        org = owner or self._config.organization
        params = {
            "id": f"{org}/{username}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.get(
            "/api/get-user-roles", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get user roles"))

        return data.get("data", data) or []

    async def add_role_for_user(
        self,
        username: str,
        role_name: str,
        *,
        owner: str | None = None,
    ) -> bool:
        """Add role to user.

        Args:
            username: Username
            role_name: Role name to add
            owner: Organization name (defaults to config.organization)

        Returns:
            True if successful.
        """
        org = owner or self._config.organization
        payload = {
            "user": f"{org}/{username}",
            "role": f"{org}/{role_name}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.post(
            "/api/add-user-role", json=payload, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to add role for user"))

        return True

    async def remove_role_from_user(
        self,
        username: str,
        role_name: str,
        *,
        owner: str | None = None,
    ) -> bool:
        """Remove role from user.

        Args:
            username: Username
            role_name: Role name to remove
            owner: Organization name (defaults to config.organization)

        Returns:
            True if successful.
        """
        org = owner or self._config.organization
        payload = {
            "user": f"{org}/{username}",
            "role": f"{org}/{role_name}",
            **self._admin_params(),
        }

        http = await self._get_http()
        response = await http.post(
            "/api/delete-user-role", json=payload, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to remove role from user"))

        return True

    # =========================================================================
    # Password Management
    # =========================================================================

    async def set_password(
        self,
        user_owner: str,
        user_name: str,
        new_password: str,
        old_password: str = "",
    ) -> dict[str, Any]:
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

        http = await self._get_http()
        response = await http.post(
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

    async def get_applications(self, owner: str = "admin") -> list[Application]:
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

        http = await self._get_http()
        response = await http.get(
            "/api/get-applications", params=params, headers=self._admin_headers(),
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise ValueError(data.get("msg", "Failed to get applications"))

        apps_data = data.get("data", data) or []
        return [Application.model_validate(a) for a in apps_data]

    async def update_application(self, application: Application) -> dict[str, Any]:
        """Update an application.

        Args:
            application: Application object with updated fields.

        Returns:
            API response data.
        """
        http = await self._get_http()
        response = await http.post(
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
    # Lifecycle
    # =========================================================================

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._http:
            await self._http.aclose()
            self._http = None
        self._jwks_client = None

    async def __aenter__(self) -> AsyncIAMClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# Alias for Casdoor SDK compatibility
AsyncCasdoorSDK = AsyncIAMClient
