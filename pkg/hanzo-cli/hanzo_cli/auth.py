"""Authentication and token management for Hanzo CLI.

Credential chain:
1. HANZO_IAM_CLIENT_ID + HANZO_IAM_CLIENT_SECRET env vars
2. ~/.hanzo/auth/token.json from `hanzo login`
3. Exit with help message
"""

from __future__ import annotations

import http.server
import json
import os
import secrets
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import click
from hanzo_iam import IAMClient, IAMConfig

TOKEN_DIR = Path.home() / ".hanzo" / "auth"
TOKEN_FILE = TOKEN_DIR / "token.json"

DEFAULT_IAM_URL = "https://hanzo.id"
DEFAULT_ORG = "hanzo"
DEFAULT_APP = "app-hanzo"
DEFAULT_CLIENT_ID = "hanzo-app-client-id"
CALLBACK_PORT = 8399
CALLBACK_PATH = "/callback"


def _save_token(data: dict[str, Any]) -> None:
    """Save token data to disk."""
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data, indent=2))
    TOKEN_FILE.chmod(0o600)


def _load_token() -> dict[str, Any] | None:
    """Load stored token from disk."""
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _clear_token() -> None:
    """Remove stored token."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def _iam_url() -> str:
    return os.getenv("HANZO_IAM_URL") or os.getenv("IAM_URL") or DEFAULT_IAM_URL


def _iam_org() -> str:
    return os.getenv("HANZO_IAM_ORG") or os.getenv("IAM_ORG") or DEFAULT_ORG


def _iam_app() -> str:
    return os.getenv("HANZO_IAM_APP") or os.getenv("IAM_APP") or DEFAULT_APP


def _iam_client_id() -> str:
    return os.getenv("IAM_CLIENT_ID") or os.getenv("HANZO_IAM_CLIENT_ID") or DEFAULT_CLIENT_ID


def get_client(ctx: click.Context | None = None) -> IAMClient:
    """Build an IAMClient using the credential chain.

    1. Env vars HANZO_IAM_CLIENT_ID + HANZO_IAM_CLIENT_SECRET
    2. Stored bearer token from `hanzo login`
    3. Exit with instructions
    """
    client_id = os.getenv("IAM_CLIENT_ID") or os.getenv("HANZO_IAM_CLIENT_ID") or ""
    client_secret = os.getenv("IAM_CLIENT_SECRET") or os.getenv("HANZO_IAM_CLIENT_SECRET") or ""

    if client_id and client_secret:
        config = IAMConfig(
            server_url=_iam_url(),
            client_id=client_id,
            client_secret=client_secret,
            organization=_iam_org(),
            application=_iam_app(),
        )
        return IAMClient(config=config)

    # Try stored token
    token_data = _load_token()
    if token_data and token_data.get("access_token"):
        config = IAMConfig(
            server_url=token_data.get("server_url", _iam_url()),
            client_id=token_data.get("client_id", ""),
            client_secret="",
            organization=token_data.get("organization", _iam_org()),
            application=token_data.get("application", _iam_app()),
        )
        return IAMClient(
            config=config,
            bearer_token=token_data["access_token"],
        )

    click.echo(
        "Not authenticated. Run 'hanzo login' or set HANZO_IAM_CLIENT_ID"
        " + HANZO_IAM_CLIENT_SECRET environment variables.",
        err=True,
    )
    sys.exit(1)


def get_token_info() -> dict[str, Any] | None:
    """Return stored token info for whoami."""
    return _load_token()


# =========================================================================
# Browser OAuth Login Flow
# =========================================================================


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback code."""

    code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)

        if "error" in qs:
            _OAuthCallbackHandler.error = qs["error"][0]
            self._respond("Login failed. You can close this window.", success=False)
            return

        _OAuthCallbackHandler.code = qs.get("code", [None])[0]
        _OAuthCallbackHandler.state = qs.get("state", [None])[0]
        self._respond("Login successful! You can close this window.")

    def _respond(self, message: str, success: bool = True) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        accent = "#6C5CE7" if success else "#e74c3c"
        body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hanzo</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    background:#0a0a0a;color:#fafafa;
    display:flex;align-items:center;justify-content:center;
    min-height:100vh;
  }}
  .card{{
    text-align:center;max-width:420px;padding:48px 32px;
    background:#111;border:1px solid #222;border-radius:16px;
  }}
  .logo{{font-size:28px;font-weight:700;letter-spacing:-.5px;margin-bottom:32px;color:#fff}}
  .logo span{{color:{accent}}}
  .icon{{font-size:48px;margin-bottom:20px}}
  h2{{font-size:20px;font-weight:600;margin-bottom:8px;color:#fff}}
  .sub{{color:#888;font-size:14px;line-height:1.5;margin-bottom:28px}}
  .tagline{{
    font-size:13px;color:#555;border-top:1px solid #222;
    padding-top:20px;margin-top:8px;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="logo"><span>&#x25B2;</span> hanzo</div>
  <div class="icon">{"&#x2705;" if success else "&#x274C;"}</div>
  <h2>{message}</h2>
  <p class="sub">You can close this window and return to your terminal.</p>
  <p class="tagline">Build something you love.</p>
</div>
</body>
</html>"""
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default request logging."""


def browser_login(port: int = CALLBACK_PORT) -> dict[str, Any]:
    """Run the browser OAuth login flow.

    Opens the user's browser to the IAM login page, starts a local HTTP
    server to receive the callback, exchanges the code for tokens.

    Returns:
        Token data dict with access_token, etc.
    """
    server_url = _iam_url()
    org = _iam_org()
    app = _iam_app()
    client_id = _iam_client_id()

    config = IAMConfig(
        server_url=server_url,
        client_id=client_id,
        client_secret="",
        organization=org,
        application=app,
    )
    client = IAMClient(config=config)

    redirect_uri = f"http://localhost:{port}{CALLBACK_PATH}"
    state = secrets.token_urlsafe(32)

    auth_url = client.get_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        scope="openid profile email",
    )

    # Reset handler state
    _OAuthCallbackHandler.code = None
    _OAuthCallbackHandler.state = None
    _OAuthCallbackHandler.error = None

    server = http.server.HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
    server.timeout = 120  # 2 minute timeout

    click.echo(f"Opening browser to login at {server_url}...")
    webbrowser.open(auth_url)
    click.echo(f"Waiting for callback on http://localhost:{port}{CALLBACK_PATH}")

    # Handle one request (the callback)
    while _OAuthCallbackHandler.code is None and _OAuthCallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    if _OAuthCallbackHandler.error:
        raise click.ClickException(f"Login failed: {_OAuthCallbackHandler.error}")

    if _OAuthCallbackHandler.state != state:
        raise click.ClickException("State mismatch — possible CSRF attack.")

    code = _OAuthCallbackHandler.code
    if not code:
        raise click.ClickException("No authorization code received.")

    # Exchange code for tokens
    tokens = client.exchange_code(code=code, redirect_uri=redirect_uri)
    client.close()

    token_data = {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "id_token": tokens.id_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
        "scope": tokens.scope,
        "server_url": server_url,
        "client_id": client_id,
        "organization": org,
        "application": app,
        "login_time": int(time.time()),
    }

    _save_token(token_data)
    return token_data


# =========================================================================
# Password Login Flow (--no-browser)
# =========================================================================


def password_login(username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """Login with username/password (no browser).

    Uses the OAuth2 Resource Owner Password Credentials (ROPC) grant
    to get a JWT directly from the token endpoint.

    Returns:
        Token data dict with access_token, etc.
    """
    import httpx

    server_url = _iam_url()
    org = _iam_org()
    app = _iam_app()
    client_id = _iam_client_id()
    client_secret = os.getenv("IAM_CLIENT_SECRET") or os.getenv("HANZO_IAM_CLIENT_SECRET") or ""

    if not username:
        username = click.prompt("Username or email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    # Use ROPC grant to get tokens directly
    resp = httpx.post(
        f"{server_url}/api/login/oauth/access_token",
        data={
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "scope": "openid profile email",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )

    data = resp.json()

    if "error" in data:
        raise click.ClickException(data.get("error_description", data["error"]))

    access_token = data.get("access_token", "")
    if not access_token:
        raise click.ClickException("No access token in response")

    token_data = {
        "access_token": access_token,
        "refresh_token": data.get("refresh_token", ""),
        "id_token": data.get("id_token", ""),
        "token_type": data.get("token_type", "Bearer"),
        "expires_in": data.get("expires_in", 0),
        "scope": data.get("scope", ""),
        "server_url": server_url,
        "client_id": client_id,
        "organization": org,
        "application": app,
        "login_time": int(time.time()),
    }

    _save_token(token_data)
    return token_data


def logout() -> None:
    """Clear stored credentials."""
    _clear_token()
