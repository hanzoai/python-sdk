"""Hanzo IAM - Identity and Access Management SDK for Hanzo ecosystem."""

from hanzo_iam import store
from hanzo_iam.config import IAMConfig
from hanzo_iam.async_client import AsyncIAMClient
from hanzo_iam.client import IAMClient

# Modules are nouns (`oauth`, `tokens`, `store`); package exports are the verbs
# (`login`, `verify`). No export shadows the module it came from — an earlier
# layout had `hanzo_iam.verify` mean both a module and a function, and
# `import hanzo_iam.verify` silently handed back the function.
from hanzo_iam.oauth import LoginError, login
from hanzo_iam.models import (
    IAM_ROUTE_PREFIX,
    OIDC_AUTHORIZE_PATH,
    OIDC_DEVICE_PATH,
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
from hanzo_iam.tokens import Verification, unverified_claims, verify

from importlib.metadata import PackageNotFoundError, version as _version

try:
    # Single-sourced from the installed distribution. A second literal here
    # said 1.1.1 while pyproject said 1.30.0, and callers read whichever they
    # happened to reach.
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
    # Endpoint seam
    "IAM_ROUTE_PREFIX",
    "OIDC_AUTHORIZE_PATH",
    "OIDC_DEVICE_PATH",
    "OIDC_JWKS_PATH",
    "OIDC_TOKEN_PATH",
    "OIDC_USERINFO_PATH",
    # Auth
    "login",
    "LoginError",
    "store",
    "verify",
    "Verification",
    "unverified_claims",
]
