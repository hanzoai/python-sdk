"""PaaS API client for Hanzo CLI.

Shared HTTP client used by k8s, run, and git commands to talk to
the PaaS platform API (platform.hanzo.ai).
"""

import os
import json
import time
from pathlib import Path
from typing import Optional

import httpx

from .output import console


PLATFORM_API_URL = os.getenv(
    "PLATFORM_API_URL",
    os.getenv("HANZO_PLATFORM_URL", "https://platform.hanzo.ai"),
)

CONTEXT_FILE = Path.home() / ".hanzo" / "context.json"
AUTH_FILE = Path.home() / ".hanzo" / "auth.json"
SESSION_FILE = Path.home() / ".hanzo" / "paas_session.json"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_iam_token() -> Optional[str]:
    """Get IAM bearer token from env or ~/.hanzo/auth.json."""
    token = os.getenv("HANZO_TOKEN") or os.getenv("HANZO_API_KEY")
    if token:
        return token

    if AUTH_FILE.exists():
        try:
            auth = json.loads(AUTH_FILE.read_text())
            # CLI login stores flat "token", worker/IAM stores nested "tokens.access_token"
            return (
                auth.get("token")
                or auth.get("api_key")
                or auth.get("tokens", {}).get("access_token")
            )
        except Exception:
            pass
    return None


# Keep old name as alias
get_token = get_iam_token


def _load_session() -> dict:
    """Load cached PaaS session tokens."""
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_session(session: dict):
    """Cache PaaS session tokens."""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(session, indent=2))


def _exchange_iam_for_session(iam_token: str, timeout: int = 15) -> Optional[dict]:
    """Exchange IAM token for PaaS session via POST /v1/auth/login."""
    url = f"{PLATFORM_API_URL}/v1/auth/login"
    payload = {"provider": "hanzo", "accessToken": iam_token}

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
    except Exception as e:
        console.print(f"[red]Failed to reach PaaS login: {e}[/red]")
        return None

    if resp.status_code >= 400:
        try:
            body = resp.json()
            msg = body.get("message") or body.get("error") or resp.text
        except Exception:
            msg = resp.text
        console.print(f"[red]PaaS login failed ({resp.status_code}): {msg}[/red]")
        return None

    data = resp.json()
    at = data.get("at", "")
    rt = data.get("rt", "")
    if not at:
        console.print("[red]PaaS login returned no session token.[/red]")
        return None

    session = {
        "access_token": at,
        "refresh_token": rt,
        "created_at": time.time(),
        "platform_url": PLATFORM_API_URL,
    }
    _save_session(session)
    return session


def _get_session_token(timeout: int = 15) -> Optional[str]:
    """Get a valid PaaS session token, exchanging IAM token if needed."""
    # Check env for direct PaaS token override
    paas_token = os.getenv("HANZO_PAAS_TOKEN")
    if paas_token:
        return paas_token

    # Check cached session (session tokens are short-lived: 5 min access, 4 hr refresh)
    session = _load_session()
    if session.get("access_token") and session.get("platform_url") == PLATFORM_API_URL:
        age = time.time() - session.get("created_at", 0)
        if age < 240:  # Use cached if < 4 min old (access token lasts 5 min)
            return session["access_token"]

    # Need fresh session — get IAM token first
    iam_token = get_iam_token()
    if not iam_token:
        return None

    session = _exchange_iam_for_session(iam_token, timeout=timeout)
    if session:
        return session["access_token"]
    return None


def _require_token() -> str:
    """Return PaaS session token or print error and raise SystemExit."""
    token = _get_session_token()
    if not token:
        console.print("[red]Not authenticated. Run 'hanzo auth login' first.[/red]")
        raise SystemExit(1)
    return token


# ---------------------------------------------------------------------------
# Context helpers  (org / project / env selection)
# ---------------------------------------------------------------------------

def load_context() -> dict:
    """Load active org/project/env context from ~/.hanzo/context.json."""
    if CONTEXT_FILE.exists():
        try:
            return json.loads(CONTEXT_FILE.read_text())
        except Exception:
            pass
    return {}


def save_context(ctx: dict):
    """Persist active context."""
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2))


def require_context(fields: tuple = ("org_id", "project_id", "env_id")) -> dict:
    """Return context dict or error if required fields are missing."""
    ctx = load_context()
    missing = [f for f in fields if not ctx.get(f)]
    if missing:
        console.print(
            f"[red]Missing context: {', '.join(missing)}[/red]\n"
            "Run 'hanzo auth context set --org ORG --project PROJECT --env ENV' first."
        )
        raise SystemExit(1)
    return ctx


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------

def container_url(
    org_id: str,
    project_id: str,
    env_id: str,
    container_id: Optional[str] = None,
) -> str:
    base = f"{PLATFORM_API_URL}/v1/org/{org_id}/project/{project_id}/env/{env_id}/container"
    if container_id:
        return f"{base}/{container_id}"
    return base


def org_url(org_id: Optional[str] = None) -> str:
    if org_id:
        return f"{PLATFORM_API_URL}/v1/org/{org_id}"
    return f"{PLATFORM_API_URL}/v1/org"


def project_url(org_id: str, project_id: Optional[str] = None) -> str:
    base = f"{PLATFORM_API_URL}/v1/org/{org_id}/project"
    if project_id:
        return f"{base}/{project_id}"
    return base


def env_url(org_id: str, project_id: str, env_id: Optional[str] = None) -> str:
    base = f"{PLATFORM_API_URL}/v1/org/{org_id}/project/{project_id}/env"
    if env_id:
        return f"{base}/{env_id}"
    return base


def cluster_url(cluster_name: Optional[str] = None) -> str:
    base = f"{PLATFORM_API_URL}/v1/cluster"
    if cluster_name:
        return f"{base}/{cluster_name}"
    return base


def git_url(provider_id: Optional[str] = None) -> str:
    base = f"{PLATFORM_API_URL}/v1/user/git"
    if provider_id:
        return f"{base}/{provider_id}"
    return base


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def extract_list(data, key: str) -> list:
    """Extract list from API response (handles both direct lists and wrapped objects)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get(key, data.get("data", []))
    return []


def find_container(client, base_url: str, name: str):
    """Find a container by name in the current environment. Returns (data, id)."""
    data = client.get(base_url)
    if data is None:
        return None, None
    for c in extract_list(data, "containers"):
        cname = c.get("name", c.get("iid", ""))
        cid = c.get("_id") or c.get("iid") or c.get("id", "")
        if cname == name or cid == name:
            return c, cid
    return None, None


# ---------------------------------------------------------------------------
# PaaS HTTP client
# ---------------------------------------------------------------------------

class PaaSClient:
    """HTTP client for PaaS API with auto session management."""

    def __init__(self, timeout: int = 30):
        self.token = _require_token()
        self.timeout = timeout
        self._refresh_token = _load_session().get("refresh_token", "")

    @property
    def headers(self) -> dict:
        h = {"Authorization": f"Bearer {self.token}"}
        if self._refresh_token:
            h["Refresh-Token"] = self._refresh_token
        return h

    def get(self, url: str, **kwargs) -> Optional[dict]:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, payload: Optional[dict] = None, **kwargs) -> Optional[dict]:
        return self._request("POST", url, json=payload, **kwargs)

    def put(self, url: str, payload: Optional[dict] = None, **kwargs) -> Optional[dict]:
        return self._request("PUT", url, json=payload, **kwargs)

    def delete(self, url: str, **kwargs) -> Optional[dict]:
        return self._request("DELETE", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(method, url, headers=self.headers, **kwargs)

                # If server refreshed our tokens, save them
                new_at = resp.headers.get("Access-Token")
                new_rt = resp.headers.get("Refresh-Token")
                if new_at:
                    self.token = new_at
                    if new_rt:
                        self._refresh_token = new_rt
                    _save_session({
                        "access_token": new_at,
                        "refresh_token": self._refresh_token,
                        "created_at": time.time(),
                        "platform_url": PLATFORM_API_URL,
                    })

                # On 401, try re-auth once
                if resp.status_code == 401:
                    new_token = self._reauth()
                    if new_token:
                        resp = client.request(method, url, headers=self.headers, **kwargs)
                    else:
                        return self._handle_response(resp)

                return self._handle_response(resp)
        except httpx.ConnectError:
            console.print(f"[red]Could not connect to {PLATFORM_API_URL}[/red]")
            return None
        except httpx.TimeoutException:
            console.print("[red]Request timed out.[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Request error: {e}[/red]")
            return None

    def _reauth(self) -> Optional[str]:
        """Re-exchange IAM token for a fresh PaaS session."""
        iam_token = get_iam_token()
        if not iam_token:
            return None
        session = _exchange_iam_for_session(iam_token, timeout=self.timeout)
        if session:
            self.token = session["access_token"]
            self._refresh_token = session.get("refresh_token", "")
            return self.token
        return None

    @staticmethod
    def _handle_response(resp: httpx.Response) -> Optional[dict]:
        if resp.status_code == 401:
            console.print("[red]Authentication failed. Run 'hanzo auth login'.[/red]")
            return None
        if resp.status_code == 403:
            console.print("[red]Permission denied.[/red]")
            return None
        if resp.status_code == 404:
            console.print("[yellow]Resource not found.[/yellow]")
            return None
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("message") or body.get("error") or resp.text
            except Exception:
                msg = resp.text
            console.print(f"[red]API error ({resp.status_code}): {msg}[/red]")
            return None

        if resp.status_code == 204:
            return {}

        try:
            return resp.json()
        except Exception:
            return {}
