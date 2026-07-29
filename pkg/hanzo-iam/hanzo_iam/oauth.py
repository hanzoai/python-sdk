"""The ONE interactive login flow: loopback redirect + PKCE (RFC 8252 / 7636).

WHY NOT THE DEVICE GRANT (RFC 8628), which would be the better CLI UX:
iam implements it fully and advertises it in discovery, but no PUBLIC client is
registered. `internal/oidc/device.go` demands a client secret from any app whose
ClientSecret is non-empty, and every registered app has one, so
``POST /v1/iam/oauth/device`` answers 401 invalid_client for hanzo-cli,
hanzo-app, hanzo-cloud and hanzo-console alike. A CLI cannot fix that by
shipping an embedded secret — that is not a secret. Registering ONE public
app (empty ClientSecret, device_code in grantTypes) is the whole server-side
change; until then this module is the only flow that can actually complete, and
shipping a device path that always 401s would be a lie in code form.

The password grant is also out: it requires client authentication too
(verified: 401 invalid_client without a secret), and ROPC cannot carry SSO or
MFA regardless.

The loopback flow works today because the token endpoint authenticates a
PKCE-bound code by the code binding rather than by a client secret when the
client presents none (iam v1.33.26, internal/oidc/token.go) — the same
relaxation that lets the hanzo.chat and cloud.hanzo.ai SPAs sign in.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import os
import secrets
import selectors
import socket
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Any, cast

import httpx

from hanzo_iam.models import OIDC_AUTHORIZE_PATH, OIDC_TOKEN_PATH
from hanzo_iam.response import IAMError, decode

DEFAULT_IAM_URL = "https://hanzo.id"
DEFAULT_CLIENT_ID = "hanzo-app"
DEFAULT_ORG = "hanzo"
DEFAULT_SCOPE = "openid profile email"

# Loopback redirect URIs registered for DEFAULT_CLIENT_ID, in preference order.
# iam matches redirect_uri by EXACT STRING (internal/schema/application.go
# IsRedirectUriValid) — it does NOT apply the RFC 8252 §7.3 rule that a loopback
# port is ignored. So the CLI cannot pick a free ephemeral port; it must bind one
# of these exact URIs, host spelling included ("localhost", not "127.0.0.1").
LOOPBACK_REDIRECTS = (
    "http://localhost:3000/callback",
    "http://localhost:8080/callback",
)

DEFAULT_TIMEOUT = 300.0


@dataclass(frozen=True)
class _Pkce:
    verifier: str
    challenge: str

    @classmethod
    def generate(cls) -> _Pkce:
        verifier = _b64url(os.urandom(32))
        challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
        return cls(verifier, challenge)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def authorize_url(
    server_url: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    challenge: str,
    scope: str = DEFAULT_SCOPE,
) -> str:
    """Build the /authorize URL for a PKCE loopback login."""
    q = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{server_url.rstrip('/')}{OIDC_AUTHORIZE_PATH}?{q}"


def exchange_code(
    server_url: str,
    client_id: str,
    code: str,
    redirect_uri: str,
    verifier: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Redeem an authorization code. No client secret: PKCE is the proof.

    Raises IAMError with the server's own words on failure — including when the
    response is not JSON at all, which is what a wrong path looks like here.
    That gate is `hanzo_iam.response.decode`, applied by every surface now; it
    used to live only in this module.
    """
    payload = _token_grant(
        server_url,
        {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
        timeout,
    )
    if not payload.get("access_token"):
        raise IAMError("token endpoint returned no access_token")
    return payload


def refresh(
    server_url: str,
    client_id: str,
    refresh_token: str,
    client_secret: str = "",
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Exchange a refresh token for a fresh access token.

    Lives here, with the rest of the token endpoint. `IAMClient.refresh_token`
    was the second implementation — same endpoint, different module, and it
    always sent `client_secret` even for the public client the loopback flow
    logs in as. A public client has no secret to send; `""` in the form is
    noise that invites someone to "fix" it by embedding one.
    """
    form = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    if client_secret:
        form["client_secret"] = client_secret
    payload = _token_grant(server_url, form, timeout)
    if not payload.get("access_token"):
        raise IAMError("token endpoint returned no access_token")
    return payload


def _token_grant(server_url: str, form: dict[str, str], timeout: float) -> dict[str, Any]:
    """POST one grant to the ONE token endpoint and decode the reply."""
    resp = httpx.post(
        f"{server_url.rstrip('/')}{OIDC_TOKEN_PATH}",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=timeout,
    )
    return cast("dict[str, Any]", decode(resp, "token endpoint"))


def login(
    server_url: str = DEFAULT_IAM_URL,
    client_id: str = DEFAULT_CLIENT_ID,
    organization: str = DEFAULT_ORG,
    scope: str = DEFAULT_SCOPE,
    redirect_uris: tuple[str, ...] = LOOPBACK_REDIRECTS,
    timeout: float = DEFAULT_TIMEOUT,
    open_browser: bool = True,
    on_url: Any = None,
) -> dict[str, Any]:
    """Run the loopback+PKCE login and return token data. Does NOT persist it.

    Persisting is `hanzo_iam.store.save`'s job — keeping them apart is what lets
    a caller verify before it writes.

    Args:
        on_url: Optional callable receiving the authorize URL, so a CLI can
            print it for a user whose browser is elsewhere.

    Raises:
        IAMError: with an actionable message on every failure path. It always
            terminates — the flow this replaces looped on `handle_request()`
            with no deadline and hung forever.
    """
    pkce = _Pkce.generate()
    state = secrets.token_urlsafe(32)

    server, redirect_uri = _bind_registered(redirect_uris)
    url = authorize_url(server_url, client_id, redirect_uri, state, pkce.challenge, scope)

    try:
        if on_url is not None:
            on_url(url)
        if open_browser:
            webbrowser.open(url)
        result = server.wait(timeout)
    finally:
        server.close()

    if result.error:
        raise IAMError(f"authorization failed: {result.error} — {result.error_description}")
    if not result.code:
        raise IAMError(
            f"no authorization code received within {timeout:.0f}s at {redirect_uri}"
        )
    # Constant-time-ish state compare. A mismatch means the code arrived from a
    # request this process did not start (RFC 6749 §10.12).
    if not secrets.compare_digest(result.state or "", state):
        raise IAMError("state mismatch — discarding the response (possible CSRF)")

    tokens = exchange_code(server_url, client_id, result.code, redirect_uri, pkce.verifier)
    now = int(time.time())
    return {
        **tokens,
        "server_url": server_url.rstrip("/"),
        "client_id": client_id,
        "organization": organization,
        "login_time": now,
        "expires_at": now + int(tokens.get("expires_in") or 0),
    }


# ---------------------------------------------------------------------------
# Loopback listener
# ---------------------------------------------------------------------------


@dataclass
class _Callback:
    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str = ""


_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Hanzo</title>
<style>body{{font-family:system-ui,sans-serif;background:#0a0a0a;color:#fafafa;
display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.c{{text-align:center;padding:48px 32px;border:1px solid #222;border-radius:16px;background:#111}}
h2{{margin:0 0 8px;font-size:20px}}p{{color:#888;font-size:14px;margin:0}}</style>
</head><body><div class="c"><h2>{title}</h2><p>{sub}</p></div></body></html>"""


def _bind_registered(uris: tuple[str, ...]) -> tuple[_Listener, str]:
    """Bind the first registered redirect URI whose port is free.

    Only registered URIs are candidates: an unregistered one is refused by
    /authorize with a bare 400 before the user ever sees a login page.
    """
    busy = []
    for uri in uris:
        parsed = urllib.parse.urlparse(uri)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            return _Listener(port, parsed.path or "/"), uri
        except OSError as e:
            busy.append(f"{uri} ({e.strerror or e})")
    raise IAMError(
        "no registered loopback redirect URI could be bound: "
        + "; ".join(busy)
        + ". Free one of those ports, or register another loopback redirect_uri"
        " on the IAM application."
    )


class _Listener:
    """A one-shot loopback HTTP listener on both 127.0.0.1 and ::1.

    Both families are bound because the registered URIs spell the host
    "localhost", and a browser may resolve that to either. Binding only one
    turns a working login into an intermittent one.
    """

    def __init__(self, port: int, path: str) -> None:
        self.result = _Callback()
        self.path = path
        self._servers: list[http.server.HTTPServer] = []
        self._sel = selectors.DefaultSelector()

        handler = _make_handler(self)
        first_error: OSError | None = None
        for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            try:
                self._servers.append(_serve(family, host, port, handler))
            except OSError as e:
                # IPv4 must succeed; a box without ::1 is normal and fine.
                if family == socket.AF_INET:
                    first_error = e
        if first_error is not None or not self._servers:
            self.close()
            raise first_error or OSError(f"could not bind port {port}")
        for s in self._servers:
            self._sel.register(s, selectors.EVENT_READ)

    def wait(self, timeout: float) -> _Callback:
        """Serve until the callback lands or the deadline passes. Never blocks
        forever — an unbounded wait is what made the previous flow unusable."""
        deadline = time.monotonic() + timeout
        while self.result.code is None and self.result.error is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            for key, _ in self._sel.select(timeout=min(remaining, 1.0)):
                key.fileobj.handle_request()  # type: ignore[union-attr]
        return self.result

    def close(self) -> None:
        for s in self._servers:
            s.server_close()
        self._servers.clear()
        self._sel.close()


def _serve(family: int, host: str, port: int, handler: Any) -> http.server.HTTPServer:
    class Server(http.server.HTTPServer):
        address_family = family
        # SO_REUSEADDR is required, not convenience: the previous callback
        # connection sits in TIME_WAIT for ~60s, so without it a second `login`
        # in the same minute dies with EADDRINUSE on a port nothing is using.
        # It does NOT let another process steal a live listener — two sockets
        # on the same concrete addr:port still need SO_REUSEPORT, which we
        # never set.
        allow_reuse_address = True

    return Server((host, port), handler)


def _make_handler(listener: _Listener) -> Any:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != listener.path:
                self.send_error(404)
                return
            q = urllib.parse.parse_qs(parsed.query)
            if "error" in q:
                listener.result.error = q["error"][0]
                listener.result.error_description = q.get("error_description", [""])[0]
                self._page("Login failed", listener.result.error_description or "Return to your terminal.")
                return
            listener.result.code = q.get("code", [None])[0]
            listener.result.state = q.get("state", [None])[0]
            if not listener.result.code:
                listener.result.error = "invalid_request"
                listener.result.error_description = "callback carried no code"
            self._page("Signed in", "You can close this window and return to your terminal.")

        def _page(self, title: str, sub: str) -> None:
            body = _PAGE.format(title=title, sub=sub).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:
            """Silence: the access log would print the authorization code."""

    return Handler
