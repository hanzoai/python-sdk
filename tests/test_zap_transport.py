"""Tests for the optional ZAP-native transport (`hanzoai.zap`).

Covers two guarantees:

1. Back-compat: `import hanzoai` succeeds and the locked public `__all__` still
   contains the core names, while the new ZAP names are additive (NOT in `__all__`).
2. Correctness: the transport translates a typed HTTP request into a
   `hanzo_zap.CloudClient.call(...)` — asserting the derived method, forwarded auth,
   and body — using a mock CloudClient, so no network and no `hanzo-zap` install.
"""

from __future__ import annotations

import json

import httpx

import hanzoai
from hanzoai import Hanzo, ZapTransport, AsyncZapTransport, zap_http_client
from hanzoai.zap import method_from_path

# The public surface that must never regress.
LOCKED_CORE_NAMES = {
    "Hanzo",
    "AsyncHanzo",
    "Client",
    "AsyncClient",
    "Stream",
    "AsyncStream",
    "HanzoError",
    "APIError",
    "APIStatusError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "agents",
    "mcp",
    "auth",
    "session",
    "config",
    "protocols",
}

ZAP_ADDITIVE_NAMES = {
    "zap",
    "zap_http_client",
    "async_zap_http_client",
    "ZapTransport",
    "AsyncZapTransport",
}


class MockCloudClient:
    """Stand-in for `hanzo_zap.CloudClient` that records calls and never touches the network."""

    def __init__(self, status: int = 200, body: bytes = b'{"ok": true}', error: str = "") -> None:
        self.status = status
        self.body = body
        self.error = error
        self.calls: list[tuple[str, str, bytes]] = []
        self.closed = False

    async def call(self, method: str, auth: str, body: bytes) -> tuple[int, bytes, str]:
        self.calls.append((method, auth, body))
        return (self.status, self.body, self.error)

    async def close(self) -> None:
        self.closed = True


# --------------------------------------------------------------------------- #
# 1. Back-compat / locked public API
# --------------------------------------------------------------------------- #


def test_import_hanzoai_succeeds() -> None:
    assert hanzoai.__version__


def test_all_contains_locked_core_names() -> None:
    missing = LOCKED_CORE_NAMES - set(hanzoai.__all__)
    assert not missing, f"locked names dropped from __all__: {missing}"


def test_zap_names_are_additive_not_in_all() -> None:
    # The ZAP helpers are importable attributes but must NOT enter the locked __all__.
    leaked = ZAP_ADDITIVE_NAMES & set(hanzoai.__all__)
    assert not leaked, f"ZAP names must stay out of __all__, found: {leaked}"
    for name in ZAP_ADDITIVE_NAMES:
        assert hasattr(hanzoai, name), f"expected additive attribute hanzoai.{name}"


# --------------------------------------------------------------------------- #
# 2. Request translation
# --------------------------------------------------------------------------- #


def test_method_from_path() -> None:
    assert method_from_path("/v1/chat/completions") == "chat.completions"
    assert method_from_path("/v1/models") == "models"
    assert method_from_path("/v1/fine_tuning/jobs") == "fine_tuning.jobs"


def test_sync_transport_translates_request() -> None:
    mock = MockCloudClient(status=200, body=b'{"id": "chatcmpl-1"}')
    transport = ZapTransport(client=mock)
    try:
        payload = {"model": "zen-1", "messages": [{"role": "user", "content": "hi"}]}
        request = httpx.Request(
            "POST",
            "https://api.hanzo.ai/v1/chat/completions",
            headers={"Authorization": "Bearer sk-test"},
            json=payload,
        )
        response = transport.handle_request(request)
    finally:
        transport.close()

    assert response.status_code == 200
    assert response.json() == {"id": "chatcmpl-1"}

    assert len(mock.calls) == 1
    method, auth, body = mock.calls[0]
    assert method == "chat.completions"
    assert auth == "Bearer sk-test"
    assert json.loads(body) == payload


def test_sync_transport_maps_zap_error_status() -> None:
    mock = MockCloudClient(status=429, body=b"", error="rate limited")
    transport = ZapTransport(client=mock)
    try:
        request = httpx.Request("GET", "https://api.hanzo.ai/v1/models")
        response = transport.handle_request(request)
    finally:
        transport.close()

    assert response.status_code == 429
    assert response.json()["error"]["message"] == "rate limited"
    assert mock.calls[0][0] == "models"


def test_full_hanzo_client_routes_through_zap() -> None:
    """End-to-end: the standard Hanzo client, unchanged, drives a resource call over ZAP."""
    models_payload = {"object": "list", "data": [{"id": "zen-1"}, {"id": "zen-2"}]}
    mock = MockCloudClient(status=200, body=json.dumps(models_payload).encode("utf-8"))

    http_client = httpx.Client(transport=ZapTransport(client=mock))
    with Hanzo(api_key="sk-test", base_url="https://api.hanzo.ai", http_client=http_client) as client:
        result = client.models.list()

    assert result == models_payload
    method, auth, _ = mock.calls[0]
    assert method == "models"
    assert auth == "Bearer sk-test"


async def test_async_transport_translates_request() -> None:
    mock = MockCloudClient(status=200, body=b'{"id": "chatcmpl-async"}')
    transport = AsyncZapTransport(client=mock)
    try:
        payload = {"model": "zen-1", "messages": [{"role": "user", "content": "hi"}]}
        request = httpx.Request(
            "POST",
            "https://api.hanzo.ai/v1/chat/completions",
            headers={"Authorization": "Bearer sk-async"},
            json=payload,
        )
        response = await transport.handle_async_request(request)
    finally:
        await transport.aclose()

    assert response.status_code == 200
    assert response.json() == {"id": "chatcmpl-async"}
    method, auth, body = mock.calls[0]
    assert method == "chat.completions"
    assert auth == "Bearer sk-async"
    assert json.loads(body) == payload


def test_zap_http_client_returns_httpx_client() -> None:
    client = zap_http_client("localhost:3692")
    try:
        assert isinstance(client, httpx.Client)
        assert isinstance(client._transport, ZapTransport)  # type: ignore[attr-defined]
    finally:
        client.close()
