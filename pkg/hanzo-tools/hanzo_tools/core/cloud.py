"""One client for the live Hanzo Cloud backend (api.hanzo.ai).

Every hanzo-tools package that reaches the cloud — code index/search, vector
search, web search, vision — talks to it through this single seam. There is
exactly one place that knows the base URL, the auth header, and how to turn a
non-2xx into a typed error; tools compose it, never re-implement it.

Auth resolves in order: ``HANZO_API_KEY`` env, then the ``apiKey`` (hk- key) in
``~/.hanzo/config.json``. Base URL is ``https://api.hanzo.ai``, overridable via
``HANZO_API_BASE``.

Reference: HIP-0300 unified tools; api.hanzo.ai /v1 surface.
"""

import os
import json
from typing import Any, ClassVar
from pathlib import Path

DEFAULT_BASE = "https://api.hanzo.ai"


def cloud_api_key() -> str | None:
    """Resolve the hk- API key: env first, then ~/.hanzo/config.json."""
    env = os.environ.get("HANZO_API_KEY") or os.environ.get("HANZO_KEY")
    if env and env.strip():
        return env.strip()

    cfg = Path.home() / ".hanzo" / "config.json"
    if cfg.exists():
        try:
            key = json.loads(cfg.read_text()).get("apiKey")
            if key and str(key).strip():
                return str(key).strip()
        except (OSError, ValueError):
            return None
    return None


def cloud_api_base() -> str:
    """Resolve the API base URL (no trailing slash)."""
    base = (
        os.environ.get("HANZO_API_BASE")
        or os.environ.get("HANZO_BASE_URL")
        or DEFAULT_BASE
    )
    return base.rstrip("/")


class CloudError(Exception):
    """A Hanzo Cloud call failed (network error or non-2xx response).

    ``status`` is the HTTP status when the server answered, else None (a
    transport/DNS failure). Tools inspect it to decide fall-back vs surface.
    """

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class HanzoCloud:
    """Async client for the api.hanzo.ai /v1 surface.

    Lazily builds one ``httpx.AsyncClient`` (reused for the process lifetime,
    mirroring the other network tools). ``configured()`` reports whether a key
    is present so tools can fall back to a local path instead of failing.
    """

    USER_AGENT: ClassVar[str] = "hanzo-tools/cloud"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        key: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or cloud_api_base()).rstrip("/")
        self.key = key if key is not None else cloud_api_key()
        self.timeout = timeout
        self._client: Any = None

    def configured(self) -> bool:
        """True when an API key is available."""
        return bool(self.key)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.USER_AGENT,
        }
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        return headers

    async def _get_client(self):
        if self._client is None:
            try:
                import httpx
            except ImportError as e:
                raise CloudError("httpx not installed. Run: pip install httpx") from e
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def _request(self, method: str, path: str, **kw: Any) -> Any:
        client = await self._get_client()
        try:
            resp = await client.request(
                method, path, headers=self._headers(), **kw
            )
        except Exception as e:  # transport/DNS/timeout — no HTTP status
            raise CloudError(f"{method} {path} failed: {e}") from e

        if resp.status_code >= 400:
            raise CloudError(
                f"{method} {path} → {resp.status_code}: {_short_body(resp)}",
                status=resp.status_code,
            )
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET path, returning parsed JSON. Raises CloudError on failure."""
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        return await self._request("GET", path, params=clean)

    async def post(self, path: str, json_body: dict[str, Any] | None = None) -> Any:
        """POST json_body to path, returning parsed JSON. Raises on failure."""
        return await self._request("POST", path, json=json_body or {})

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _short_body(resp: Any, limit: int = 300) -> str:
    """A trimmed, single-line error body for CloudError messages."""
    try:
        body = resp.text
    except Exception:
        return ""
    body = " ".join(body.split())
    return body[:limit] + ("…" if len(body) > limit else "")
