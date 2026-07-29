"""Tests for hanzo_iam.oauth — the loopback + PKCE login flow.

These pin the four things that made the previous flow unusable:
  * it posted to /oauth/token, which hanzo.id answers with a 200 HTML page
  * it sent no PKCE, so the exchange needed a client secret a CLI cannot hold
  * it looped on handle_request() with no deadline and hung forever
  * it bound a port nobody had registered as a redirect_uri
"""

from __future__ import annotations

import base64
import hashlib
import socket
import threading
import time
import urllib.parse
import urllib.request

import httpx
import pytest

from hanzo_iam import IAMError, oauth

ISSUER = "https://hanzo.id"


def _params(url: str) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# --- Endpoint paths -------------------------------------------------------


def test_authorize_url_carries_the_v1_iam_prefix():
    """Unprefixed /oauth/authorize is the SPA, not the endpoint."""
    url = oauth.authorize_url(ISSUER, "hanzo-app", "http://localhost:3000/callback", "st", "ch")
    assert url.startswith(f"{ISSUER}/v1/iam/oauth/authorize?")


def test_authorize_url_is_a_complete_pkce_request():
    url = oauth.authorize_url(ISSUER, "hanzo-app", "http://localhost:3000/callback", "st", "ch")
    q = _params(url)
    assert q["response_type"] == "code"
    assert q["client_id"] == "hanzo-app"
    assert q["code_challenge"] == "ch"
    assert q["code_challenge_method"] == "S256"
    assert q["state"] == "st"
    assert q["redirect_uri"] == "http://localhost:3000/callback"


def test_registered_redirect_uris_are_bindable_by_a_normal_user():
    """iam matches redirect_uri by exact string and does NOT apply RFC 8252
    §7.3 port-agnostic loopback matching, so the CLI must use a registered URI
    — and a privileged port would make the flow root-only."""
    for uri in oauth.LOOPBACK_REDIRECTS:
        parsed = urllib.parse.urlparse(uri)
        assert parsed.hostname in ("localhost", "127.0.0.1")
        assert parsed.port is not None, f"{uri} has no port; port 80 needs root"
        assert parsed.port >= 1024, f"{uri} is a privileged port"


# --- PKCE -----------------------------------------------------------------


def test_pkce_challenge_is_s256_of_the_verifier():
    p = oauth._Pkce.generate()
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(p.verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode()
    assert p.challenge == expected


def test_pkce_verifier_meets_rfc7636_length_and_alphabet():
    p = oauth._Pkce.generate()
    assert 43 <= len(p.verifier) <= 128
    assert set(p.verifier) <= set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    )


def test_pkce_is_fresh_every_time():
    assert oauth._Pkce.generate().verifier != oauth._Pkce.generate().verifier


# --- Token exchange -------------------------------------------------------


class _Capture:
    def __init__(self, status=200, json_body=None, content_type="application/json", text=""):
        self.status, self.body, self.ctype, self.text = status, json_body, content_type, text
        self.sent: dict = {}

    def __call__(self, url, data=None, headers=None, timeout=None):
        self.sent = {"url": url, "data": data}
        req = httpx.Request("POST", url)
        return httpx.Response(
            self.status,
            headers={"content-type": self.ctype},
            json=self.body if self.body is not None else None,
            text=None if self.body is not None else self.text,
            request=req,
        )


def test_exchange_posts_to_the_prefixed_token_endpoint(monkeypatch):
    cap = _Capture(json_body={"access_token": "a.b.c", "expires_in": 3600})
    monkeypatch.setattr(httpx, "post", cap)
    oauth.exchange_code(ISSUER, "hanzo-app", "code", "http://localhost:3000/callback", "verif")
    assert cap.sent["url"] == f"{ISSUER}/v1/iam/oauth/token"


def test_exchange_sends_the_verifier_and_no_client_secret(monkeypatch):
    """PKCE is the proof. A CLI cannot hold a secret, and shipping one would
    not be a secret."""
    cap = _Capture(json_body={"access_token": "a.b.c"})
    monkeypatch.setattr(httpx, "post", cap)
    oauth.exchange_code(ISSUER, "hanzo-app", "code", "http://localhost:3000/callback", "verif")
    assert cap.sent["data"]["code_verifier"] == "verif"
    assert cap.sent["data"]["grant_type"] == "authorization_code"
    assert "client_secret" not in cap.sent["data"]


def test_html_response_is_diagnosed_as_a_wrong_path(monkeypatch):
    """hanzo.id serves the sign-in SPA with 200 text/html on any unmatched
    path. The old client called .json() on it and raised JSONDecodeError,
    hiding a wrong URL behind a parse error."""
    monkeypatch.setattr(httpx, "post", _Capture(content_type="text/html", text="<!doctype html>"))
    with pytest.raises(IAMError, match="wrong path"):
        oauth.exchange_code(ISSUER, "hanzo-app", "c", "http://localhost:3000/callback", "v")


def test_oauth_error_body_is_surfaced_verbatim(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        _Capture(
            status=400,
            json_body={"error": "invalid_grant", "error_description": "code expired"},
        ),
    )
    with pytest.raises(IAMError, match="invalid_grant.*code expired"):
        oauth.exchange_code(ISSUER, "hanzo-app", "c", "http://localhost:3000/callback", "v")


def test_missing_access_token_is_an_error_not_a_silent_success(monkeypatch):
    monkeypatch.setattr(httpx, "post", _Capture(json_body={"token_type": "Bearer"}))
    with pytest.raises(IAMError, match="no access_token"):
        oauth.exchange_code(ISSUER, "hanzo-app", "c", "http://localhost:3000/callback", "v")


# --- The loopback listener ------------------------------------------------


def test_listener_times_out_instead_of_hanging_forever():
    """THE liveness regression. The shipped flow was

        while handler.code is None and handler.error is None:
            server.handle_request()

    with no deadline: a user who closed the browser tab wedged the CLI until
    it was killed. This must return promptly instead.
    """
    port = _free_port()
    listener = oauth._Listener(port, "/callback")
    try:
        started = time.monotonic()
        result = listener.wait(timeout=0.5)
        assert time.monotonic() - started < 5
        assert result.code is None
    finally:
        listener.close()


def test_listener_captures_code_and_state():
    port = _free_port()
    listener = oauth._Listener(port, "/callback")
    try:
        def knock():
            time.sleep(0.1)
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}/callback?code=abc123&state=xyz", timeout=5
            ).read()

        threading.Thread(target=knock, daemon=True).start()
        result = listener.wait(timeout=10)
        assert result.code == "abc123"
        assert result.state == "xyz"
    finally:
        listener.close()


def test_listener_captures_an_authorization_error():
    port = _free_port()
    listener = oauth._Listener(port, "/callback")
    try:
        def knock():
            time.sleep(0.1)
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}/callback?error=access_denied"
                "&error_description=user+said+no",
                timeout=5,
            ).read()

        threading.Thread(target=knock, daemon=True).start()
        result = listener.wait(timeout=10)
        assert result.error == "access_denied"
        assert result.error_description == "user said no"
    finally:
        listener.close()


def test_listener_releases_its_port_on_close():
    port = _free_port()
    oauth._Listener(port, "/callback").close()
    listener = oauth._Listener(port, "/callback")  # would raise if still held
    listener.close()


def test_binding_reports_which_ports_were_busy():
    """Every candidate port occupied — the user needs to know which and why,
    not a bare failure. Ports 3000 and 8080 really are usually taken."""
    uris = tuple(f"http://localhost:{_free_port()}/callback" for _ in range(2))
    held = []
    try:
        for uri in uris:
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", urllib.parse.urlparse(uri).port))
            s.listen(1)
            held.append(s)

        with pytest.raises(IAMError) as e:
            oauth._bind_registered(uris)
        for uri in uris:
            assert uri in str(e.value)
    finally:
        for s in held:
            s.close()


def test_a_second_login_is_not_blocked_by_time_wait():
    """The callback socket lingers in TIME_WAIT for ~60s. Without SO_REUSEADDR
    a user who runs `login` twice in a minute gets EADDRINUSE on a port nothing
    is actually using."""
    port = _free_port()
    for _ in range(2):
        listener = oauth._Listener(port, "/callback")
        try:
            def knock():
                time.sleep(0.05)
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/callback?code=c&state=s", timeout=5
                ).read()

            threading.Thread(target=knock, daemon=True).start()
            assert listener.wait(timeout=10).code == "c"
        finally:
            listener.close()


# --- End to end -----------------------------------------------------------


@pytest.fixture
def free_redirect():
    """A redirect URI on a port nothing else holds.

    The real registered URIs are ports 3000 and 8080 — the two most contended
    ports on any developer box (8080 is taken by hanzoai/cloud on this one), so
    a flow test that used them would be testing port luck. The registered URIs
    are asserted separately by
    test_registered_redirect_uris_are_bindable_by_a_normal_user.
    """
    return (f"http://localhost:{_free_port()}/callback",)


def _drive_login(monkeypatch, respond, exchange=None):
    """Run login() while a fake browser hits the callback."""
    seen: dict = {}

    def fake_open(url):
        seen["url"] = url
        threading.Thread(target=lambda: respond(url), daemon=True).start()
        return True

    monkeypatch.setattr(oauth.webbrowser, "open", fake_open)
    monkeypatch.setattr(
        httpx, "post", exchange or _Capture(json_body={"access_token": "a.b.c", "expires_in": 60})
    )
    return seen


def test_login_end_to_end(monkeypatch, free_redirect):
    def respond(url):
        q = _params(url)
        time.sleep(0.1)
        urllib.request.urlopen(
            f"{q['redirect_uri']}?code=THECODE&state={q['state']}", timeout=5
        ).read()

    seen = _drive_login(monkeypatch, respond)
    result = oauth.login(timeout=15, redirect_uris=free_redirect)

    assert result["access_token"] == "a.b.c"
    assert result["client_id"] == oauth.DEFAULT_CLIENT_ID
    assert result["expires_at"] >= result["login_time"]
    assert _params(seen["url"])["code_challenge_method"] == "S256"


def test_login_rejects_a_mismatched_state(monkeypatch, free_redirect):
    """A code that arrives with someone else's state is a CSRF attempt, and
    must never be redeemed."""
    exchanged = []

    def respond(url):
        q = _params(url)
        time.sleep(0.1)
        urllib.request.urlopen(
            f"{q['redirect_uri']}?code=INJECTED&state=attacker", timeout=5
        ).read()

    def never(*a, **kw):
        exchanged.append(a)
        raise AssertionError("must not exchange a code with a bad state")

    _drive_login(monkeypatch, respond, exchange=never)
    with pytest.raises(IAMError, match="state mismatch"):
        oauth.login(timeout=15, redirect_uris=free_redirect)
    assert exchanged == []


def test_login_surfaces_an_idp_error(monkeypatch, free_redirect):
    def respond(url):
        q = _params(url)
        time.sleep(0.1)
        urllib.request.urlopen(
            f"{q['redirect_uri']}?error=access_denied&error_description=nope", timeout=5
        ).read()

    _drive_login(monkeypatch, respond)
    with pytest.raises(IAMError, match="access_denied"):
        oauth.login(timeout=15, redirect_uris=free_redirect)


def test_login_gives_up_rather_than_hanging(monkeypatch, free_redirect):
    monkeypatch.setattr(oauth.webbrowser, "open", lambda url: True)
    started = time.monotonic()
    with pytest.raises(IAMError, match="no authorization code received"):
        oauth.login(timeout=0.5, redirect_uris=free_redirect)
    assert time.monotonic() - started < 10


def test_login_can_hand_the_url_to_the_caller(monkeypatch, free_redirect):
    """For a user whose browser is not on this machine."""
    urls: list[str] = []
    monkeypatch.setattr(oauth.webbrowser, "open", lambda url: True)
    with pytest.raises(IAMError):
        oauth.login(timeout=0.3, open_browser=False, on_url=urls.append,
                    redirect_uris=free_redirect)
    assert urls and urls[0].startswith(f"{ISSUER}/v1/iam/oauth/authorize?")
