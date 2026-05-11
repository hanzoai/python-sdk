"""Tests for hanzo_tools.browser.zap_server.

Covers:
- Wire format encode/decode round-trip and parity with shared/zap.ts.
- Server bind on OS-assigned port (HIP-0069: mDNS-only discovery).
- Mock extension client: register, send response to RPC, ping/pong.
- Browser resolution priority (client_id > browser > default preference).
- Browser leases (claim / release / reject when held by other holder).
"""

from __future__ import annotations

import asyncio
import json
import struct
import time

import pytest
import websockets
from websockets.asyncio.client import connect as ws_connect

from hanzo_tools.browser import zap_server as zs


# ---------------------------------------------------------------------------
# Wire format
# ---------------------------------------------------------------------------


class TestWireFormat:
    def test_magic(self):
        assert zs.ZAP_MAGIC == b"\x5a\x41\x50\x01"

    def test_constants_match_extension(self):
        # Must stay locked to shared/zap.ts canonical values.
        assert zs.MSG_HANDSHAKE == 0x01
        assert zs.MSG_HANDSHAKE_OK == 0x02
        assert zs.MSG_REQUEST == 0x10
        assert zs.MSG_RESPONSE == 0x11
        assert zs.MSG_PING == 0xFE
        assert zs.MSG_PONG == 0xFF

    def test_encode_layout(self):
        from zap.protocol import HEADER_SIZE

        frame = zs.encode(zs.MSG_REQUEST, {"id": "x", "method": "y"})
        assert frame[:4] == zs.ZAP_MAGIC
        assert frame[4] == zs.MSG_REQUEST
        (length,) = struct.unpack(">I", frame[5:9])
        assert length == len(frame) - HEADER_SIZE
        assert json.loads(frame[9:].decode()) == {"id": "x", "method": "y"}

    def test_round_trip(self):
        for msg_type in (
            zs.MSG_HANDSHAKE,
            zs.MSG_HANDSHAKE_OK,
            zs.MSG_REQUEST,
            zs.MSG_RESPONSE,
            zs.MSG_PING,
            zs.MSG_PONG,
        ):
            payload = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
            decoded = zs.decode(zs.encode(msg_type, payload))
            assert decoded is not None
            assert decoded[0] == msg_type
            assert decoded[1] == payload

    def test_decode_rejects_bad_magic(self):
        bad = b"\xff\xff\xff\xff" + b"\x10" + struct.pack(">I", 0)
        assert zs.decode(bad) is None

    def test_decode_rejects_short_frame(self):
        assert zs.decode(b"") is None
        assert zs.decode(b"\x5a\x41\x50") is None

    def test_decode_handles_empty_payload(self):
        frame = zs.encode(zs.MSG_PING, {})
        decoded = zs.decode(frame)
        assert decoded is not None and decoded[1] == {}


# ---------------------------------------------------------------------------
# Helpers — mock extension client
# ---------------------------------------------------------------------------


class MockExtensionClient:
    """Minimal browser-extension client speaking ZAP wire format.

    Registers on connect, exposes ``response_handler`` so tests can react
    to inbound MSG_REQUEST and reply with MSG_RESPONSE.
    """

    def __init__(self, port: int, *, browser: str = "firefox", client_id: str | None = None):
        self.port = port
        self.browser = browser
        self.client_id = client_id or f"ext-test-{int(time.time() * 1000)}"
        self.ws: websockets.ClientConnection | None = None
        self.received: list[tuple[int, dict]] = []
        self.handshake_ok: dict | None = None
        self._task: asyncio.Task | None = None
        self.response_handler: callable | None = None

    async def connect(self) -> None:
        self.ws = await ws_connect(f"ws://127.0.0.1:{self.port}")
        await self.ws.send(
            zs.encode(
                zs.MSG_HANDSHAKE,
                {
                    "clientId": self.client_id,
                    "clientType": "browser_extension",
                    "browser": self.browser,
                    "version": "test-0.0",
                    "capabilities": ["navigate", "evaluate", "click"],
                },
            )
        )
        # Wait for HANDSHAKE_OK
        raw = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
        decoded = zs.decode(bytes(raw))
        assert decoded is not None and decoded[0] == zs.MSG_HANDSHAKE_OK
        self.handshake_ok = decoded[1]
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        assert self.ws is not None
        try:
            async for raw in self.ws:
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                decoded = zs.decode(bytes(raw))
                if decoded is None:
                    continue
                msg_type, payload = decoded
                self.received.append((msg_type, payload or {}))
                if msg_type == zs.MSG_REQUEST and self.response_handler is not None:
                    method = payload.get("method") if payload else ""
                    params = payload.get("params") if payload else {}
                    req_id = payload.get("id") if payload else None
                    try:
                        result = self.response_handler(method, params)
                        if asyncio.iscoroutine(result):
                            result = await result
                        await self.ws.send(zs.encode(zs.MSG_RESPONSE, {"id": req_id, "result": result}))
                    except Exception as e:
                        await self.ws.send(
                            zs.encode(zs.MSG_RESPONSE, {"id": req_id, "error": {"code": -1, "message": str(e)}})
                        )
                elif msg_type == zs.MSG_PING:
                    await self.ws.send(zs.encode(zs.MSG_PONG, {}))
        except Exception:
            pass

    async def close(self) -> None:
        if self._task:
            self._task.cancel()
        if self.ws:
            await self.ws.close()


# ---------------------------------------------------------------------------
# Server fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def server():
    """A live ZapServer on an OS-assigned port. mDNS publish is best-effort
    — if zap-mdns is unavailable the start() returns None, and the test
    is skipped (CI without zeroconf shouldn't hard-fail)."""
    srv = zs.ZapServer()
    port = await srv.start()
    if port is None:
        pytest.skip("ZapServer.start() returned None — zap-mdns/websockets missing")
    yield srv
    await srv.stop()


@pytest.fixture
async def client(server):
    c = MockExtensionClient(server.port)
    await c.connect()
    # Allow the server to register the connection
    await asyncio.sleep(0.05)
    yield c
    await c.close()


# ---------------------------------------------------------------------------
# Bind / shutdown
# ---------------------------------------------------------------------------


class TestServerLifecycle:
    async def test_binds_on_ephemeral_port(self):
        srv = zs.ZapServer()
        port = await srv.start()
        if port is None:
            pytest.skip("zap-mdns/websockets missing")
        try:
            assert isinstance(port, int) and port > 0
            assert srv.port == port
        finally:
            await srv.stop()

    async def test_two_servers_get_distinct_ports(self):
        a = zs.ZapServer()
        b = zs.ZapServer()
        try:
            port_a = await a.start()
            port_b = await b.start()
            if port_a is None or port_b is None:
                pytest.skip("zap-mdns/websockets missing")
            assert port_a != port_b
        finally:
            await a.stop()
            await b.stop()

    async def test_stop_clears_port(self):
        srv = zs.ZapServer()
        port = await srv.start()
        if port is None:
            pytest.skip("zap-mdns/websockets missing")
        await srv.stop()
        assert srv.port is None


# ---------------------------------------------------------------------------
# Handshake / client registry
# ---------------------------------------------------------------------------


class TestClientRegistry:
    async def test_handshake_registers_client(self, server, client):
        assert server.has_client()
        assert server.has_client(browser="firefox")
        assert not server.has_client(browser="chrome")
        assert len(server.clients) == 1
        assert server.clients[0].browser == "firefox"
        assert server.clients[0].client_id == client.client_id

    async def test_handshake_ok_includes_server_id_and_tools(self, server, client):
        assert client.handshake_ok is not None
        assert client.handshake_ok["serverId"] == server.server_id
        assert isinstance(client.handshake_ok["tools"], list)
        assert any(t["name"] == "browser" for t in client.handshake_ok["tools"])

    async def test_disconnect_removes_client(self, server):
        c = MockExtensionClient(server.port)
        await c.connect()
        await asyncio.sleep(0.05)
        assert server.has_client()
        await c.close()
        # Allow server cleanup
        await asyncio.sleep(0.1)
        assert not server.has_client()


# ---------------------------------------------------------------------------
# RPC dispatch
# ---------------------------------------------------------------------------


class TestRpcDispatch:
    async def test_send_round_trips_to_extension(self, server, client):
        async def handler(method, params):
            assert method == "Page.navigate"
            assert params == {"url": "https://example.com"}
            return {"frameId": "main"}

        client.response_handler = handler
        result = await server.send("Page.navigate", {"url": "https://example.com"})
        assert result == {"frameId": "main"}

    async def test_extension_error_propagates(self, server, client):
        async def handler(method, params):
            raise RuntimeError("nope")

        client.response_handler = handler
        with pytest.raises(RuntimeError, match="nope"):
            await server.send("hanzo.click", {"selector": "#x"})

    async def test_send_with_browser_filter(self, server):
        c1 = MockExtensionClient(server.port, browser="firefox", client_id="ff-1")
        c2 = MockExtensionClient(server.port, browser="chrome", client_id="ch-1")
        await c1.connect()
        await c2.connect()
        await asyncio.sleep(0.05)

        c1.response_handler = lambda m, p: "from-firefox"
        c2.response_handler = lambda m, p: "from-chrome"

        try:
            assert await server.send("any", {}, browser="firefox") == "from-firefox"
            assert await server.send("any", {}, browser="chrome") == "from-chrome"
        finally:
            await c1.close()
            await c2.close()

    async def test_no_match_raises(self, server, client):
        # client is firefox; ask for chrome
        with pytest.raises(RuntimeError, match="No ZAP-connected"):
            await server.send("any", {}, browser="chrome")

    async def test_ping_pong(self, server, client):
        # Send ping and verify server echoes pong; just ensure no crash.
        await client.ws.send(zs.encode(zs.MSG_PING, {}))
        # Receive pong
        await asyncio.sleep(0.05)
        # Server replies with MSG_PONG (we caught it in client.received via _run)
        types = [t for t, _ in client.received]
        assert zs.MSG_PONG in types

    async def test_extension_initiated_request_acked(self, server, client):
        # Extension sends MSG_REQUEST as a notification (server must ack)
        await client.ws.send(zs.encode(zs.MSG_REQUEST, {"id": "evt-1", "method": "notifications/elementSelected", "params": {"x": 1}}))
        await asyncio.sleep(0.1)
        # Find the response
        responses = [p for t, p in client.received if t == zs.MSG_RESPONSE]
        assert any(r.get("id") == "evt-1" for r in responses)


# ---------------------------------------------------------------------------
# Resolution priority
# ---------------------------------------------------------------------------


class TestResolution:
    async def test_resolve_explicit_client_id(self, server):
        c1 = MockExtensionClient(server.port, browser="firefox", client_id="ff-1")
        c2 = MockExtensionClient(server.port, browser="firefox", client_id="ff-2")
        await c1.connect()
        await c2.connect()
        await asyncio.sleep(0.05)
        try:
            picked = server.resolve_client(client_id="ff-2")
            assert picked is not None and picked.client_id == "ff-2"
        finally:
            await c1.close()
            await c2.close()

    async def test_default_prefers_firefox(self, server):
        chrome = MockExtensionClient(server.port, browser="chrome", client_id="ch")
        firefox = MockExtensionClient(server.port, browser="firefox", client_id="ff")
        await chrome.connect()
        await firefox.connect()
        await asyncio.sleep(0.05)
        try:
            picked = server.resolve_client()
            assert picked is not None and "firefox" in picked.browser
        finally:
            await chrome.close()
            await firefox.close()


# ---------------------------------------------------------------------------
# Leases
# ---------------------------------------------------------------------------


class TestLeases:
    async def test_claim_and_release(self, server, client):
        lease = server.claim(client.client_id, ttl=10)
        assert lease.client_id == client.client_id
        assert lease.holder == server.server_id
        assert server.release(client.client_id) is True

    async def test_claim_rejects_when_held_by_other(self, server, client):
        # First grab from server
        server.claim(client.client_id, ttl=10)
        # Synthesise a different "holder" by mutating server_id; this is the
        # closest we can get without spinning up a second ZapServer.
        original = server.server_id
        try:
            server.server_id = "other-mcp"
            with pytest.raises(RuntimeError, match="already leased"):
                server.claim(client.client_id, ttl=10)
        finally:
            server.server_id = original

    async def test_release_only_works_for_holder(self, server, client):
        server.claim(client.client_id, ttl=10)
        original = server.server_id
        try:
            server.server_id = "other-mcp"
            assert server.release(client.client_id) is False
        finally:
            server.server_id = original

    async def test_send_blocked_by_other_holder(self, server, client):
        # Hold with a different holder
        from hanzo_tools.browser.zap_server import BrowserLease

        server._leases[client.client_id] = BrowserLease(
            client_id=client.client_id,
            holder="someone-else",
            expires_at=time.time() + 30,
        )
        with pytest.raises(RuntimeError, match="leased by"):
            await server.send("any", {})


# ---------------------------------------------------------------------------
# Cluster discovery (mDNS — best-effort, may be empty in CI)
# ---------------------------------------------------------------------------


class TestClusterDiscovery:
    async def test_list_mcp_instances_returns_list(self, server):
        # mDNS browse may return [] in containers without multicast routing.
        # We just assert the call shape is correct.
        instances = zs.ZapServer.list_mcp_instances(timeout=0.5)
        assert isinstance(instances, list)
        for entry in instances:
            assert "server_id" in entry
            assert "host" in entry
            assert "port" in entry
            assert "url" in entry
