"""Hanzo IAM - Identity and Access Management SDK for Hanzo ecosystem."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from hanzo_iam import store

# ONE surface per concern, and no concern served twice:
#
#   client    the ADMIN entity verbs, against the issuer
#   oauth     the OIDC protocol surface (authorize, exchange, refresh, login)
#   tokens    judging a credential
#   store     persisting one
#   response  turning any IAM reply into a value or an IAMError
#
# `IAMClient` used to own an OIDC surface as well — get_authorization_url,
# exchange_code, refresh_token, get_user_info, and a password-grant `login`
# that collided by name with the `login` exported below. Two owners of the
# token endpoint is two answers to "what authenticates this exchange": oauth
# proves possession with PKCE, the client posted a client_secret.
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
from hanzo_iam.oauth import login

# ONE failure type for every IAM call. It replaced three that meant the same
# thing in different modules: `LoginError` (oauth), `ValueError` (client) and a
# bare `HTTPException` (fastapi) — so "the call failed" was three different
# excepts depending on which surface you happened to be holding.
from hanzo_iam.response import IAMError
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
    "IAMError",
    "store",
    "verify",
    "Verification",
    "unverified_claims",
]
