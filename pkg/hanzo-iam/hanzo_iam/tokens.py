"""The ONE place a Hanzo credential is judged valid.

Every auth surface in the SDK answers "am I logged in?" by calling `verify()`
here. It is deliberately the only implementation: the defect this replaces was
`bool(token_string)`, which reported success for the literal string
``fake.not.a.real.jwt`` and made every downstream permission check a lie.

`verify()` fails CLOSED. An unreachable JWKS is not a pass — a client that
cannot check a signature does not know the token is good, and saying otherwise
is the same bug in a new costume. The reason code says which it was so a caller
can tell "your token expired" from "you are offline".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import jwt

# Signature algorithms iam issues. `none` is absent by construction — an
# unsigned token is an unauthenticated token, and listing it here is the classic
# JWT bypass.
ALGORITHMS = ["RS256", "ES256"]

# Reason codes. A caller branches on these; the human string is for the user.
OK = "ok"
NO_CREDENTIAL = "no_credential"
MALFORMED = "malformed"
EXPIRED = "expired"
BAD_SIGNATURE = "bad_signature"
WRONG_ISSUER = "wrong_issuer"
WRONG_AUDIENCE = "wrong_audience"
JWKS_UNREACHABLE = "jwks_unreachable"
UNKNOWN_KEY = "unknown_key"
OPAQUE = "opaque"


@dataclass(frozen=True)
class Verification:
    """The result of judging a credential. Truthy only when genuinely valid."""

    valid: bool
    reason: str
    detail: str = ""
    claims: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.valid


def _jwks_client(jwks_uri: str) -> jwt.PyJWKClient:
    # PyJWKClient caches signing keys in-process, so a long-lived session pays
    # for the fetch once. Cached per URI so multiple issuers do not collide.
    client = _JWKS_CLIENTS.get(jwks_uri)
    if client is None:
        client = jwt.PyJWKClient(jwks_uri, cache_keys=True, lifespan=600)
        _JWKS_CLIENTS[jwks_uri] = client
    return client


_JWKS_CLIENTS: dict[str, jwt.PyJWKClient] = {}


def reset_jwks_cache() -> None:
    """Drop cached signing keys — for tests and for key rotation."""
    _JWKS_CLIENTS.clear()


def is_jwt(token: str) -> bool:
    """Report whether `token` is shaped like a JWS compact serialization.

    Shape only. A string that passes this has NOT been verified — that is
    precisely the confusion this module exists to end.
    """
    parts = token.split(".")
    return len(parts) == 3 and all(parts)


def verify(
    token: str | None,
    *,
    jwks_uri: str,
    issuer: str | None = None,
    audience: str | None = None,
    leeway: float = 30.0,
) -> Verification:
    """Verify `token`'s signature, expiry, issuer and (optionally) audience.

    Args:
        token: The access or ID token to judge. None/empty is not valid.
        jwks_uri: Where the issuer publishes its signing keys. Must be the
            prefixed path — hanzo.id answers 200 text/html on an unmatched
            /.well-known/jwks, which reads as a successful fetch of garbage.
        issuer: Expected `iss`. Checked when given.
        audience: Expected `aud`. Checked when given. Left None by callers that
            hold a token minted for a sibling app and only need to know the
            issuer signed it.
        leeway: Clock-skew tolerance in seconds for time-based claims.

    Returns:
        A Verification. `.valid` is True only if the signature checked out
        against a published key and no claim was violated.
    """
    if not token:
        return Verification(False, NO_CREDENTIAL, "no token present")
    if not is_jwt(token):
        # An opaque credential (an API key) cannot be judged offline. Saying
        # "valid" because it is a non-empty string is the original defect;
        # callers that accept API keys must confirm them against the server.
        return Verification(False, OPAQUE, "credential is not a JWT; verify server-side")

    try:
        signing_key = _jwks_client(jwks_uri).get_signing_key_from_jwt(token)
    except jwt.exceptions.PyJWKClientConnectionError as e:
        return Verification(False, JWKS_UNREACHABLE, f"cannot reach {jwks_uri}: {e}")
    except jwt.exceptions.PyJWKClientError as e:
        # Covers "no key for this kid" and a JWKS document that did not parse —
        # which is what an HTML sign-in page deserialises to.
        return Verification(False, UNKNOWN_KEY, f"no usable signing key from {jwks_uri}: {e}")
    except Exception as e:  # malformed header, unparseable token
        return Verification(False, MALFORMED, str(e))

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            issuer=issuer,
            audience=audience,
            leeway=leeway,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": issuer is not None,
                "verify_aud": audience is not None,
                "require": ["exp"],
            },
        )
    except jwt.ExpiredSignatureError as e:
        return Verification(False, EXPIRED, str(e))
    except jwt.InvalidIssuerError as e:
        return Verification(False, WRONG_ISSUER, str(e))
    except jwt.InvalidAudienceError as e:
        return Verification(False, WRONG_AUDIENCE, str(e))
    except jwt.InvalidSignatureError as e:
        return Verification(False, BAD_SIGNATURE, str(e))
    except jwt.InvalidTokenError as e:
        return Verification(False, MALFORMED, str(e))

    return Verification(True, OK, claims=claims)


def unverified_claims(token: str) -> dict[str, Any]:
    """Decode claims WITHOUT verifying anything — display only.

    Named so that no reader mistakes its output for a trust decision. Use
    `verify()` for anything that gates access.
    """
    return jwt.decode(token, options={"verify_signature": False})
