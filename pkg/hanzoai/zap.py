"""Optional ZAP-native transport for the Hanzo client.

This module lets the standard :class:`~hanzoai.Hanzo` / :class:`~hanzoai.AsyncHanzo`
client speak Hanzo's zero-copy binary wire protocol (``ZAP``) instead of HTTP/1.1,
*without any change to the public client class or a single resource method*.

The seam is httpx's pluggable transport. The Hanzo client already accepts a custom
``http_client``; this module supplies an :class:`httpx.BaseTransport` (and its async
twin) that translates each typed request into a ``hanzo_zap.CloudClient.call(...)``
over the ZAP wire, then hands the reply back to the SDK as a normal
:class:`httpx.Response`. Because the translation happens below httpx, every existing
resource call (``client.chat.completions.create(...)``, ``client.models.list()``, …)
works unchanged.

ZAP is strictly **opt-in**. Nothing here runs unless you build a ZAP-backed
``http_client`` and pass it explicitly::

    import hanzoai

    client = hanzoai.Hanzo(
        api_key="sk-...",
        base_url="https://api.hanzo.ai",
        http_client=hanzoai.zap_http_client("api.hanzo.ai:3692"),
    )
    client.chat.completions.create(model="...", messages=[...])  # now over ZAP

The default transport remains plain HTTPS; omit ``http_client`` and nothing changes.

``hanzo-zap`` is an **optional** dependency (``pip install 'hanzoai[zap]'``). It is
imported lazily, so ``import hanzoai`` and this module both import cleanly when it is
not installed — only actually opening a ZAP connection requires it.

Request/response mapping
------------------------
* **Method** — derived from the request path: the leading ``/`` and a ``v1/`` prefix
  are stripped and remaining segments are joined with ``.``. So ``/v1/chat/completions``
  becomes the ZAP method ``chat.completions`` (matching
  :meth:`hanzo_zap.CloudClient.chat_completion`), and ``/v1/models`` becomes ``models``.
* **Auth** — a bearer credential is forwarded. An existing ``Authorization`` header is
  passed verbatim; otherwise the api key the SDK attaches (``Ocp-Apim-Subscription-Key``
  or ``x-api-key``) is forwarded as ``Bearer <key>``.
* **Body** — the request body bytes are forwarded unchanged; the reply bytes become the
  response body with ``content-type: application/json``.

Only unary (non-streaming) JSON calls are translated; streaming responses are out of
scope for this transport and should use the default HTTPS client.
"""

from __future__ import annotations

import os
import json
import asyncio
import threading
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from hanzo_zap import CloudClient

__all__ = [
    "ZapTransport",
    "AsyncZapTransport",
    "zap_http_client",
    "async_zap_http_client",
    "method_from_path",
]

DEFAULT_NODE_ID = "python-sdk"
ZAP_ENDPOINT_ENV = "HANZO_ZAP_ENDPOINT"


def _load_cloud_client() -> type[CloudClient]:
    """Import ``hanzo_zap.CloudClient`` lazily with a clear install hint."""
    try:
        from hanzo_zap import CloudClient
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch in tests
        raise ImportError(
            "The ZAP-native transport requires the optional 'hanzo-zap' package. "
            "Install it with: pip install 'hanzoai[zap]'"
        ) from exc
    return CloudClient


#: API-key headers the Hanzo client may attach, in fallback order after ``Authorization``.
_API_KEY_HEADERS = ("ocp-apim-subscription-key", "x-api-key")


def _auth_from_request(request: httpx.Request) -> str:
    """Extract a bearer credential to forward over ZAP.

    Prefers an explicit ``Authorization`` header; otherwise normalizes the SDK's api-key
    header into ``Bearer <key>``. Returns ``""`` when no credential is present.
    """
    authorization = request.headers.get("authorization")
    if authorization:
        return authorization
    for header in _API_KEY_HEADERS:
        key = request.headers.get(header)
        if key:
            return f"Bearer {key}"
    return ""


def method_from_path(path: str) -> str:
    """Derive a ZAP method name from an HTTP request path.

    ``/v1/chat/completions`` -> ``chat.completions``; ``/v1/models`` -> ``models``.
    """
    trimmed = path.strip("/")
    if trimmed.startswith("v1/"):
        trimmed = trimmed[len("v1/") :]
    return trimmed.replace("/", ".")


def _build_response(request: httpx.Request, status: int, body: bytes, error: str) -> httpx.Response:
    if not body and error:
        body = json.dumps({"error": {"message": error, "type": "zap_error"}}).encode("utf-8")
    return httpx.Response(
        status_code=status,
        headers={"content-type": "application/json"},
        content=body,
        request=request,
    )


class _LoopThread:
    """A dedicated asyncio event loop running on a daemon thread.

    Lets the synchronous transport drive the async :class:`CloudClient` from any
    thread — including one that already has its own running loop — via
    :func:`asyncio.run_coroutine_threadsafe`.
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="hanzoai-zap-loop", daemon=True
        )
        self._thread.start()

    def run(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def close(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._loop.close()


class ZapTransport(httpx.BaseTransport):
    """Synchronous httpx transport that routes requests over ZAP.

    Pass the resulting client to :class:`~hanzoai.Hanzo` via ``http_client`` (see
    :func:`zap_http_client` for the one-liner). A pre-built ``client`` may be injected
    (chiefly for tests); otherwise a :class:`hanzo_zap.CloudClient` is connected lazily
    on first request.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        client: CloudClient | None = None,
        use_tls: bool | None = None,
        node_id: str = DEFAULT_NODE_ID,
    ) -> None:
        self._endpoint = endpoint or os.environ.get(ZAP_ENDPOINT_ENV)
        self._use_tls = use_tls
        self._node_id = node_id
        self._client = client
        self._owns_client = client is None
        self._loop = _LoopThread()
        self._lock = threading.Lock()

    def _ensure_client(self) -> CloudClient:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    cloud_client = _load_cloud_client()
                    self._client = self._loop.run(
                        cloud_client.connect(
                            self._endpoint, use_tls=self._use_tls, node_id=self._node_id
                        )
                    )
        return self._client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        client = self._ensure_client()
        method = method_from_path(request.url.path)
        auth = _auth_from_request(request)
        body = request.read()
        status, resp_body, error = self._loop.run(client.call(method, auth, body))
        return _build_response(request, status, resp_body, error)

    def close(self) -> None:
        try:
            if self._client is not None and self._owns_client:
                self._loop.run(self._client.close())
        finally:
            self._loop.close()


class AsyncZapTransport(httpx.AsyncBaseTransport):
    """Asynchronous httpx transport that routes requests over ZAP.

    Pass the resulting client to :class:`~hanzoai.AsyncHanzo` via ``http_client`` (see
    :func:`async_zap_http_client`).
    """

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        client: CloudClient | None = None,
        use_tls: bool | None = None,
        node_id: str = DEFAULT_NODE_ID,
    ) -> None:
        self._endpoint = endpoint or os.environ.get(ZAP_ENDPOINT_ENV)
        self._use_tls = use_tls
        self._node_id = node_id
        self._client = client
        self._owns_client = client is None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> CloudClient:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    cloud_client = _load_cloud_client()
                    self._client = await cloud_client.connect(
                        self._endpoint, use_tls=self._use_tls, node_id=self._node_id
                    )
        return self._client

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        client = await self._ensure_client()
        method = method_from_path(request.url.path)
        auth = _auth_from_request(request)
        body = await request.aread()
        status, resp_body, error = await client.call(method, auth, body)
        return _build_response(request, status, resp_body, error)

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.close()


def zap_http_client(
    endpoint: str | None = None,
    *,
    use_tls: bool | None = None,
    node_id: str = DEFAULT_NODE_ID,
    **httpx_kwargs: Any,
) -> httpx.Client:
    """Build an :class:`httpx.Client` whose transport speaks ZAP.

    Pass the result straight to :class:`~hanzoai.Hanzo`::

        hanzoai.Hanzo(api_key="sk-...", http_client=hanzoai.zap_http_client("api.hanzo.ai:3692"))

    ``endpoint`` defaults to the ``HANZO_ZAP_ENDPOINT`` env var, then to
    ``hanzo_zap``'s own default (``localhost:3692``). Extra keyword arguments are
    forwarded to :class:`httpx.Client`.
    """
    transport = ZapTransport(endpoint, use_tls=use_tls, node_id=node_id)
    return httpx.Client(transport=transport, **httpx_kwargs)


def async_zap_http_client(
    endpoint: str | None = None,
    *,
    use_tls: bool | None = None,
    node_id: str = DEFAULT_NODE_ID,
    **httpx_kwargs: Any,
) -> httpx.AsyncClient:
    """Async counterpart of :func:`zap_http_client` for :class:`~hanzoai.AsyncHanzo`."""
    transport = AsyncZapTransport(endpoint, use_tls=use_tls, node_id=node_id)
    return httpx.AsyncClient(transport=transport, **httpx_kwargs)
