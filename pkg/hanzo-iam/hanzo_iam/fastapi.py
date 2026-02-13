"""FastAPI integration for Hanzo IAM.

Provides FastAPI dependencies for authentication and authorization
using Hanzo IAM (hanzo.id, zoo.id, lux.id, pars.id).

Usage:
    from hanzo_iam.fastapi import configure, require_auth, get_current_user

    # Configure at startup
    configure(
        client_id="your-client-id",
        client_secret="your-client-secret",
        org="hanzo",
    )

    # Use in routes
    @app.get("/protected")
    async def protected(claims: JWTClaims = Depends(require_auth)):
        return {"user": claims.sub}

    @app.get("/user")
    async def user_info(user: UserInfo = Depends(get_current_user)):
        return {"email": user.email}
"""

from __future__ import annotations

import os
from typing import Callable

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from hanzo_iam.models import IAMConfig, JWTClaims, Organization, UserInfo

# Global state
_config: IAMConfig | None = None
_jwks_client: PyJWKClient | None = None

# Security scheme
_bearer = HTTPBearer(auto_error=False)
_bearer_required = HTTPBearer(auto_error=True)


def configure(
    client_id: str | None = None,
    client_secret: str | None = None,
    org: str | Organization = Organization.HANZO,
) -> IAMConfig:
    """Configure the global IAM client.

    Args:
        client_id: OAuth2 client ID (or HANZO_IAM_CLIENT_ID env var)
        client_secret: OAuth2 client secret (or HANZO_IAM_CLIENT_SECRET env var)
        org: Organization (hanzo, zoo, lux, pars)

    Returns:
        The configured IAMConfig

    Raises:
        ValueError: If client_id is not provided
    """
    global _config, _jwks_client

    # Resolve organization
    if isinstance(org, str):
        org = Organization(org)

    # Get credentials from args or environment
    resolved_client_id = client_id or os.getenv("HANZO_IAM_CLIENT_ID", "")
    resolved_client_secret = client_secret or os.getenv("HANZO_IAM_CLIENT_SECRET", "")

    if not resolved_client_id:
        raise ValueError("client_id required (or set HANZO_IAM_CLIENT_ID)")

    _config = IAMConfig(
        server_url=org.iam_url,
        client_id=resolved_client_id,
        client_secret=resolved_client_secret,
        organization=org.value,
    )

    # Reset JWKS client to pick up new config
    _jwks_client = None

    return _config


def get_config() -> IAMConfig:
    """Get the configured IAM config.

    Returns:
        The current IAMConfig

    Raises:
        RuntimeError: If configure() has not been called
    """
    if _config is None:
        raise RuntimeError("IAM not configured. Call configure() first.")
    return _config


def _get_jwks_client() -> PyJWKClient:
    """Get or create the JWKS client."""
    global _jwks_client

    if _jwks_client is None:
        config = get_config()
        jwks_url = f"{config.server_url}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)

    return _jwks_client


# =============================================================================
# Token extraction dependencies
# =============================================================================


async def get_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    """Extract bearer token from request (optional).

    Returns None if no token is present.
    """
    if credentials is None:
        return None
    return credentials.credentials


async def require_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_required),
) -> str:
    """Require bearer token from request.

    Raises 401 if no token is present.
    """
    return credentials.credentials


# =============================================================================
# Token validation dependencies
# =============================================================================


def _validate_token(token: str) -> JWTClaims:
    """Validate JWT token and return claims.

    Args:
        token: JWT token string

    Returns:
        JWTClaims with validated claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    config = get_config()
    jwks_client = _get_jwks_client()

    try:
        # Get signing key from JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=config.client_id,
            issuer=config.server_url,
        )

        return JWTClaims.model_validate(payload)

    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {err}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


async def get_token_claims(
    token: str | None = Depends(get_token),
) -> JWTClaims | None:
    """Validate token and return claims (optional).

    Returns None if no token is present.
    Raises 401 if token is invalid.
    """
    if token is None:
        return None
    return _validate_token(token)


async def require_auth(
    token: str = Depends(require_token),
) -> JWTClaims:
    """Require valid token and return claims.

    Raises 401 if no token or invalid token.
    """
    return _validate_token(token)


# =============================================================================
# User info dependencies
# =============================================================================


async def _fetch_user_info(token: str) -> UserInfo:
    """Fetch user info from IAM server.

    Args:
        token: Access token

    Returns:
        UserInfo from the IAM userinfo endpoint

    Raises:
        HTTPException: If request fails
    """
    config = get_config()
    userinfo_url = f"{config.server_url}/api/userinfo"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch user info",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserInfo.model_validate(response.json())


async def get_current_user(
    token: str = Depends(require_token),
) -> UserInfo:
    """Get full user info from IAM.

    Requires valid token. Fetches user info from IAM userinfo endpoint.
    """
    return await _fetch_user_info(token)


async def get_optional_user(
    token: str | None = Depends(get_token),
) -> UserInfo | None:
    """Get user info if authenticated, None otherwise.

    Does not raise on missing/invalid token.
    """
    if token is None:
        return None

    try:
        _validate_token(token)  # Validate first
        return await _fetch_user_info(token)
    except HTTPException:
        return None


# =============================================================================
# Authorization dependencies
# =============================================================================


def require_org(allowed_orgs: list[str | Organization]) -> Callable:
    """Create dependency that requires user to be from specific org(s).

    Args:
        allowed_orgs: List of allowed organization names or Organization enums

    Returns:
        FastAPI dependency that validates org membership

    Usage:
        @app.get("/hanzo-only")
        async def route(claims: JWTClaims = Depends(require_org(["hanzo"]))):
            ...
    """
    # Normalize to strings
    orgs = [o.value if isinstance(o, Organization) else o for o in allowed_orgs]

    async def _check_org(claims: JWTClaims = Depends(require_auth)) -> JWTClaims:
        user_org = claims.owner or ""
        if user_org not in orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to organizations: {orgs}",
            )
        return claims

    return _check_org


async def require_admin(
    claims: JWTClaims = Depends(require_auth),
) -> JWTClaims:
    """Require user to have admin role.

    Raises 403 if user is not an admin.
    """
    if "admin" not in claims.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return claims


def require_role(role: str) -> Callable:
    """Create dependency that requires specific role.

    Args:
        role: Required role name

    Returns:
        FastAPI dependency that validates role

    Usage:
        @app.get("/moderators")
        async def route(claims: JWTClaims = Depends(require_role("moderator"))):
            ...
    """

    async def _check_role(claims: JWTClaims = Depends(require_auth)) -> JWTClaims:
        if role not in claims.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}",
            )
        return claims

    return _check_role


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Configuration
    "configure",
    "get_config",
    # Token extraction
    "get_token",
    "require_token",
    # Token validation
    "get_token_claims",
    "require_auth",
    # User info
    "get_current_user",
    "get_optional_user",
    # Authorization
    "require_org",
    "require_admin",
    "require_role",
]
