"""The ONE place this package spells Hanzo KMS's HTTP surface.

The paths this replaces were Infisical's (``/api/v3/secrets/raw``). Hanzo KMS is
not Infisical and never served them — ``kms.hanzo.ai/api/v3/secrets/raw``
answers ``404 {"message":"not found"}``. The canonical surface, as implemented
by the server (``~/work/hanzo/kms``) and by the reference Go client
(``kms/sdk/go/kmsclient``), is org-scoped and env-keyed:

    GET    /v1/kms/orgs/{org}/secrets                  ?prefix=
    GET    /v1/kms/orgs/{org}/secrets/{path}/{name}    ?env=
    POST   /v1/kms/orgs/{org}/secrets                  {path,name,env,value}
    DELETE /v1/kms/orgs/{org}/secrets/{path}/{name}    ?env=

A write MUST carry `env` explicitly. The server defaults a missing one to
"default", which silently diverts a prod write into the wrong bucket.
"""

from __future__ import annotations

from urllib.parse import quote

KMS_ROUTE_PREFIX = "/v1/kms"
AUTH_LOGIN_PATH = f"{KMS_ROUTE_PREFIX}/auth/login"
HEALTH_PATH = f"{KMS_ROUTE_PREFIX}/health"


def secrets_collection(org: str) -> str:
    """The org's secret collection — list (GET) and upsert (POST)."""
    return f"{KMS_ROUTE_PREFIX}/orgs/{quote(org, safe='')}/secrets"


def secret(org: str, path: str, name: str) -> str:
    """One secret's URL path.

    `path` is a hierarchy and its '/' separators are kept. `name` is a single
    key: any '/' inside it is escaped to %2F rather than promoted to a level.
    '.' and '..' segments are rejected outright — they are meaningless as key
    components and their only effect on a URL path is to climb out of the org's
    collection once a server or proxy normalises the path.
    """
    segments = [s for s in path.split("/") if s]
    for s in segments:
        if s in (".", ".."):
            raise ValueError(f"invalid secret path segment {s!r} in {path!r}")
    if name.strip("/") in ("", ".", ".."):
        raise ValueError(f"invalid secret name {name!r}")
    segments.append(name.strip("/"))
    return f"{secrets_collection(org)}/" + "/".join(quote(s, safe="") for s in segments)
