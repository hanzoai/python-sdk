"""Asynchronous IAM client for Hanzo IAM."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx
import jwt

from hanzo_iam.client import basic
from hanzo_iam.config import IAMConfig
from hanzo_iam import routes
from hanzo_iam.models import (
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
        self._http: httpx.AsyncClient | None = None
        self._jwks_client: PyJWKClient | None = None
        self._openid_config: dict[str, Any] | None = None

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

    # =========================================================================
    # Admin Auth Helpers
    # =========================================================================

    def _admin_headers(self) -> dict[str, str]:
        """The credential, in Authorization — the only place IAM reads one.

        A bearer if we hold one, otherwise the confidential client's own pair as
        HTTP Basic (RFC 6749 2.3.1).
        """
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {"Authorization": basic(self._config.client_id, self._config.client_secret)}

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
            response = await http.get(OIDC_DISCOVERY_PATH)
            response.raise_for_status()
            self._openid_config = routes.decode(response)
        return self._openid_config

    async def get_jwks(self) -> dict[str, Any]:
        """Get JSON Web Key Set for token verification.

        Returns:
            JWKS with public keys for JWT verification.
        """
        http = await self._get_http()
        response = await http.get(OIDC_JWKS_PATH)
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
        return f"{base_url}{OIDC_AUTHORIZE_PATH}?{urlencode(params)}"

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
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

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
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

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
            OIDC_TOKEN_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return TokenResponse.model_validate(routes.decode(response))

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
            jwks_url = self._config.jwks_uri
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
            OIDC_INTROSPECT_PATH,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return routes.decode(response)

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
            OIDC_USERINFO_PATH,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return UserInfo.model_validate(routes.decode(response))

    # =========================================================================
    # User Management (IAM Admin API)
    # =========================================================================

    async def get_user(self, user_id: str) -> User:
        """Get one user, by `name` or by `owner/name`.

        Raises routes.IAMError with status 404 when the user is absent.
        """
        owner, name = routes.owner_name(user_id, self._config.organization)
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.row(routes.USERS, owner, name), headers=self._admin_headers())
        )
        return User.model_validate(body)

    async def get_users(self, owner: str | None = None) -> list[User]:
        """List users. Omitting `owner` lets the server scope the read."""
        params = {"owner": owner} if owner else {}
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.USERS, params=params, headers=self._admin_headers())
        )
        return [User.model_validate(u) for u in routes.listing(body, "users")]

    async def get_user_count(self, *, owner: str | None = None) -> int:
        """Number of users in scope, from the list route's own total."""
        params = {"owner": owner} if owner else {}
        params["limit"] = "1"
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.USERS, params=params, headers=self._admin_headers())
        )
        return int(body["total"])

    async def create_user(self, user: User, password: str = "") -> User:
        """Create a user. The server hashes the password; it never stores it as given."""
        http = await self._get_http()
        body = routes.check(
            await http.post(
                routes.USERS, headers=self._admin_headers(), json=self._user_body(user, password)
            )
        )
        return User.model_validate(body)

    async def update_user(self, user: User, password: str = "") -> User:
        """Replace a user row. Omitted secrets and flags are carried over by the server."""
        http = await self._get_http()
        body = routes.check(
            await http.put(
                routes.row(routes.USERS, user.owner, user.name),
                headers=self._admin_headers(),
                json=self._user_body(user, password),
            )
        )
        return User.model_validate(body)

    async def delete_user(self, user: User) -> bool:
        """Delete a user. True once the row is gone."""
        http = await self._get_http()
        body = routes.check(
            await http.delete(
                routes.row(routes.USERS, user.owner, user.name), headers=self._admin_headers()
            )
        )
        return bool(body.get("deleted"))

    @staticmethod
    def _user_body(user: User, password: str) -> dict[str, Any]:
        """The nested write body the users routes take."""
        body: dict[str, Any] = {
            "user": user.model_dump(by_alias=True, exclude_none=True)
        }
        if password:
            body["password"] = password
        return body

    # =========================================================================
    # Organizations
    # =========================================================================

    async def get_organizations(
        self, *, q: str = "", limit: int = 0
    ) -> list[dict[str, Any]]:
        """List organizations visible to the caller."""
        params: dict[str, str] = {}
        if q:
            params["q"] = q
        if limit:
            params["limit"] = str(limit)
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.ORGANIZATIONS, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "organizations")

    async def get_organization(self, name: str) -> dict[str, Any]:
        """Get one organization. Organization rows are owned by `admin`."""
        http = await self._get_http()
        return routes.check(
            await http.get(
                routes.row(routes.ORGANIZATIONS, "admin", name), headers=self._admin_headers()
            )
        )

    # =========================================================================
    # Providers
    # =========================================================================

    async def get_providers(self, *, owner: str | None = None) -> list[dict[str, Any]]:
        """List authentication providers."""
        params = {"owner": owner} if owner else {}
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.PROVIDERS, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "providers")

    # =========================================================================
    # Roles
    # =========================================================================

    async def get_roles(self, *, owner: str | None = None) -> list[dict[str, Any]]:
        """List roles."""
        params = {"owner": owner or self._config.organization}
        http = await self._get_http()
        body = routes.check(
            await http.get(routes.ROLES, params=params, headers=self._admin_headers())
        )
        return routes.listing(body, "roles")

    async def get_role(
        self, role_name: str, *, owner: str | None = None
    ) -> dict[str, Any]:
        """Get one role, members included."""
        org = owner or self._config.organization
        http = await self._get_http()
        return routes.check(
            await http.get(routes.row(routes.ROLES, org, role_name), headers=self._admin_headers())
        )

    async def put_role(self, role: dict[str, Any]) -> dict[str, Any]:
        """Replace a role row."""
        http = await self._get_http()
        return routes.check(
            await http.put(
                routes.row(routes.ROLES, role["owner"], role["name"]),
                headers=self._admin_headers(),
                json=role,
            )
        )

    async def get_user_roles(
        self, username: str, *, owner: str | None = None
    ) -> list[dict[str, Any]]:
        """Roles the user belongs to.

        Membership is the role's own `users` list, so this reads the roles of the
        organization and keeps the ones naming this user.
        """
        org = owner or self._config.organization
        member = f"{org}/{username}"
        return [r for r in await self.get_roles(owner=org) if member in (r.get("users") or [])]

    async def add_role_for_user(
        self, username: str, role_name: str, *, owner: str | None = None
    ) -> bool:
        """Add a user to a role. True if the role changed."""
        org = owner or self._config.organization
        member = f"{org}/{username}"
        role = await self.get_role(role_name, owner=org)
        members = list(role.get("users") or [])
        if member in members:
            return False
        role["users"] = members + [member]
        await self.put_role(role)
        return True

    async def remove_role_from_user(
        self, username: str, role_name: str, *, owner: str | None = None
    ) -> bool:
        """Remove a user from a role. True if the role changed."""
        org = owner or self._config.organization
        member = f"{org}/{username}"
        role = await self.get_role(role_name, owner=org)
        members = list(role.get("users") or [])
        if member not in members:
            return False
        role["users"] = [m for m in members if m != member]
        await self.put_role(role)
        return True

    # =========================================================================
    # Password
    # =========================================================================

    async def set_password(
        self,
        user_owner: str,
        user_name: str,
        new_password: str,
        old_password: str = "",
    ) -> dict[str, Any]:
        """Set a user's password. The server hashes it; nothing stores it in the clear."""
        http = await self._get_http()
        body = routes.check(
            await http.put(
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

    async def get_application(self) -> Application:
        """Get the application this client is configured for."""
        http = await self._get_http()
        body = routes.check(
            await http.get(
                routes.row(
                    routes.APPLICATIONS,
                    self._config.organization,
                    self._config.application,
                ),
                headers=self._admin_headers(),
            )
        )
        return Application.model_validate(body)

    async def get_applications(self, owner: str) -> list[Application]:
        """List an organization's applications. IAM requires the owner here."""
        http = await self._get_http()
        body = routes.check(
            await http.get(
                routes.APPLICATIONS, params={"owner": owner}, headers=self._admin_headers()
            )
        )
        return [
            Application.model_validate(a) for a in routes.listing(body, "applications")
        ]

    async def update_application(self, application: Application) -> Application:
        """Replace an application row. An omitted clientSecret keeps the stored one."""
        http = await self._get_http()
        body = routes.check(
            await http.put(
                routes.row(routes.APPLICATIONS, application.owner, application.name),
                headers=self._admin_headers(),
                json=application.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Application.model_validate(body)

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
