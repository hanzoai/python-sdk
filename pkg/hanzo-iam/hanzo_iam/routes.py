"""Hanzo IAM endpoint paths — the one place this SDK names an admin route.

Every path here is the NATIVE surface. The legacy "verb" spellings this SDK used
to call (`get-user`, `get-users`, `get-organizations`, …) are being removed from
the server: they are an upstream shape, HIP-0111 forbids them, and a capability
that has an RFC uses its RFC.

Two things changed together, which is why this module exists rather than 22
inline literals:

    path      the verb URL became a noun URL
    envelope  the verb surface answered {status, msg, data} at HTTP 200 even for
              a miss. The native surface returns the object at the TOP LEVEL and
              uses real status codes, and it NAMES its lists — {"users": [...]},
              not {"data": [...]}.

Swapping only the path is the dangerous half. A caller that does
`x if isinstance(x, list) else []` against a native response gets `[]` — it
reports "none" for a healthy org instead of failing.

`unwrap` reads both shapes so a fleet mid-rollout keeps working. That is
deliberately temporary: once every server serves native only, the envelope branch
is dead code and should be deleted with it.

OIDC/OAuth paths are NOT here — they live in models.py (OIDC_TOKEN_PATH and
friends) and are pinned by tests/test_endpoints.py. This module is the admin
surface only.
"""

from __future__ import annotations

import httpx

from typing import Any

# --- native admin routes -----------------------------------------------------

USER = "/v1/iam/users/get"
USERS = "/v1/iam/users"
APPLICATION = "/v1/iam/application"
APPLICATIONS = "/v1/iam/applications"
ORGANIZATION = "/v1/iam/organizations/get"
ORGANIZATIONS = "/v1/iam/organizations"
PROVIDERS = "/v1/iam/providers"
ROLE = "/v1/iam/roles/get"
ROLES = "/v1/iam/roles"

#: OAuth 2.0 token endpoint (RFC 6749 §3.2). The `oauth/access_token` spelling
#: this SDK used is a legacy alias the server still answers but never advertises
#: — OIDC discovery names only this one.
TOKEN = "/v1/iam/oauth/token"

#: The key the native surface wraps a LIST in, per route. The verb surface put
#: every list under "data"; the native one names what it returns. A list route
#: missing from this table unwraps to [] and reads as "empty".
LIST_KEY = {
    USERS: "users",
    APPLICATIONS: "applications",
    ORGANIZATIONS: "organizations",
    PROVIDERS: "providers",
    ROLES: "roles",
}


class IAMError(Exception):
    """An IAM call did not produce a value."""


def decode(response: httpx.Response) -> Any:
    """The wire decision, before the envelope decision: is this JSON at all?

    hanzo.id serves its sign-in SPA on every unmatched path, so a wrong path
    answers 200 text/html. A decoder that trusts the status code then dies
    inside .json() with a byte offset; this names the path instead.
    """
    kind = response.headers.get("content-type", "")
    if "json" not in kind:
        raise IAMError(
            f"{response.request.method} {response.request.url} answered"
            f" {response.status_code} {kind or 'no content-type'} rather than JSON"
            " — that is a path IAM does not serve, not a refusal"
        )
    try:
        return response.json()
    except ValueError as e:
        raise IAMError(f"{response.request.url} returned unparseable JSON: {e}") from e


def unwrap(body: Any, list_key: str | None = None) -> Any:
    """Return the payload from either the native or the legacy envelope.

    Raises ValueError when the legacy envelope carries an error, because that
    surface reported failures INSIDE a 200 and callers relied on this raising
    rather than on a falsy return. The native surface signals with the status
    code, which the caller has already checked via raise_for_status().
    """
    if not isinstance(body, dict):
        return body

    if body.get("status") == "error":
        raise ValueError(body.get("msg") or "IAM request failed")

    if list_key is not None:
        if list_key in body:  # native: {"users": [...]}
            return body[list_key] or []
        if "data" in body:  # legacy: {"status", "msg", "data": [...]}
            return body["data"] or []
        return []

    # Only a body whose keys are EXACTLY the envelope's is unwrapped, so a native
    # row that legitimately carries a `data` column survives intact.
    if "data" in body and set(body) <= {"status", "msg", "data", "data2"}:
        return body["data"]
    return body
