"""Authentication middleware and utilities."""

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings

security = HTTPBearer(auto_error=False)


def get_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> str | None:
    """
    Extract API key from request.

    Checks in order:
    1. Authorization header (Bearer token)
    2. x-hanzo-api-key header
    3. x-api-key header
    4. apikey in JSON body

    Args:
        request: FastAPI request
        credentials: Optional bearer credentials

    Returns:
        API key if found, None otherwise
    """
    # Check Bearer token
    if credentials and credentials.credentials:
        return credentials.credentials

    # Check custom headers
    api_key = request.headers.get("x-hanzo-api-key")
    if api_key:
        return api_key

    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key

    # Check JSON body (for backwards compatibility)
    # This is handled in the request models

    return None


def verify_api_key(api_key: str | None) -> bool:
    """
    Verify API key.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    if settings.disable_auth:
        return True

    if not api_key:
        return False

    # Compare with configured API key
    return api_key == settings.api_key


def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> str:
    """
    Require authentication for a request.

    Args:
        request: FastAPI request
        credentials: Optional bearer credentials

    Returns:
        API key if authenticated

    Raises:
        HTTPException: If not authenticated
    """
    api_key = get_api_key(request, credentials)

    # Check if auth is disabled
    if settings.disable_auth:
        return api_key or "disabled"

    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key or ""  # Return empty string if None


async def get_or_verify_user_id(
    user_id: str,
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str:
    """
    Get or verify user ID from request.

    In a production system, this would validate that the authenticated
    user has access to the requested user_id. For now, we just verify
    authentication and return the user_id.

    Args:
        user_id: Requested user ID
        credentials: Optional bearer credentials
        request: FastAPI request

    Returns:
        Verified user ID

    Raises:
        HTTPException: If not authenticated or unauthorized
    """
    # Require authentication
    require_auth(request, credentials)

    # In a real system, we would check if the API key owner
    # has access to this user_id. For now, just return it.
    return user_id
