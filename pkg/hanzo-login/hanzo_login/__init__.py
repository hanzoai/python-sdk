"""Who a Hanzo tool acts as.

One resolver for every Hanzo tool on a machine, so a person signs in once, with the
``hanzo`` CLI, and every tool follows. Order:

1. ``HANZO_API_KEY`` (explicit).
2. The CLI's login: ``hanzo auth token`` prints the active identity's access token,
   ``--as <identity>`` another's. The CLI owns its identity store and the refresh; nothing
   here reads or writes that store.
3. ``apiKey`` in ``~/.hanzo/config.json`` (legacy), last, so a stale key for another
   account can never shadow a person's login.

Naming an identity (per call, or with ``use`` for this process) always asks the login,
even with a key set, and never falls through: a tool asked to act as X does not act as Y.

The CLI is ``~/.local/bin/hanzo``, never a lookup on PATH: Debian's hanzo-ide package puts
a GUI at /usr/bin/hanzo that opens a window on any arguments.
"""

from __future__ import annotations

import os
import re
import json
import time
import base64
import binascii
import subprocess
from typing import Any
from pathlib import Path
from dataclasses import field, dataclass

__all__ = [
    "Credential",
    "LoginError",
    "claims",
    "cli",
    "credential",
    "describe",
    "forget",
    "identities",
    "switch",
    "token",
    "use",
    "using",
    "valid",
    "valid_org",
]

TTL = 300  # seconds a login's token is kept: it is a JWT that lives about an hour
REFUSAL_TTL = 10  # seconds "not signed in" is remembered, so a fresh login is seen soon
TIMEOUT = 30  # seconds the CLI gets to answer (it may refresh over the network)
SKEW = 30  # a token this close to its exp is fetched again, not served from memory

_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._@+/-]{0,127}")
_KEY_PREFIX = re.compile(r"[a-z]{2}[-_]")
_FIELDS = ("key", "owner", "subject", "expiry", "active")


class LoginError(Exception):
    """The login would not answer. The message is the CLI's own one-line reason."""


@dataclass(frozen=True)
class Credential:
    """What answered. ``source`` is env, login or stored; None when nothing did.

    ``secret`` never appears in a repr. ``identity`` is the one asked for, if any.
    ``refused`` is the CLI's reason when the login was consulted and failed but another
    source answered (or none did).
    """

    source: str | None
    secret: str = field(default="", repr=False)
    identity: str | None = None
    refused: str | None = None


_using: str | None = None
_tokens: dict[str, tuple[float, str]] = {}
_refusals: dict[str, tuple[float, str]] = {}


def _now() -> float:
    return time.monotonic()


def cli() -> Path:
    """The ``hanzo`` CLI where hanzo.sh installs it."""
    return Path.home() / ".local" / "bin" / "hanzo"


def valid(identity: str) -> str:
    """``identity`` if it is ``owner`` or ``owner/name``, else LoginError. Checked before argv."""
    if not isinstance(identity, str) or not _IDENTITY.fullmatch(identity) or identity.count("/") > 1:
        # never echoed: a person may have pasted a token here
        raise LoginError(
            "an identity is owner or owner/name: 1-128 characters of A-Z a-z 0-9 . _ @ + -, "
            "starting with a letter or digit"
        )
    return identity


def valid_org(org: str) -> str:
    """``org`` if it is a name, else LoginError. It rides in the ``X-Org-Id`` header."""
    if not isinstance(org, str) or not _IDENTITY.fullmatch(org) or "/" in org:
        raise LoginError("an org is a name: 1-128 characters of A-Z a-z 0-9 . _ @ + -, starting with a letter or digit")
    return org


def _run(*args: str) -> str:
    exe = cli()
    if not exe.is_file():
        raise LoginError(f"the hanzo CLI is not installed at {exe}")
    try:
        out = subprocess.run(
            [str(exe), *args], capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise LoginError(f"the hanzo CLI did not run: {e}") from None
    if out.returncode != 0:
        said = next((line.strip() for line in out.stderr.splitlines() if line.strip()), "")
        raise LoginError(said[:300] or f"hanzo {' '.join(args)} exited {out.returncode}")
    return out.stdout


def token(identity: str | None = None) -> str:
    """The login's access token: the active identity's, or ``identity``'s without making it active."""
    if identity:
        valid(identity)
    key = identity or ""
    now = _now()
    hit = _tokens.get(key)
    if hit and hit[0] > now:
        return hit[1]
    no = _refusals.get(key)
    if no and no[0] > now:
        raise LoginError(no[1])
    try:
        out = _run("auth", "token", *(["--as", identity] if identity else [])).strip()
        if not out or any(ch.isspace() for ch in out):
            raise LoginError("hanzo auth token did not print one token")
    except LoginError as e:
        _tokens.pop(key, None)
        _refusals[key] = (now + REFUSAL_TTL, str(e))
        raise
    _refusals.pop(key, None)
    exp = (claims(out) or {}).get("exp")
    ttl = TTL if not isinstance(exp, (int, float)) else max(0.0, min(TTL, exp - time.time() - SKEW))
    _tokens[key] = (now + ttl, out)
    return out


def forget(identity: str | None = None) -> None:
    """Drop the kept token for ``identity`` (the active one when None); every one when called bare."""
    if identity is None:
        _tokens.clear()
        _refusals.clear()
    else:
        _tokens.pop(identity, None)
        _refusals.pop(identity, None)


def identities() -> list[dict[str, Any]]:
    """The CLI's identities: ``key``, ``owner``, ``subject``, ``expiry``, ``active``. No secrets."""
    try:
        rows = json.loads(_run("auth", "list", "-o", "json"))
    except ValueError:
        raise LoginError("hanzo auth list did not print JSON") from None
    if not isinstance(rows, list):
        raise LoginError("hanzo auth list did not print a list")
    return [
        {k: row[k] for k in _FIELDS if k in row}
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("key"), str)
    ]


def switch(identity: str) -> None:
    """Make ``identity`` the CLI's active one, for the whole machine."""
    _run("auth", "switch", valid(identity))
    forget()


def using() -> str | None:
    """The identity chosen with ``use`` in this process, or None."""
    return _using


def use(identity: str | None) -> None:
    """Act as ``identity`` in this process only; None clears.

    The login is asked for it first, so an identity it does not hold is refused and the
    choice stays as it was.
    """
    global _using
    if identity:
        forget(identity)
        token(identity)
    _using = identity or None


def credential(identity: str | None = None) -> Credential:
    """Who to act as. LoginError when an identity was named and the login will not give it."""
    named = identity or _using
    if named:
        return Credential("login", token(named), named)
    key = (os.environ.get("HANZO_API_KEY") or os.environ.get("HANZO_KEY") or "").strip()
    if key:
        return Credential("env", key)
    refused = None
    try:
        return Credential("login", token())
    except LoginError as e:
        refused = str(e)
    key = _stored()
    return Credential("stored" if key else None, key, None, refused)


def _stored() -> str:
    try:
        key = json.loads((Path.home() / ".hanzo" / "config.json").read_text()).get("apiKey")
    except (OSError, ValueError, AttributeError):
        return ""
    return str(key).strip() if key else ""


def claims(tok: str) -> dict[str, Any] | None:
    """A JWT's claims, read without verifying it (the server does); None for a token that is not a JWT."""
    parts = tok.split(".")
    if len(parts) != 3:
        return None
    try:
        out = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    except (ValueError, binascii.Error):
        return None
    return out if isinstance(out, dict) else None


def describe(identity: str | None = None) -> dict[str, Any]:
    """Which source answered and who it is. Never a token or a key, only a key's prefix."""
    cred = credential(identity)
    out: dict[str, Any] = {"source": cred.source, "using": _using}
    if cred.secret:
        c = claims(cred.secret)
        if c is not None:
            if cred.source == "login":
                out["identity"] = cred.identity or _active(c)
            out["email"] = c.get("email")
            out["name"] = c.get("displayName") or c.get("name")
            out["org"] = c.get("owner")
            out["orgs"] = c["orgs"] if isinstance(c.get("orgs"), list) else []
        else:
            match = _KEY_PREFIX.match(cred.secret)
            out["key"] = (match.group(0) if match else "") + "…"
    if cred.refused:
        out["login"] = cred.refused
    return out


def _active(c: dict[str, Any]) -> str | None:
    """The active identity's key: the CLI's ``active`` row, else the token's owner/name."""
    try:
        for row in identities():
            if row.get("active"):
                return row["key"]
    except LoginError:
        pass
    owner, name = c.get("owner"), c.get("name")
    return f"{owner}/{name}" if owner and name else None
