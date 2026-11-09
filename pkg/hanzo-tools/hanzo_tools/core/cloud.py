"""One client for the live Hanzo Cloud backend (api.hanzo.ai).

Every hanzo-tools package that reaches the cloud — code index/search, vector
search, web search, research, vision — talks to it through this one client.
There is exactly one place that knows the base URL, the auth header, and how to
turn a non-2xx into a typed error; tools compose it, never re-implement it.

Auth resolves through ``hanzo_login`` (the one resolver every Hanzo tool shares):
``HANZO_API_KEY`` env, then the ``hanzo`` CLI's login (``hanzo auth token``), then the
legacy ``apiKey`` in ``~/.hanzo/config.json`` last. An identity named per call (``identity``)
or for the process (``hanzo_login.use``) always asks the login. It is resolved on each
request, not once: a login's token is short-lived and the CLI refreshes it.
Base URL is ``https://api.hanzo.ai``, overridable via ``HANZO_API_BASE``.

Reference: HIP-0300 unified tools; api.hanzo.ai /v1 surface.
"""

import os
import json
from typing import Any
from importlib import metadata
from collections.abc import Mapping, AsyncIterator

import hanzo_login as login

DEFAULT_BASE = "https://api.hanzo.ai"
try:
    USER_AGENT = f"hanzo-tools/{metadata.version('hanzo-tools')}"
except metadata.PackageNotFoundError:
    USER_AGENT = "hanzo-tools/source"

#: What a cloud-backed tool says when no key resolved — one sentence in one
#: place, so the shapes cannot drift apart tool by tool. ``pk-`` is the
#: publishable key you may ship in a browser bundle; ``sk-`` and ``hk-`` are the
#: ones you may not. ``isAPIKey`` in cloud's ``auth_identity.go`` is the
#: authority — it admits ``hk-``, ``sk-``, ``pk-``, ``fw_`` and ``hz_``, and a
#: token carrying no such prefix never reaches key validation at all.
NO_KEY = "no API key: run `hanzo auth login` or set HANZO_API_KEY (hk-/sk-/pk-)"


def cloud_api_key(identity: str | None = None) -> str | None:
    """The bearer credential, or None. ``identity`` asks the login for that account.

    Raises ``hanzo_login.LoginError`` when an identity is named (here, or with
    ``hanzo_login.use``) and the login will not give it.
    """
    return login.credential(identity).secret or None


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
    ``body`` is the answer's decoded JSON (None when it was not JSON or there
    was no answer) and ``headers`` its headers, so a refusal can be read whole
    (``hanzoai.usage.refusal``) rather than out of the trimmed message.
    """

    def __init__(
        self,
        message: str,
        status: int | None = None,
        body: Any = None,
        headers: Mapping[str, str] | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.body = body
        self.headers = headers if headers is not None else {}


class HanzoCloud:
    """Async client for the api.hanzo.ai /v1 surface.

    Lazily builds one ``httpx.AsyncClient`` (reused for the process lifetime,
    mirroring the other network tools). ``configured()`` reports whether a
    credential is present so tools can fall back to a local path instead of failing.

    ``key`` pins one credential for this client; left out, each request resolves it
    (``cloud_api_key``), so a login that was refreshed or switched is followed.
    ``identity`` on a request asks the login for that account instead, and ``org``
    acts in another org the credential belongs to (``X-Org-Id``). ``agent`` is the
    User-Agent, ``hanzo-tools/<version>`` by default.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        key: str | None = None,
        timeout: float = 60.0,
        agent: str | None = None,
    ):
        self.base_url = (base_url or cloud_api_base()).rstrip("/")
        self.key = key
        self.timeout = timeout
        self.agent = agent or USER_AGENT
        self._client: Any = None

    def _secret(self, identity: str | None = None) -> str | None:
        if not identity and self.key is not None:
            return self.key or None
        return cloud_api_key(identity)

    def configured(self) -> bool:
        """True when a credential is available."""
        try:
            return bool(self._secret())
        except login.LoginError:
            return False

    def _headers(self, identity: str | None = None, org: str | None = None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.agent,
        }
        secret = self._secret(identity)
        if secret:
            headers["Authorization"] = f"Bearer {secret}"
        if org:
            headers["X-Org-Id"] = login.valid_org(org)
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

    def _auth(self, method: str, path: str, identity: str | None, org: str | None) -> dict[str, str]:
        try:
            return self._headers(identity, org)
        except login.LoginError as e:
            raise CloudError(f"{method} {path}: {e}") from e

    async def send(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        identity: str | None = None,
        org: str | None = None,
        **kw: Any,
    ) -> tuple[Any, Mapping[str, str]]:
        """One request: the parsed JSON body and the answer's headers.

        For a route whose headers say something (the ``X-Hanzo-*`` usage
        headers on a priced call). ``kw`` passes to httpx (``params``,
        ``json``). Raises CloudError on a transport failure or a non-2xx, or when
        ``identity`` is named and the login will not give it.
        """
        base = self._auth(method, path, identity, org)
        client = await self._get_client()
        try:
            resp = await client.request(
                method, path, headers={**base, **(headers or {})}, **kw
            )
        except Exception as e:  # transport/DNS/timeout — no HTTP status
            raise CloudError(f"{method} {path} failed: {e}") from e

        if resp.status_code >= 400:
            try:
                body = resp.json()
            except ValueError:
                body = None
            raise CloudError(
                f"{method} {path} → {resp.status_code}: {_short_body(resp)}",
                status=resp.status_code,
                body=body,
                headers=resp.headers,
            )
        try:
            return resp.json(), resp.headers
        except ValueError:
            return {"text": resp.text}, resp.headers

    async def _request(
        self, method: str, path: str, headers: dict[str, str] | None = None, **kw: Any
    ) -> Any:
        body, _ = await self.send(method, path, headers=headers, **kw)
        return body

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET path, returning parsed JSON. Raises CloudError on failure."""
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        return await self._request("GET", path, params=clean)

    async def post(
        self,
        path: str,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """POST json_body to path, returning parsed JSON. Raises on failure.

        ``headers`` ride beside the auth header, for a route that reads one (Enso's
        X-Max-Cost and X-Max-Latency-Ms on /v1/chat/completions).
        """
        return await self._request("POST", path, headers=headers, json=json_body or {})

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
        headers = {**self._auth("POST", path, None, None), "Accept": "text/event-stream"}
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
                    try:
                        body = resp.json()
                    except ValueError:
                        body = None
                    raise CloudError(
                        f"POST {path} → {resp.status_code}: {_short_body(resp)}",
                        status=resp.status_code,
                        body=body,
                        headers=resp.headers,
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
        identity: str | None = None,
        org: str | None = None,
    ) -> Any:
        """Any-method call, for callers driving routes from the OpenAPI spec.

        The spec names methods this client has no bespoke helper for (PUT,
        PATCH, DELETE), so it needs one generic entry rather than a helper per
        verb — the auth header and error mapping stay in this one place.
        ``identity`` acts as that account for this call, ``org`` in that org.
        """
        kw: dict[str, Any] = {}
        if params:
            kw["params"] = {k: v for k, v in params.items() if v is not None}
        if json_body is not None:
            kw["json"] = json_body
        return await self._request(method.upper(), path, identity=identity, org=org, **kw)

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
