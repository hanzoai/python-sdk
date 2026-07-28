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

import importlib.metadata as _md

try:
    __version__ = _md.version("hanzo-iam")
except _md.PackageNotFoundError:  # running from a source tree
    __version__ = "1.30.1"

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
