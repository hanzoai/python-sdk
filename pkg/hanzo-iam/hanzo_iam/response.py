"""The ONE place an IAM HTTP response becomes a value or an error.

Three modules used to decide this independently — `client` (15 times, inline),
`oauth` (`_json_or_raise`) and `fastapi` (`_fetch_user_info`) — and they
disagreed on the question that actually bites: *is the body JSON at all?*

Only `oauth` asked. hanzo.id serves its sign-in SPA on every unmatched path, so
a wrong path answers **200 text/html**; a decoder that trusts the status code
then dies inside `.json()` with a byte offset instead of naming the path. The
other two surfaces call the same host over the same base URL, so they had the
same trap and none of the protection. `models.py` documents it for the OIDC
paths; this is where it is enforced for all of them.

Two functions, one layered on the other, because there are two decisions:

    decode  the WIRE decision   — is this JSON, and did IAM say no?
    unwrap  the ENVELOPE decision — `{status,msg,data}` -> data, or raise

OIDC endpoints answer bare JSON and use `decode`. The v1 compat verbs answer the
`{status,msg,data}` envelope and use `unwrap`. Neither is a flag on the other:
a flag would be two behaviours behind one name.
"""

from __future__ import annotations

from typing import Any

import httpx


class IAMError(Exception):
    """An IAM call did not produce a value.

    The ONE failure type for every IAM HTTP surface in this package. It replaced
    three: `LoginError` (oauth), `ValueError` (client) and a bare
    `HTTPException` (fastapi) — so "the call failed" was three different
    excepts depending on which module you happened to be holding.
    """


def decode(resp: httpx.Response, what: str) -> Any:
    """Return the JSON body of `resp`, or raise IAMError describing the refusal.

    `what` names the endpoint in the message ("token endpoint", "get-users"),
    because the failure worth distinguishing is *which* call went wrong.

    Refuses, in order:

    1. a body that is not JSON — this is a WRONG PATH, not a rejected call, and
       saying so is the whole point of the gate;
    2. a body that claims to be JSON and will not parse;
    3. an OAuth error object (`{"error": ..., "error_description": ...}`),
       reported in the server's own words;
    4. any non-2xx status. Neither predecessor checked this: `client` called
       `raise_for_status()` and threw the server's explanation away, `oauth`
       relied on the error object alone. A 403 from IAM's authz seam carries a
       JSON body and must surface as a refusal, never as an empty result.
    """
    ctype = resp.headers.get("content-type", "")
    if "json" not in ctype:
        raise IAMError(
            f"{what} answered {resp.status_code} {ctype or 'no content-type'}"
            f" instead of JSON at {resp.request.url} — this is the wrong path,"
            " not a rejected call"
        )
    try:
        payload = resp.json()
    except ValueError as e:
        raise IAMError(f"{what} returned unparseable JSON: {e}") from e

    if isinstance(payload, dict) and payload.get("error"):
        raise IAMError(
            f"{what} answered {resp.status_code} rejected: {payload['error']}"
            f" — {payload.get('error_description') or payload.get('msg') or 'no description'}"
        )
    if resp.status_code >= 400:
        raise IAMError(f"{what} answered {resp.status_code}: {payload}")
    return payload


def unwrap(resp: httpx.Response, what: str) -> Any:
    """`decode`, plus the v1 `{status,msg,data}` envelope the compat verbs use.

    The envelope reports failure as **200** `{"status":"error","msg":...}` — the
    status line says nothing — so this is the only place that can tell a refusal
    from a result on those routes. Callers get the value or an exception and
    never inspect `status` themselves; a second reader of that field is a second
    place the error channel lives.
    """
    payload = decode(resp, what)
    if not isinstance(payload, dict):
        return payload
    if payload.get("status") == "error":
        raise IAMError(f"{what} failed: {payload.get('msg') or 'no message'}")
    return payload.get("data", payload)
