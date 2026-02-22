"""Thin HTTP client for the Hanzo PaaS REST API.

Wraps the /v1/* endpoints exposed by the platform service
(paas/platform/routes/*).

Auth flow:
1. ``hanzo login`` stores an IAM token at ~/.hanzo/auth/token.json
2. On first PaaS call we exchange that IAM token for a PaaS session
   via POST /v1/auth/login {provider:"hanzo", accessToken:"<IAM JWT>"}
3. PaaS returns {at, rt} — we cache these in ~/.hanzo/paas/session.json
4. Subsequent calls use the PaaS ``at`` in the Authorization header

Environment variables:
    HANZO_PAAS_URL  — PaaS API base URL (default: https://platform.hanzo.ai)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import click
import httpx

from hanzo_cli.auth import get_token_info

DEFAULT_PAAS_URL = "https://platform.hanzo.ai"
SESSION_DIR = Path.home() / ".hanzo" / "paas"
SESSION_FILE = SESSION_DIR / "session.json"


def _save_session(data: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2))
    SESSION_FILE.chmod(0o600)


def _load_session() -> dict[str, Any] | None:
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


class PaaSClient:
    """Lightweight wrapper around the PaaS platform REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ):
        self._base_url = (
            base_url or os.getenv("HANZO_PAAS_URL", DEFAULT_PAAS_URL)
        ).rstrip("/")
        self._at = access_token
        self._rt = refresh_token
        self._http: httpx.Client | None = None

    # -- bootstrap -----------------------------------------------------------

    @classmethod
    def _exchange_iam_token(cls, base_url: str) -> PaaSClient:
        """Exchange the stored IAM token for a fresh PaaS session."""
        token_data = get_token_info()
        if not token_data or not token_data.get("access_token"):
            click.echo(
                "Not authenticated. Run 'hanzo login' first.",
                err=True,
            )
            sys.exit(1)

        iam_token = token_data["access_token"]

        with httpx.Client(base_url=base_url, timeout=30.0) as tmp:
            resp = tmp.post(
                "/v1/auth/login",
                json={
                    "provider": "hanzo",
                    "accessToken": iam_token,
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "hanzo-cli/0.1",
                },
            )
            if resp.status_code == 401:
                click.echo(
                    "IAM token rejected by PaaS. Try 'hanzo login' again.",
                    err=True,
                )
                sys.exit(1)
            resp.raise_for_status()
            data = resp.json()

        at = data.get("at", "")
        rt = data.get("rt", "")

        if not at:
            click.echo("PaaS login succeeded but no session token returned.", err=True)
            sys.exit(1)

        _save_session({"at": at, "rt": rt, "login_time": int(time.time())})
        return cls(base_url=base_url, access_token=at, refresh_token=rt)

    @classmethod
    def from_auth(cls) -> PaaSClient:
        """Build a client, exchanging the IAM token for a PaaS session.

        1. Check for a cached PaaS session (validate with authenticated endpoint)
        2. If expired/invalid, exchange the IAM token via POST /v1/auth/login
        3. Cache the PaaS session for reuse
        """
        base_url = os.getenv("HANZO_PAAS_URL", DEFAULT_PAAS_URL).rstrip("/")

        # Try cached PaaS session first
        session = _load_session()
        if session and session.get("at"):
            inst = cls(
                base_url=base_url,
                access_token=session["at"],
                refresh_token=session.get("rt"),
            )
            # Validate with an authenticated endpoint
            try:
                resp = inst.http.get("/v1/org")
                if resp.status_code != 401:
                    return inst
            except Exception:
                pass
            inst.close()

        return cls._exchange_iam_token(base_url)

    @property
    def http(self) -> httpx.Client:
        if self._http is None:
            headers: dict[str, str] = {
                "User-Agent": "hanzo-cli/0.1",
                "Content-Type": "application/json",
            }
            if self._at:
                headers["Authorization"] = self._at
            if self._rt:
                headers["Refresh-Token"] = self._rt
            self._http = httpx.Client(
                base_url=self._base_url,
                timeout=30.0,
                headers=headers,
            )
        return self._http

    def close(self) -> None:
        if self._http:
            self._http.close()
            self._http = None

    # -- helpers -------------------------------------------------------------

    def _reauth(self) -> None:
        """Re-exchange the IAM token for a fresh PaaS session."""
        self.close()
        fresh = self._exchange_iam_token(self._base_url)
        self._at = fresh._at
        self._rt = fresh._rt
        # _http will be lazily rebuilt on next access

    def _ok(self, resp: httpx.Response, *, _retried: bool = False) -> Any:
        # PaaS may return refreshed tokens in headers
        new_at = resp.headers.get("Access-Token")
        new_rt = resp.headers.get("Refresh-Token")
        if new_at:
            self._at = new_at
            _save_session(
                {
                    "at": new_at,
                    "rt": new_rt or self._rt or "",
                    "login_time": int(time.time()),
                }
            )
            # Rebuild client with new token
            self.close()

        # Auto-retry on 401: re-exchange IAM token and replay the request
        if resp.status_code == 401 and not _retried:
            self._reauth()
            # Replay the original request using just the path
            req = resp.request
            path = req.url.raw_path.decode("ascii")  # e.g. /v1/org
            retry_resp = self.http.request(
                method=req.method,
                url=path,
                content=req.content if req.content else None,
            )
            return self._ok(retry_resp, _retried=True)

        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("error", "")
                details = err.get("details", "")
                fields = err.get("fields", [])
                parts = [f"PaaS error {resp.status_code}"]
                if msg:
                    parts.append(msg)
                if details:
                    parts.append(details)
                for f in fields:
                    parts.append(f"  {f.get('param', '?')}: {f.get('msg', '')}")
                raise click.ClickException("\n".join(parts))
            except (ValueError, KeyError):
                pass
            resp.raise_for_status()

        if not resp.content or resp.status_code == 204:
            return {}
        return resp.json()

    # ========================================================================
    # Organizations
    # ========================================================================

    def list_orgs(self) -> list[dict[str, Any]]:
        return self._ok(self.http.get("/v1/org"))

    def get_org(self, org_id: str) -> dict[str, Any]:
        return self._ok(self.http.get(f"/v1/org/{org_id}"))

    # ========================================================================
    # Projects
    # ========================================================================

    def list_projects(self, org_id: str) -> list[dict[str, Any]]:
        return self._ok(self.http.get(f"/v1/org/{org_id}/project"))

    def get_project(self, org_id: str, project_id: str) -> dict[str, Any]:
        return self._ok(self.http.get(f"/v1/org/{org_id}/project/{project_id}"))

    # ========================================================================
    # Environments
    # ========================================================================

    def list_envs(self, org_id: str, project_id: str) -> list[dict[str, Any]]:
        return self._ok(self.http.get(f"/v1/org/{org_id}/project/{project_id}/env"))

    # ========================================================================
    # Containers (Deployments)
    # ========================================================================

    def _container_base(self, org_id: str, project_id: str, env_id: str) -> str:
        return f"/v1/org/{org_id}/project/{project_id}/env/{env_id}/container"

    def list_containers(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
    ) -> list[dict[str, Any]]:
        url = self._container_base(org_id, project_id, env_id)
        return self._ok(self.http.get(url))

    def get_container(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> dict[str, Any]:
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}"
        return self._ok(self.http.get(url))

    def create_container(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        url = self._container_base(org_id, project_id, env_id)
        return self._ok(self.http.post(url, json=payload))

    def update_container(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}"
        return self._ok(self.http.put(url, json=payload))

    def delete_container(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> dict[str, Any]:
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}"
        return self._ok(self.http.delete(url))

    def redeploy_container(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> dict[str, Any]:
        """Trigger a redeploy by re-PUTting the container config.

        The PaaS API doesn't expose a dedicated /redeploy endpoint.
        Updating the container with its current config triggers a rolling restart.
        """
        # Fetch current config, then PUT it back to trigger redeployment
        container = self.get_container(org_id, project_id, env_id, container_id)
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}"
        return self._ok(self.http.put(url, json=container))

    def get_container_pods(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> list[dict[str, Any]]:
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}/pods"
        return self._ok(self.http.get(url))

    def get_container_logs(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> Any:
        url = f"{self._container_base(org_id, project_id, env_id)}/{container_id}/logs"
        return self._ok(self.http.get(url))

    def get_container_events(
        self,
        org_id: str,
        project_id: str,
        env_id: str,
        container_id: str,
    ) -> list[dict[str, Any]]:
        url = (
            f"{self._container_base(org_id, project_id, env_id)}/{container_id}/events"
        )
        return self._ok(self.http.get(url))

    # ========================================================================
    # Cluster
    # ========================================================================

    def cluster_info(self) -> dict[str, Any]:
        return self._ok(self.http.get("/v1/cluster/info"))

    def cluster_templates(self) -> list[dict[str, Any]]:
        return self._ok(self.http.get("/v1/cluster/templates"))
