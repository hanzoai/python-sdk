"""Hanzo IAM - Identity and Access Management SDK for Hanzo ecosystem."""

from hanzo_iam.async_client import AsyncIAMClient
from hanzo_iam.client import IAMClient
from hanzo_iam.models import (
    Application,
    IAMConfig,
    JWTClaims,
    Organization,
    TokenResponse,
    User,
    UserInfo,
)

from importlib.metadata import PackageNotFoundError, version as _version

try:
    # Single-sourced from the installed distribution. This said "1.1.1" while
    # pyproject said 1.30.0 — 29 minor versions of drift.
    __version__ = _version("hanzo-iam")
except PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+dev"

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
]
