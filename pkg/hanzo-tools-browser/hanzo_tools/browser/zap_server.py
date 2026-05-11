"""ZAP (Zero-latency Agent Protocol) server for hanzo-tools-browser.

Wire format and constants come from the canonical ``zap-protocol`` package
so every implementation in the stack stays byte-identical.

Discovery is mDNS-only per HIP-0069: the server binds an OS-assigned
ephemeral port and advertises it under ``_hanzo._tcp.local.`` via
``zap-mdns``. There is no well-known port pool, no lockfile arbitration,
and no shared config registry — clients (browser extensions, sibling
MCPs, agents) browse mDNS to find every live ZAP service on the LAN.

One ZapServer per hanzo-mcp process. Lifetime = MCP lifetime.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

# Wire format — single source of truth is the `zap-protocol` package
# (~/work/zap/zap-py). Import the constants instead of redefining them so
# any future change (e.g. MSG_STREAM, MAX_MESSAGE_SIZE) lands here for free.
from zap.protocol import (
    ZAP_MAGIC,
    HEADER_SIZE,
    MAX_MESSAGE_SIZE,
    MSG_HANDSHAKE,
    MSG_HANDSHAKE_OK,
    MSG_REQUEST,
    MSG_RESPONSE,
    MSG_PING,
    MSG_PONG,
    encode,
    decode,
)

# Browser-resolution preference (mirror cdp-bridge-server.ts)
DEFAULT_BROWSER_PREFERENCE: list[str] = ["firefox", "safari", "edge", "chrome"]

# How long an exclusive browser lease lasts unless explicitly extended.
DEFAULT_LEASE_TTL = 60.0


# ---------------------------------------------------------------------------
# Client tracking
# ---------------------------------------------------------------------------


@dataclass
class ZapClient:
    """A connected browser extension."""

    client_id: str
    browser: str
    version: str
    capabilities: list[str]
    ws: Any  # websockets.WebSocketServerProtocol — typed Any to avoid hard dep
    connected_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "browser": self.browser,
            "version": self.version,
            "capabilities": self.capabilities,
            "connected_at": self.connected_at,
            "last_active": self.last_active,
        }


@dataclass
class BrowserLease:
    """An exclusive lease on a browser client (sub-agent claim/release)."""

    client_id: str
    holder: str
    expires_at: float

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class ZapServer:
    """Single-port ZAP server hosted inside a hanzo-mcp process.

    One instance per Python MCP. Lifetime = MCP lifetime. Concurrent
    extensions register and dispatch independently.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        agent_label: Optional[str] = None,
        server_id: Optional[str] = None,
        request_timeout: float = 30.0,
    ):
        self.host = host
        self.agent_label = agent_label or os.environ.get("HANZO_AGENT_LABEL", "")
        # server_id is `mcp-py-<pid>-<4hex>`. PID alone collides across hosts on
        # the same LAN; the random suffix makes the name globally unique so
        # zeroconf never has to auto-rename to "(2)".
        self.server_id = server_id or f"mcp-py-{os.getpid()}-{uuid.uuid4().hex[:4]}"
        self.request_timeout = request_timeout

        self._port: Optional[int] = None
        self._server: Any = None  # websockets server
        self._mdns_handle: Any = None
        self._clients: dict[str, ZapClient] = {}
        self._ws_to_id: dict[Any, str] = {}
        self._pending: dict[str, asyncio.Future] = {}
        self._req_counter = 0
        self._leases: dict[str, BrowserLease] = {}  # client_id -> lease
        self._tools_manifest: list[dict] = [
            {
                "name": "browser",
                "description": "Hanzo browser tool (Python MCP, ZAP-native)",
                "inputSchema": {"type": "object"},
            }
        ]
        # Inbound RPC handler — set by hanzo-mcp at startup to expose its
        # full tool surface to extensions over the same socket. Without it,
        # incoming MSG_REQUEST calls get a noop ack (legacy behaviour).
        self._request_handler: Optional[Callable[[str, dict], Awaitable[Any]]] = None

    # ---- lifecycle ------------------------------------------------------

    async def start(self) -> Optional[int]:
        """Bind to an OS-assigned port and advertise it via mDNS.

        Discovery is mDNS-only (HIP-0069); the OS picks the port, mDNS
        carries it. No well-known port pool, no lockfile arbitration —
        every MCP gets its own ephemeral port and is found by browsing
        ``_hanzo._tcp.local.``.

        Returns the bound port, or ``None`` if either ``websockets`` or
        ``zap-mdns`` is missing.
        """
        try:
            import websockets  # noqa: F401
        except ImportError:
            logger.warning("websockets not installed; ZAP server disabled")
            return None
        try:
            import zap_mdns
        except ImportError:
            logger.error(
                "zap-mdns not installed; the server is unreachable without it. "
                "`pip install zap-mdns`."
            )
            return None

        from websockets.asyncio.server import serve as _serve

        async def _handler(websocket):
            await self._handle_connection(websocket)

        # Bind to port 0 → OS picks an ephemeral port. The actual port
        # comes back via the server's sockets attribute.
        self._server = await _serve(_handler, self.host, 0)
        sockets = getattr(self._server, "sockets", None) or []
        if not sockets:
            logger.error("zap: server has no sockets after start()")
            return None
        self._port = sockets[0].getsockname()[1]
        logger.info(
            "ZAP server listening on ws://%s:%d (mcp=%s, agent=%s)",
            self.host,
            self._port,
            self.server_id,
            self.agent_label or "?",
        )

        # mDNS publish — the only way clients find this server.
        # zeroconf.register_service blocks briefly setting up multicast,
        # so run it on a worker thread to avoid asyncio EventLoopBlocked.
        try:
            self._mdns_handle = await asyncio.to_thread(
                zap_mdns.publish,
                port=self._port,
                server_id=self.server_id,
                agent_label=self.agent_label or "",
                version="zap/1",
                capabilities=["mcp", "browser-bridge"],
            )
            logger.info("mDNS published %s on :%d", zap_mdns.SERVICE_TYPE, self._port)
        except Exception as e:
            logger.warning("mDNS publish failed: %s: %s", type(e).__name__, e)
            self._mdns_handle = None

        return self._port

    async def stop(self) -> None:
        """Gracefully shut down: retract mDNS, close clients, drop sockets."""
        # Retract mDNS announcement first so consumers see us go away.
        if self._mdns_handle is not None:
            try:
                self._mdns_handle.close()
            except Exception:
                pass
            self._mdns_handle = None

        if self._server is not None:
            self._server.close()
            try:
                await self._server.wait_closed()
            except Exception:
                pass
            self._server = None

        for client in list(self._clients.values()):
            try:
                await client.ws.close()
            except Exception:
                pass
        self._clients.clear()
        self._ws_to_id.clear()
        self._port = None

    # ---- public API -----------------------------------------------------

    def set_tools(self, tools: list[dict]) -> None:
        """Replace the advertised tool manifest (sent to clients on handshake)."""
        self._tools_manifest = list(tools)

    def set_request_handler(
        self, handler: Optional[Callable[[str, dict], Awaitable[Any]]]
    ) -> None:
        """Register / replace the inbound RPC handler. Receives (method, params),
        returns a JSON-serialisable result. Used by hanzo-mcp to expose its
        full tool surface to extensions over the same socket."""
        self._request_handler = handler

    @property
    def port(self) -> Optional[int]:
        return self._port

    @property
    def clients(self) -> list[ZapClient]:
        return list(self._clients.values())

    def has_client(self, browser: Optional[str] = None) -> bool:
        if not self._clients:
            return False
        if not browser:
            return True
        b = browser.lower()
        return any(b in c.browser.lower() for c in self._clients.values())

    def resolve_client(
        self,
        client_id: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> Optional[ZapClient]:
        """Pick which connected extension to dispatch to.

        Priority: explicit client_id > browser preference > most-recent-active
        > default browser preference list.
        """
        if client_id and client_id in self._clients:
            return self._clients[client_id]

        candidates = list(self._clients.values())
        if not candidates:
            return None

        if browser:
            b = browser.lower()
            matches = [c for c in candidates if b in c.browser.lower()]
            if not matches:
                return None
            return max(matches, key=lambda c: c.last_active)

        # No explicit selector: respect global default preference list.
        for pref in DEFAULT_BROWSER_PREFERENCE:
            matches = [c for c in candidates if pref in c.browser.lower()]
            if matches:
                return max(matches, key=lambda c: c.last_active)

        return max(candidates, key=lambda c: c.last_active)

    async def send(
        self,
        method: str,
        params: Optional[dict] = None,
        *,
        browser: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Send a method request to a connected extension and await result.

        Raises ``RuntimeError`` if no client matches.
        """
        client = self.resolve_client(client_id=client_id, browser=browser)
        if client is None:
            raise RuntimeError(
                f"No ZAP-connected browser extension"
                + (f" matching '{browser}'" if browser else "")
            )

        # Honour leases: if a different holder has a non-expired lease on this
        # client, reject.
        lease = self._leases.get(client.client_id)
        if lease and not lease.expired and lease.holder != self.server_id:
            raise RuntimeError(
                f"browser leased by {lease.holder} until {time.ctime(lease.expires_at)}"
            )

        req_id = self._next_req_id()
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = future
        client.last_active = time.time()

        try:
            await client.ws.send(
                encode(
                    MSG_REQUEST,
                    {"id": req_id, "method": method, "params": params or {}},
                )
            )
            return await asyncio.wait_for(
                future, timeout=timeout or self.request_timeout
            )
        finally:
            self._pending.pop(req_id, None)

    # ---- leases ---------------------------------------------------------

    def claim(self, client_id: str, ttl: float = DEFAULT_LEASE_TTL) -> BrowserLease:
        """Take an exclusive lease on a browser client for ``ttl`` seconds.

        Raises ``RuntimeError`` if already held by someone else.
        """
        lease = self._leases.get(client_id)
        if lease and not lease.expired and lease.holder != self.server_id:
            raise RuntimeError(
                f"already leased by {lease.holder} until {time.ctime(lease.expires_at)}"
            )
        new = BrowserLease(
            client_id=client_id,
            holder=self.server_id,
            expires_at=time.time() + ttl,
        )
        self._leases[client_id] = new
        return new

    def release(self, client_id: str) -> bool:
        """Release a lease this server holds. Returns True if released."""
        lease = self._leases.get(client_id)
        if lease and lease.holder == self.server_id:
            del self._leases[client_id]
            return True
        return False

    # ---- cluster discovery ---------------------------------------------
    # Cross-MCP visibility comes from mDNS, not a shared file. Use
    # ``zap_mdns.browse()`` to enumerate live MCPs on the LAN.

    @staticmethod
    def list_mcp_instances(timeout: float = 1.5) -> list[dict]:
        """Browse ``_hanzo._tcp.local.`` for every live ZAP service."""
        try:
            import zap_mdns
        except ImportError:
            return []
        return [
            {
                "server_id": s.server_id,
                "host": s.host,
                "port": s.port,
                "url": s.url,
                "agent_label": s.agent_label,
                "version": s.version,
                "capabilities": list(s.capabilities or []),
            }
            for s in zap_mdns.browse(timeout=timeout)
        ]

    # ---- ws handler -----------------------------------------------------

    async def _handle_connection(self, websocket: Any) -> None:
        try:
            async for raw in websocket:
                if not isinstance(raw, (bytes, bytearray)):
                    # Spec is binary frames; ignore stray text.
                    continue
                decoded = decode(bytes(raw))
                if decoded is None:
                    logger.debug("zap: malformed frame from %s", websocket)
                    continue
                msg_type, payload = decoded
                await self._dispatch(websocket, msg_type, payload or {})
        except Exception as e:
            # websockets normalises connection-closed via exception flow;
            # don't spam logs.
            logger.debug("zap connection ended: %s", e)
        finally:
            cid = self._ws_to_id.pop(websocket, None)
            if cid:
                existing = self._clients.get(cid)
                if existing is not None and existing.ws is websocket:
                    self._clients.pop(cid, None)
                    self._leases.pop(cid, None)
                    logger.info("zap: client disconnected %s", cid)
                else:
                    logger.debug(
                        "zap: stale ws %s for client %s — newer connection holds the slot",
                        websocket,
                        cid,
                    )

    async def _dispatch(self, websocket: Any, msg_type: int, payload: dict) -> None:
        if msg_type == MSG_HANDSHAKE:
            client_id = payload.get("clientId") or f"ext-{int(time.time() * 1000)}"
            client = ZapClient(
                client_id=client_id,
                browser=payload.get("browser", "unknown"),
                version=payload.get("version", "0"),
                capabilities=list(payload.get("capabilities") or []),
                ws=websocket,
            )
            self._clients[client_id] = client
            self._ws_to_id[websocket] = client_id
            logger.info(
                "zap: client connected %s (%s v%s, %d caps)",
                client_id,
                client.browser,
                client.version,
                len(client.capabilities),
            )
            await websocket.send(
                encode(
                    MSG_HANDSHAKE_OK,
                    {
                        "serverId": self.server_id,
                        "name": "hanzo-mcp",
                        "agentLabel": self.agent_label,
                        "tools": self._tools_manifest,
                    },
                )
            )
            return

        if msg_type == MSG_PING:
            await websocket.send(encode(MSG_PONG, {}))
            return

        if msg_type == MSG_PONG:
            return

        # MSG_RESPONSE: extension is answering an RPC we sent.
        if msg_type == MSG_RESPONSE:
            req_id = payload.get("id")
            future = self._pending.get(req_id) if req_id else None
            if future is None or future.done():
                return
            if "error" in payload and payload["error"]:
                err = payload["error"]
                msg = err.get("message") if isinstance(err, dict) else str(err)
                future.set_exception(RuntimeError(msg or "ZAP error"))
            else:
                future.set_result(payload.get("result"))
            return

        # MSG_REQUEST: extension is calling US — most commonly because the
        # extension wants to invoke an MCP tool exposed by this server. Route
        # via the registered request_handler (set by hanzo-mcp at startup).
        # Without a handler, fall back to noop ack (legacy notifications).
        if msg_type == MSG_REQUEST:
            req_id = payload.get("id")
            method = payload.get("method", "")
            params = payload.get("params") or {}
            cid = self._ws_to_id.get(websocket)
            if cid and cid in self._clients:
                self._clients[cid].last_active = time.time()
            if req_id is None:
                # Notification — no response expected.
                return
            handler = self._request_handler
            if handler is None:
                await websocket.send(
                    encode(
                        MSG_RESPONSE,
                        {"id": req_id, "result": {"ack": True, "method": method}},
                    )
                )
                return
            try:
                result = await handler(method, params)
                await websocket.send(
                    encode(MSG_RESPONSE, {"id": req_id, "result": result})
                )
            except Exception as e:
                await websocket.send(
                    encode(
                        MSG_RESPONSE,
                        {
                            "id": req_id,
                            "error": {
                                "code": -1,
                                "message": f"{type(e).__name__}: {e}",
                            },
                        },
                    )
                )
            return

        logger.debug("zap: unknown msg type 0x%02x", msg_type)

    def _next_req_id(self) -> str:
        self._req_counter += 1
        return f"py-{self._req_counter}"


# ---------------------------------------------------------------------------
# Process-wide singleton (one ZAP server per hanzo-mcp)
# ---------------------------------------------------------------------------


_singleton: Optional[ZapServer] = None
_singleton_lock = asyncio.Lock()


async def get_or_start_server(
    *,
    host: str = "127.0.0.1",
    agent_label: Optional[str] = None,
) -> Optional[ZapServer]:
    """Return the process-wide ZAP server, starting it if needed.

    Returns ``None`` if either ``websockets`` or ``zap-mdns`` is missing.
    """
    global _singleton
    async with _singleton_lock:
        if _singleton is not None and _singleton.port is not None:
            return _singleton
        srv = ZapServer(host=host, agent_label=agent_label)
        port = await srv.start()
        if port is None:
            return None
        _singleton = srv
        return srv


def get_server() -> Optional[ZapServer]:
    """Return the current singleton (or None if not started)."""
    return _singleton


async def shutdown_server() -> None:
    global _singleton
    async with _singleton_lock:
        if _singleton is not None:
            await _singleton.stop()
            _singleton = None


__all__ = [
    "ZapClient",
    "ZapServer",
    "BrowserLease",
    "DEFAULT_BROWSER_PREFERENCE",
    "DEFAULT_LEASE_TTL",
    "MSG_HANDSHAKE",
    "MSG_HANDSHAKE_OK",
    "MSG_REQUEST",
    "MSG_RESPONSE",
    "MSG_PING",
    "MSG_PONG",
    "ZAP_MAGIC",
    "encode",
    "decode",
    "get_or_start_server",
    "get_server",
    "shutdown_server",
]
