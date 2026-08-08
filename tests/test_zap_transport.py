"""Tests for the optional ZAP-native transport (`hanzoai.zap`).

Covers two guarantees:

1. The package imports and still exports its core names, while the ZAP names are
   additive (NOT in `__all__`).
2. Correctness: the transport translates a typed HTTP request into a
   `hanzo_zap.CloudClient.call(...)` — asserting the derived method, forwarded auth,
   and body — using a mock CloudClient, so no network and no `hanzo-zap` install.

This file used to lock the STAINLESS surface — `Hanzo`, `AsyncHanzo`, `Client`,
`Stream`, `HanzoError`, … — and import `Hanzo` at module scope. Every one of those
18 names was deleted by 648e7354 ("retire Stainless"), which replaced
`pkg/hanzoai` with openapi-generator output whose entry point is `ApiClient` +
`Configuration`. The import therefore raised at COLLECTION, so pytest reported an
error and ran none of the transport tests below — which is how the whole suite
stayed red through the 3.1.x releases without anyone seeing it. The lock now names
what the package actually exports.
"""

from __future__ import annotations

import json

import httpx

import hanzoai
from hanzoai import ZapTransport, AsyncZapTransport, zap_http_client
from hanzoai.zap import method_from_path

# The public surface that must never regress: the generated client's entry point
# and its error hierarchy. They live on `hanzoai.cloud`, which is the client —
# the package root re-exported a SECOND client's copies of these same nine names
# flat, so `hanzoai.ApiClient` and `hanzoai.cloud.ApiClient` were different
# classes talking to different documents under one spelling.
LOCKED_CORE_NAMES = {
    "ApiClient",
    "Configuration",
    "ApiResponse",
    "OpenApiException",
    "ApiException",
    "ApiTypeError",
    "ApiValueError",
    "ApiKeyError",
    "ApiAttributeError",
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
    import hanzoai.cloud

    missing = LOCKED_CORE_NAMES - set(hanzoai.cloud.__all__)
    assert not missing, f"locked names dropped from hanzoai.cloud.__all__: {missing}"


def test_core_names_are_not_also_flat_on_the_root() -> None:
    """One spelling, one class. These nine names existed on BOTH `hanzoai` and
    `hanzoai.cloud` as distinct classes bound to distinct documents, so which one
    a caller got depended on which import they happened to write."""
    also_flat = {n for n in LOCKED_CORE_NAMES if hasattr(hanzoai, n)}
    assert not also_flat, f"root re-exports a second client's {sorted(also_flat)}"


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


def test_full_httpx_client_routes_through_zap() -> None:
    """End-to-end through a real httpx.Client — the only seam ZAP actually has.

    It used to drive `hanzoai.Hanzo(..., http_client=...)`. That class is gone and
    nothing replaced the seam: the generated client's `rest.py` is urllib3, and no
    type in `pkg/hanzoai` takes an `http_client`. So `hanzoai.zap` is reachable
    only by a caller holding httpx directly, and that is what this asserts —
    honestly, rather than through a class that does not exist.
    """
    models_payload = {"object": "list", "data": [{"id": "zen-1"}, {"id": "zen-2"}]}
    mock = MockCloudClient(status=200, body=json.dumps(models_payload).encode("utf-8"))

    with httpx.Client(transport=ZapTransport(client=mock)) as http_client:
        response = http_client.get(
            "https://api.hanzo.ai/v1/models",
            headers={"Authorization": "Bearer sk-test"},
        )

    assert response.status_code == 200
    assert response.json() == models_payload
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
