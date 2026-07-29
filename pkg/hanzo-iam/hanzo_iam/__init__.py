"""Hanzo IAM - Identity and Access Management SDK for Hanzo ecosystem."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from hanzo_iam import store

# One IAM HTTP client. There were two — a sync `IAMClient` and an async
# `AsyncIAMClient` mirroring its whole surface, with no consumer, no test and
# no export used anywhere in the fleet. Worse, `AsyncIAMClient` was DEFINED
# TWICE (client.py and async_client.py) and the two copies had drifted, so the
# name resolved to whichever module won the import. Re-add async when
# something needs it, generated from the spec, not hand-mirrored.
from hanzo_iam.client import IAMClient
from hanzo_iam.config import IAMConfig
from hanzo_iam.models import (
    IAM_ROUTE_PREFIX,
    IAM_WHOAMI_PATH,
    OIDC_AUTHORIZE_PATH,
    OIDC_DEVICE_PATH,
    OIDC_DISCOVERY_PATH,
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

# Modules are nouns (`oauth`, `tokens`, `store`); package exports are the verbs
# (`login`, `verify`). No export shadows the module it came from — an earlier
# layout had `hanzo_iam.verify` mean both a module and a function, and
# `import hanzo_iam.verify` silently handed back the function.
from hanzo_iam.oauth import LoginError, login
from hanzo_iam.tokens import Verification, unverified_claims, verify

try:
    # Single-sourced from the installed distribution. A second literal here
    # said 1.1.1 while pyproject said 1.30.0, and callers read whichever they
    # happened to reach.
    __version__ = _version("hanzo-iam")
except PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+dev"

__all__ = [
    # Client
    "IAMClient",
    # Config
    "IAMConfig",
    # Models
    "Application",
    "JWTClaims",
    "Organization",
    "TokenResponse",
    "User",
    "UserInfo",
    # Endpoint seam -- ALL of it. A partial export is why a caller ends up
    # re-spelling the one path that was missing.
    "IAM_ROUTE_PREFIX",
    "IAM_WHOAMI_PATH",
    "OIDC_AUTHORIZE_PATH",
    "OIDC_DEVICE_PATH",
    "OIDC_DISCOVERY_PATH",
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
