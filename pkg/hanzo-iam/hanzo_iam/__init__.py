"""Hanzo IAM - Identity and Access Management SDK for Hanzo ecosystem."""

from hanzo_iam.async_client import AsyncCasdoorSDK, AsyncIAMClient
from hanzo_iam.client import CasdoorSDK, IAMClient
from hanzo_iam.models import (
    Application,
    IAMConfig,
    JWTClaims,
    Organization,
    TokenResponse,
    User,
    UserInfo,
)

__version__ = "1.1.0"

__all__ = [
    # Clients
    "IAMClient",
    "AsyncIAMClient",
    # Config
    "IAMConfig",
    # Models
    "Application",
    "JWTClaims",
    "Organization",
    "TokenResponse",
    "User",
    "UserInfo",
    # Aliases for Casdoor compatibility
    "CasdoorSDK",
    "AsyncCasdoorSDK",
]
