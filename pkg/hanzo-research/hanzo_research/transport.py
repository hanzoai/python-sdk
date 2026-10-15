"""One HTTP path to api.hanzo.ai for both clients: the credential, the acting org, retries, refusals.

Stdlib only (urllib), so a zero-dependency harness can import it.
"""

from __future__ import annotations

import os
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping
from importlib import metadata

from . import wire
from .errors import Error, Denied, Unavailable, refusal

DEFAULT_BASE = "https://api.hanzo.ai"
try:
    # one statement of the version: the installed distribution's (pyproject.toml)
    VERSION = metadata.version("hanzo-research")
except metadata.PackageNotFoundError:
    VERSION = "source"
# A body past this is refused rather than read (the crate's cap is 8 MiB, which the hanzo
# org's run listing, 1.5 MB at 330 runs, passes at about 1,800 runs).
MAX_RESPONSE_BYTES = 64 << 20
# 503 is the research store's failover answer ("retry"): asked again after 2, 4 and 8 s.
WAITS = (2, 4, 8)
ADMIN = "admin"
LOOPBACK = ("127.0.0.1", "localhost", "::1")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise Error(f"redirect to {newurl} refused", code, req.get_method(), urllib.parse.urlsplit(req.full_url).path)


class Transport:
    """Base URL, credential, acting org and project, shared by `Research` and `Arena`.

    `token` None resolves `HANZO_API_KEY`, else `hanzo auth token`, on the first call that
    needs one; "" sends no credential. The org a call acts in is the server's rule, read
    from the token: a person's home org is the first of its signed `orgs`, and `org`
    switches to another of them (`X-Org-Id`), any org for a SuperAdmin (home `admin`); a
    machine token acts in its `owner` alone; an API key in the org it was minted in. A
    switch the server would not honour, where it would act in the home org instead, is
    refused here. The project is the token's `project` claim, `default` for a key or a
    token naming none, and `project` (or RESEARCH_PROJECT) asking another is refused.
    """

    def __init__(
        self,
        base: str | None = None,
        token: str | None = None,
        org: str | None = None,
        project: str | None = None,
        timeout: float = 120.0,
    ):
        self.base = (base or os.environ.get("RESEARCH_BASE") or DEFAULT_BASE).rstrip("/")
        parts = urllib.parse.urlsplit(self.base)
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in LOOPBACK):
            # a bearer token never crosses a network in the clear
            raise ValueError(f"base {self.base!r} is neither https nor http on this machine")
        self.timeout = timeout
        self._token = token
        self._cli = False
        self._org = (org or "").strip() or None
        self._project = project or os.environ.get("RESEARCH_PROJECT") or None
        self._checked = False
        self._opener = urllib.request.build_opener(_NoRedirect)

    # ── identity ────────────────────────────────────────────────────────────────

    @property
    def token(self) -> str:
        if self._token is None:
            env = os.environ.get("HANZO_API_KEY", "").strip()
            self._token = env or wire.token()
            self._cli = not env and bool(self._token)
        if not self._checked:
            self._check()
        return self._token

    @property
    def project(self) -> str:
        """The project records are filed under: the token's claim, `default` for a key or none."""
        tok = self.token
        if tok:
            return wire.claimed(tok) or "default"
        return wire.scope(self._project or "")

    @property
    def org(self) -> str | None:
        """The org calls act in: the one asked for, else the token's home org; None for a key or no token."""
        return self._org or (_identity(self.token)[0] if self.token else None)

    def _check(self) -> None:
        tok = self._token or ""
        if any(not 32 < ord(ch) < 127 for ch in tok):
            # never echoed: the value is a secret
            raise Denied("the credential holds characters an HTTP header cannot carry")
        have = wire.claimed(tok) or "default"
        if tok and self._project and wire.scope(self._project) != have:
            raise Error(f"the token's project is {have}, not {self._project}: records would be filed under {have}")
        if tok and self._org:
            home, orgs, machine = _identity(tok)
            if home is None:
                raise Denied("an API key acts in the org it was minted in; org= cannot move it")
            if machine and self._org != home:
                raise Denied(f"a machine token acts in its own org, {home}, never {self._org}")
            if home != ADMIN and self._org != home and (self._org == ADMIN or self._org not in orgs):
                raise Denied(
                    f"this token cannot act in org {self._org} (its orgs: {', '.join(orgs)}); the server would act in {home}"
                )
        self._checked = True

    # ── calls ───────────────────────────────────────────────────────────────────

    def get(self, path: str, query: Mapping[str, Any] | None = None, auth: bool = True) -> Any:
        return json.loads(self.call("GET", path, query, None, auth) or b"null")

    def post(self, path: str, body: Any, query: Mapping[str, Any] | None = None) -> Any:
        return json.loads(self.call("POST", path, query, body, True) or b"null")

    def call(self, method: str, path: str, query: Mapping[str, Any] | None, body: Any, auth: bool) -> bytes:
        """One request; its raw answer on 2xx, else the typed error. 503 is asked again after 2, 4 and 8 s."""
        url = self.base + path + _query(query)
        data = None if body is None else json.dumps(body, allow_nan=False).encode()
        waits = list(WAITS)
        refreshed = False
        while True:
            # the base is https, or http to this machine, checked in __init__
            req = urllib.request.Request(url, data=data, method=method, headers=self._headers(auth, data is not None))  # noqa: S310
            try:
                with self._opener.open(req, timeout=self.timeout) as r:
                    return _read(r, method, path)
            except urllib.error.HTTPError as e:
                raw = _read(e, method, path) if e.fp else b""
                if e.code == 503 and waits:
                    time.sleep(waits.pop(0))
                    continue
                if e.code == 401 and auth and self._cli and not refreshed:
                    # a CLI token lives about an hour: fetch the current one and ask once more
                    refreshed, self._token, self._checked = True, wire.token(), False
                    continue
                err = refusal(e.code, raw, method, path, _retry(e.headers))
                if isinstance(err, Denied) and auth and not self._token:
                    err.message += " (no credential: set HANZO_API_KEY or run `hanzo auth login`)"
                    err.args = (f"{method} {path}: {err.status}: {err.message}",)
                raise err from None
            except Error:
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                raise Unavailable(f"no answer: {getattr(e, 'reason', e)}", 0, method, path) from None

    def _headers(self, auth: bool, body: bool) -> dict[str, str]:
        h = {"Accept": "application/json", "User-Agent": f"hanzo-research/{VERSION} (python)"}
        if body:
            h["Content-Type"] = "application/json"
        if auth:
            tok = self.token
            if tok:
                h["Authorization"] = f"Bearer {tok}"
            h["X-Project-Id"] = self.project
            if self._org:
                h["X-Org-Id"] = self._org
        return h


def _identity(tok: str) -> tuple[str | None, list[str], bool]:
    """(home org, signed orgs, machine) of a JWT as the server reads them; home None for a non-JWT key."""
    c = wire.claims(tok)
    if c is None:
        return None, [], False
    orgs = [str(m.get("org")) for m in c.get("orgs") or [] if isinstance(m, dict) and m.get("org")]
    machine = c.get("type") == "application" or not orgs
    return (str(c.get("owner") or "") if machine else orgs[0]), orgs, machine


def _query(q: Mapping[str, Any] | None) -> str:
    pairs = []
    for k, v in (q or {}).items():
        if v is None or v == "":
            continue
        if isinstance(v, bool):
            v = "true" if v else "false"
        pairs.append(f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}")
    return "?" + "&".join(pairs) if pairs else ""


def _read(r: Any, method: str, path: str) -> bytes:
    raw = r.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise Error(f"answer past {MAX_RESPONSE_BYTES} bytes refused", getattr(r, "status", 0) or 0, method, path)
    return bytes(raw)


def _retry(headers: Any) -> float | None:
    v = headers.get("Retry-After") if headers else None
    try:
        return float(v) if v else None
    except ValueError:
        return None
