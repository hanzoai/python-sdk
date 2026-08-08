"""One client for the live Hanzo Cloud backend (api.hanzo.ai).

Every hanzo-tools package that reaches the cloud — code index/search, vector
search, web search, research, vision — talks to it through this one client.
There is exactly one place that knows the base URL, the auth header, and how to
turn a non-2xx into a typed error; tools compose it, never re-implement it.

Auth resolves in order: ``HANZO_API_KEY`` env, the ``apiKey`` (a ``pk-``/``sk-``
key) in ``~/.hanzo/config.json``, then the ``hanzo`` CLI's live IAM session.
Base URL is ``https://api.hanzo.ai``, overridable via ``HANZO_API_BASE``.

Reference: HIP-0300 unified tools; api.hanzo.ai /v1 surface.
"""

import os
import json
import subprocess
from typing import Any, ClassVar
from pathlib import Path
from collections.abc import AsyncIterator

DEFAULT_BASE = "https://api.hanzo.ai"

#: What a cloud-backed tool says when no key resolved — one sentence in one
#: place, so the shapes cannot drift apart tool by tool. Cloud admits two:
#: ``pk-`` is the publishable key you may ship in a browser bundle, ``sk-`` is
#: the one you may not. ``APIKeyPrefixes`` in cloud's ``auth_identity.go`` is
#: the authority; anything else resolves to no principal.
NO_KEY = "no API key: run `hanzo login` or set HANZO_API_KEY (pk-/sk-)"


# Memo for cli_session_token: shelling out costs ~100ms and the token is stable
# for the session, so resolve it at most once per process. `False` means "asked
# and there was none", which is distinct from "not asked yet" (None).
_cli_token: str | None | bool = None


def cli_session_token() -> str | None:
    """The bearer token held by the ``hanzo`` CLI's IAM session.

    The CLI already owns interactive login against hanzo.id, so asking it for a
    token means tools never prompt, never keep a second copy of the credential,
    and never parse a secret out of a file themselves.
    """
    global _cli_token
    if _cli_token is not None:
        return _cli_token or None

    try:
        out = subprocess.run(
            ["hanzo", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        _cli_token = False  # no CLI on PATH: do not retry on every call
        return None

    token = (out.stdout or "").strip()
    _cli_token = token if out.returncode == 0 and token else False
    return _cli_token or None


def cloud_api_key() -> str | None:
    """Resolve the bearer credential.

    Order: ``HANZO_API_KEY`` env, then the key in ~/.hanzo/config.json, then
    the CLI's live IAM session.
    """
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
            pass

    return cli_session_token()


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

    async def stream(
        self,
        path: str,
        json_body: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """POST json_body to path and yield the events the server streams back.

        Server-sent events are the cloud's other reply shape. The answer engine
        (``/v1/ask``) writes ``data: {…}`` frames as it plans, searches, reads
        and writes, so a caller follows the work instead of waiting minutes in
        silence. It belongs beside get/post: the base URL, the auth header and
        the error mapping stay in this one place.

        Each frame's JSON object is yielded as a dict. The terminal ``[DONE]``
        sentinel (the OpenAI convention the server mirrors) marks the end of the
        stream, not an event, so it is skipped rather than handed to callers.
        ``timeout`` overrides the client default for one call — a research pass
        legitimately outlives a request-shaped budget.
        """
        client = await self._get_client()
        headers = {**self._headers(), "Accept": "text/event-stream"}
        try:
            async with client.stream(
                "POST",
                path,
                headers=headers,
                json=json_body or {},
                timeout=timeout if timeout is not None else self.timeout,
            ) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    raise CloudError(
                        f"POST {path} → {resp.status_code}: {_short_body(resp)}",
                        status=resp.status_code,
                    )
                async for line in resp.aiter_lines():
                    event = _sse_event(line)
                    if event is not None:
                        yield event
        except CloudError:
            raise
        except Exception as e:  # transport/DNS/timeout — no HTTP status
            raise CloudError(f"POST {path} stream failed: {e}") from e

    async def call(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Any-method call, for callers driving routes from the OpenAPI spec.

        The spec names methods this client has no bespoke helper for (PUT,
        PATCH, DELETE), so it needs one generic entry rather than a helper per
        verb — the auth header and error mapping stay in this one place.
        """
        kw: dict[str, Any] = {}
        if params:
            kw["params"] = {k: v for k, v in params.items() if v is not None}
        if json_body is not None:
            kw["json"] = json_body
        return await self._request(method.upper(), path, **kw)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _sse_event(line: str) -> dict[str, Any] | None:
    """The event carried by one SSE line, or None when it carries none.

    Blank separators, keep-alive comments, ``event:``/``id:`` fields and the
    terminal ``[DONE]`` sentinel are all "no event". A ``data:`` payload that is
    not a JSON object is skipped too: one malformed frame must not end an answer
    that is still arriving.
    """
    if not line.startswith("data:"):
        return None
    payload = line[len("data:") :].strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        event = json.loads(payload)
    except ValueError:
        return None
    return event if isinstance(event, dict) else None


def _short_body(resp: Any, limit: int = 300) -> str:
    """A trimmed, single-line error body for CloudError messages."""
    try:
        body = resp.text
    except Exception:
        return ""
    body = " ".join(body.split())
    return body[:limit] + ("…" if len(body) > limit else "")
