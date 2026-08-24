"""Hanzo IAM admin addresses — the one place this SDK names an admin route.

IAM serves its CRUD under `/v1/iam/` and nowhere else. A collection is a plural
noun; one row of it is `{collection}/{owner}/{name}`, built by `row`. A row is
identified by owner and name, never by an opaque id and never by a verb.

Four readers, one per shape, so a caller never has to guess:

    decode     the wire decision, before any other: is this JSON at all?
               hanzo.id serves its sign-in SPA on every unmatched path, so a
               wrong path answers 200 text/html. This names the path instead of
               dying inside .json() with a byte offset.
    check      every response passes through it. A refusal is an RFC 9457
               problem document and absence is 404, so this raises with the
               server's own `detail` rather than returning something falsy.
    listing    a collection GET answers a wrapper keyed by the plural —
               {"users": [...], "total": N} — never a bare array. Reading a
               missing key as [] would report "none" for a healthy org, so a
               missing key raises.
    envelope   {"status", "msg", "data"} — the shape account, memberships,
               password and login answer, and only those.

A row GET, POST and PUT answer the record itself at the top level; DELETE
answers {"deleted": true}. Those need no reader beyond `check`.

OIDC/OAuth paths are NOT here — they live in models.py (OIDC_TOKEN_PATH and
friends) and are pinned by tests/test_endpoints.py. This module is the admin
surface only.
"""

from __future__ import annotations

import httpx

from typing import Any

# --- collections -------------------------------------------------------------

USERS = "/v1/iam/users"
ORGANIZATIONS = "/v1/iam/organizations"
APPLICATIONS = "/v1/iam/applications"
ROLES = "/v1/iam/roles"
PROVIDERS = "/v1/iam/providers"
PERMISSIONS = "/v1/iam/permissions"
PROJECTS = "/v1/iam/projects"
WORKSPACES = "/v1/iam/workspaces"
INVITATIONS = "/v1/iam/invitations"
AUDIT_LOGS = "/v1/iam/audit-logs"
TOKENS = "/v1/iam/tokens"
SESSIONS = "/v1/iam/sessions"
CERTS = "/v1/iam/certs"
KEYS = "/v1/iam/keys"

# --- single-address surfaces -------------------------------------------------

#: Own profile. Answers the envelope.
ACCOUNT = "/v1/iam/account"

#: Org membership. GET takes exactly one of ?user= or ?org=. Answers the envelope.
MEMBERSHIPS = "/v1/iam/memberships"

#: PUT to set a password. IAM hashes it, so a password is never a row field.
#: Answers the envelope.
PASSWORD = "/v1/iam/password"

#: POST username+password to sign in. Answers the envelope.
LOGIN = "/v1/iam/login"

#: OAuth 2.0 token endpoint (RFC 6749 §3.2). The `oauth/access_token` spelling
#: this SDK used is a legacy alias the server still answers but never advertises
#: — OIDC discovery names only this one.
TOKEN = "/v1/iam/oauth/token"

#: The key each collection GET wraps its list in. The plural in the path and the
#: key in the body are not always the same word, and a route missing from this
#: table has no reader — which is the point: add it here or do not read it.
LIST_KEY = {
    USERS: "users",
    ORGANIZATIONS: "organizations",
    APPLICATIONS: "applications",
    ROLES: "roles",
    PROVIDERS: "providers",
    PERMISSIONS: "permissions",
    PROJECTS: "projects",
    WORKSPACES: "workspaces",
    INVITATIONS: "invitations",
    AUDIT_LOGS: "auditLogs",
    TOKENS: "tokens",
    SESSIONS: "sessions",
    CERTS: "certs",
    KEYS: "keys",
}


class IAMError(Exception):
    """An IAM call did not produce a value.

    `status` is the HTTP status when IAM refused, so a caller can tell absence
    (404) from a scope refusal (403); it is None when the answer never was IAM.
    """

    def __init__(self, message: str, response: httpx.Response | None = None):
        super().__init__(message)
        self.response = response

    @property
    def status(self) -> int | None:
        return None if self.response is None else self.response.status_code


def row(collection: str, owner: str, name: str) -> str:
    """Address one row of a collection."""
    return f"{collection}/{owner}/{name}"


def owner_name(ident: str, default_owner: str) -> tuple[str, str]:
    """Split an `owner/name` identity, filling the owner when only a name is given."""
    owner, _, name = ident.rpartition("/")
    return (owner or default_owner), name


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
            " — that is a path IAM does not serve, not a refusal",
            response,
        )
    try:
        return response.json()
    except ValueError as e:
        raise IAMError(
            f"{response.request.url} returned unparseable JSON: {e}", response
        ) from e


def reason(response: httpx.Response) -> str:
    """The reason IAM gave for refusing: the RFC 9457 detail, else the body."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("title") or body.get("msg") or body)
    return str(body)


def check(response: httpx.Response) -> Any:
    """The body IAM answered, or a raise carrying the reason it refused."""
    if response.is_error:
        raise IAMError(
            f"{response.status_code} {response.request.url.path}: {reason(response)}",
            response,
        )
    return decode(response)


def listing(body: Any, key: str) -> list:
    """Read a collection GET: {"users": [...], "total": N} -> the list."""
    if not isinstance(body, dict):
        raise IAMError(f"expected an object keyed {key!r}, got {type(body).__name__}")
    if key not in body:
        raise IAMError(f"{key!r} missing from the response; keys are {sorted(body)}")
    return body[key] or []


def envelope(body: Any) -> Any:
    """Read the {status, msg, data} shape and return what it carries."""
    if not isinstance(body, dict):
        return body
    if body.get("status") == "error":
        raise IAMError(body.get("msg") or "IAM refused the request")
    return body.get("data")
