"""Authentication and token management for Hanzo CLI.

This module is a thin adapter over `hanzo_iam` — the ONE implementation of the
login flow (`hanzo_iam.oauth`), the token store (`hanzo_iam.store`) and token
verification (`hanzo_iam.tokens`). It used to carry a second, divergent copy of
all three; the copy posted to the unprefixed /oauth/token (a 200 HTML page on
hanzo.id), sent no PKCE, and waited for its callback in an unbounded loop.

Credential chain:
1. IAM_CLIENT_ID + IAM_CLIENT_SECRET env vars (machine-to-machine)
2. The stored token from `hanzo login`
3. Exit with help
"""

from __future__ import annotations

import os
import sys
from typing import Any

import click
from hanzo_iam import IAMClient, IAMConfig, oauth, store, tokens
from hanzo_iam.models import OIDC_JWKS_PATH

DEFAULT_IAM_URL = oauth.DEFAULT_IAM_URL
DEFAULT_ORG = oauth.DEFAULT_ORG
DEFAULT_APP = "hanzo-app"
DEFAULT_CLIENT_ID = oauth.DEFAULT_CLIENT_ID

TOKEN_FILE = store.TOKEN_FILE


def _save_token(data: dict[str, Any]) -> str:
    return store.save(data)


def _load_token() -> dict[str, Any] | None:
    return store.load()


def _clear_token() -> None:
    store.clear()


def _env(name: str) -> str:
    """Read env var (IAM_*)."""
    return os.getenv(name) or ""


def _iam_url() -> str:
    return _env("IAM_URL") or DEFAULT_IAM_URL


def _iam_org() -> str:
    return _env("IAM_ORG") or DEFAULT_ORG


def _iam_app() -> str:
    return _env("IAM_APP") or DEFAULT_APP


def _iam_client_id() -> str:
    return _env("IAM_CLIENT_ID") or DEFAULT_CLIENT_ID


def get_client(ctx: click.Context | None = None) -> IAMClient:
    """Build an IAMClient using the credential chain.

    1. Env vars IAM_CLIENT_ID + IAM_CLIENT_SECRET
    2. Stored bearer token from `hanzo login`
    3. Exit with instructions
    """
    client_id = _env("IAM_CLIENT_ID")
    client_secret = _env("IAM_CLIENT_SECRET")

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
        "Not authenticated. Run 'hanzo login' or set IAM_CLIENT_ID"
        " + IAM_CLIENT_SECRET environment variables.",
        err=True,
    )
    sys.exit(1)


def get_token_info() -> dict[str, Any] | None:
    """Return stored token info for whoami."""
    return _load_token()




def verify_token_data(data: dict[str, Any] | None) -> tokens.Verification:
    """Judge a token dict — stored or freshly issued. The ONE verification seam
    for this CLI, so `whoami`, `login` and every command agree on what valid
    means."""
    if not data or not data.get("access_token"):
        return tokens.Verification(False, tokens.NO_CREDENTIAL, "no credential found")
    server_url = (data.get("server_url") or _iam_url()).rstrip("/")
    return tokens.verify(
        data["access_token"],
        jwks_uri=f"{server_url}{OIDC_JWKS_PATH}",
        issuer=server_url,
    )


def verify_token() -> tokens.Verification:
    """Judge the stored credential."""
    return verify_token_data(_load_token())


def browser_login(port: int | None = None, open_browser: bool = True) -> dict[str, Any]:
    """Sign in through the browser (authorization code + PKCE) and store it.

    `port` selects among the redirect URIs registered on the IAM application.
    It cannot be an arbitrary port: iam compares redirect_uri by exact string,
    so an unregistered one is refused with a bare 400 before the user ever sees
    a login page.
    """
    uris = oauth.LOOPBACK_REDIRECTS
    if port is not None:
        wanted = [u for u in uris if f":{port}/" in u]
        if not wanted:
            raise click.ClickException(
                f"Port {port} is not a registered redirect URI. Registered: "
                + ", ".join(uris)
            )
        uris = tuple(wanted)

    token_data = oauth.login(
        server_url=_iam_url(),
        client_id=_iam_client_id(),
        organization=_iam_org(),
        redirect_uris=uris,
        open_browser=open_browser,
        on_url=lambda u: click.echo(f"Open this URL to sign in:\n\n  {u}\n"),
    )
    token_data["application"] = _iam_app()

    # Verify BEFORE storing: a token we cannot check is not one to keep and
    # later present as proof of identity.
    result = verify_token_data(token_data)
    if not result.valid:
        raise click.ClickException(
            f"IAM issued a token this client cannot verify ({result.reason}:"
            f" {result.detail}). Not storing it."
        )
    token_data["stored_in"] = _save_token(token_data)
    return token_data


def logout() -> None:
    """Clear stored credentials."""
    _clear_token()
