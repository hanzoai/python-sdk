"""ZAP (Zero-latency Agent Protocol) server for hanzo-tools-browser.

Wire format (compatible with @hanzo/browser-extension/src/shared/zap.ts):
    [0x5A 0x41 0x50 0x01][type:1][length:4 BE][JSON payload]

Message types:
    MSG_HANDSHAKE    = 0x01  client -> server
    MSG_HANDSHAKE_OK = 0x02  server -> client
    MSG_REQUEST      = 0x10  bidirectional
    MSG_RESPONSE     = 0x11  bidirectional
    MSG_PING         = 0xFE
    MSG_PONG         = 0xFF

Each hanzo-mcp process runs ONE ZapServer that:
1. Claims the lowest free port from [9999, 9998, 9997, 9996, 9995] using a
   POSIX flock at ~/.hanzo/extension/zap-{port}.lock so multiple MCPs don't
   collide.
2. Accepts WebSocket connections from browser extensions, registers them by
   {client_id, browser, version, capabilities, ws}.
3. Exposes ``send(method, params, browser=None, client_id=None)`` for the
   browser tool to dispatch RPC calls into a connected extension.
4. Persists its presence to ~/.hanzo/extension/config.json:mcp_instances so
   sibling MCPs can introspect the cluster.
"""

from __future__ import annotations

import asyncio
import errno
import fcntl
import json
import logging
import os
import socket
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

# Wire format constants (canonical: shared/zap.ts)
ZAP_MAGIC = b"\x5a\x41\x50\x01"
HEADER_SIZE = 9  # 4 magic + 1 type + 4 length

MSG_HANDSHAKE = 0x01
MSG_HANDSHAKE_OK = 0x02
MSG_REQUEST = 0x10
MSG_RESPONSE = 0x11
MSG_PING = 0xFE
MSG_PONG = 0xFF

# Port preference (lowest first; matches DEFAULT_ZAP_PORTS in shared/zap.ts)
DEFAULT_ZAP_PORTS: list[int] = [9999, 9998, 9997, 9996, 9995]

# Browser-resolution preference (mirror cdp-bridge-server.ts)
DEFAULT_BROWSER_PREFERENCE: list[str] = ["firefox", "safari", "edge", "chrome"]

# How long an exclusive browser lease lasts unless explicitly extended.
DEFAULT_LEASE_TTL = 60.0


# ---------------------------------------------------------------------------
# Wire format
# ---------------------------------------------------------------------------


def encode(msg_type: int, payload: Any) -> bytes:
    """Encode a ZAP frame.

    JSON-encoded payload, length-prefixed, big-endian.
    """
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return ZAP_MAGIC + bytes([msg_type]) + struct.pack(">I", len(body)) + body


def decode(data: bytes) -> Optional[tuple[int, Any]]:
    """Decode a single ZAP frame. Returns ``None`` for malformed input.

    Caller must hand a complete frame (websockets.recv() guarantees this for
    binary messages — frame == one ws message).
    """
    if len(data) < HEADER_SIZE:
        return None
    if data[0:4] != ZAP_MAGIC:
        return None
    msg_type = data[4]
    (length,) = struct.unpack(">I", data[5:9])
    if len(data) < HEADER_SIZE + length:
        return None
    body = data[HEADER_SIZE : HEADER_SIZE + length]
    payload = json.loads(body.decode("utf-8")) if length else None
    return msg_type, payload


# ---------------------------------------------------------------------------
# Lock file (cross-MCP port arbitration)
# ---------------------------------------------------------------------------


def _lock_dir() -> Path:
    d = Path.home() / ".hanzo" / "extension"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _claim_port_lock(port: int) -> Optional[int]:
    """Try to acquire an exclusive flock on ``zap-{port}.lock``.

    Returns the open file descriptor on success, ``None`` if another
    process already holds it. The fd must be kept open for the lifetime
    of the server (closing releases the lock).
    """
    lock_path = _lock_dir() / f"zap-{port}.lock"
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        os.close(fd)
        if e.errno in (errno.EWOULDBLOCK, errno.EACCES):
            return None
        raise
    # Write our pid so the file is informative
    os.ftruncate(fd, 0)
    os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
    return fd


def _release_port_lock(fd: Optional[int]) -> None:
    if fd is not None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(fd)
        except OSError:
            pass


def _port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    """Best-effort TCP probe — does a bind succeed?"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        s.close()
        return False


# ---------------------------------------------------------------------------
# Shared config (~/.hanzo/extension/config.json)
# ---------------------------------------------------------------------------


def _config_path() -> Path:
    return _lock_dir() / "config.json"


def _config_lock_path() -> Path:
    return _lock_dir() / "config.json.lock"


def _read_config() -> dict:
    p = _config_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _atomic_update_config(mutate: Callable[[dict], None]) -> dict:
    """Read-modify-write ~/.hanzo/extension/config.json under fcntl flock."""
    lock_path = _config_lock_path()
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        cfg = _read_config()
        mutate(cfg)
        tmp = _config_path().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, indent=2))
        os.replace(tmp, _config_path())
        return cfg
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(lock_fd)


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
        ports: Optional[list[int]] = None,
        agent_label: Optional[str] = None,
        server_id: Optional[str] = None,
        request_timeout: float = 30.0,
    ):
        self.host = host
        self.ports = list(ports or DEFAULT_ZAP_PORTS)
        self.agent_label = agent_label or os.environ.get("HANZO_AGENT_LABEL", "")
        self.server_id = server_id or f"mcp-py-{os.getpid()}"
        self.request_timeout = request_timeout

        self._port: Optional[int] = None
        self._lock_fd: Optional[int] = None
        self._server: Any = None  # websockets server
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

    # ---- lifecycle ------------------------------------------------------

    async def start(self) -> Optional[int]:
        """Bind to the lowest-numbered free port. Returns port or None."""
        try:
            import websockets  # noqa: F401
        except ImportError:
            logger.warning("websockets not installed; ZAP server disabled")
            return None

        for port in self.ports:
            fd = _claim_port_lock(port)
            if fd is None:
                logger.debug("zap port %d already locked by another mcp", port)
                continue
            if not _port_is_free(port, self.host):
                _release_port_lock(fd)
                logger.debug("zap port %d in use (no lock but socket bound)", port)
                continue
            try:
                from websockets.asyncio.server import serve as _serve

                async def _handler(websocket):
                    await self._handle_connection(websocket)

                self._server = await _serve(_handler, self.host, port)
            except ImportError:
                # Older websockets API (< 13)
                from websockets.server import serve as _serve  # type: ignore

                async def _handler_legacy(websocket, _path):
                    await self._handle_connection(websocket)

                self._server = await _serve(_handler_legacy, self.host, port)  # type: ignore
            except OSError as e:
                _release_port_lock(fd)
                logger.debug("zap bind on %d failed: %s", port, e)
                continue

            self._port = port
            self._lock_fd = fd
            self._register_in_config()
            logger.info(
                "ZAP server listening on ws://%s:%d (mcp=%s, agent=%s)",
                self.host,
                port,
                self.server_id,
                self.agent_label or "?",
            )
            # Best-effort mDNS publish so LAN-wide consumers can find us
            # without hard-coded ports. No-op if `hanzo-zap-mdns` (which
            # owns the zeroconf dep) isn't installed.
            self._mdns_handle = None
            try:
                import hanzo_zap_mdns
                # zeroconf's register_service blocks the event loop briefly
                # while it sets up the multicast socket; from inside an
                # asyncio coroutine that triggers EventLoopBlocked. Run on
                # a worker thread so it never sees our loop.
                self._mdns_handle = await asyncio.to_thread(
                    hanzo_zap_mdns.publish,
                    port=port,
                    server_id=self.server_id,
                    agent_label=self.agent_label or "",
                    version="zap/1",
                    capabilities=["mcp", "browser-bridge"],
                )
                logger.info("mDNS published _hanzo-zap._tcp.local. on :%d", port)
            except ImportError:
                logger.debug("hanzo-zap-mdns not installed; mDNS publish skipped")
            except Exception as _e:
                logger.warning("mDNS publish failed: %s: %s", type(_e).__name__, _e)
            return port

        logger.warning("ZAP: no free port in %s", self.ports)
        return None

    async def stop(self) -> None:
        """Gracefully shut down: close clients, release lock, drop registry entry."""
        # Retract mDNS announcement first so consumers see us go away.
        try:
            if getattr(self, "_mdns_handle", None) is not None:
                self._mdns_handle.close()
                self._mdns_handle = None
        except Exception:
            pass
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

        self._unregister_from_config()
        _release_port_lock(self._lock_fd)
        self._lock_fd = None
        self._port = None

    # ---- public API -----------------------------------------------------

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
                encode(MSG_REQUEST, {"id": req_id, "method": method, "params": params or {}})
            )
            return await asyncio.wait_for(future, timeout=timeout or self.request_timeout)
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

    # ---- registry (cross-MCP visibility) -------------------------------

    def _register_in_config(self) -> None:
        def mut(cfg: dict) -> None:
            instances = cfg.setdefault("mcp_instances", [])
            # purge stale (dead pids) and any prior entry for our own
            # (pid, port). In production each MCP is its own process so
            # de-dup by pid alone would suffice; we key on (pid, port) so
            # tests and edge cases that bring up two ZAP servers under one
            # pid both stay visible.
            instances[:] = [
                i
                for i in instances
                if _pid_alive(i.get("pid"))
                and not (i.get("pid") == os.getpid() and i.get("port") == self._port)
            ]
            instances.append(
                {
                    "port": self._port,
                    "pid": os.getpid(),
                    "started_at": time.time(),
                    "agent_label": self.agent_label,
                    "server_id": self.server_id,
                }
            )

        try:
            _atomic_update_config(mut)
        except Exception as e:
            logger.warning("config registry write failed: %s", e)

    def _unregister_from_config(self) -> None:
        target_pid = os.getpid()
        target_port = self._port

        def mut(cfg: dict) -> None:
            instances = cfg.get("mcp_instances", [])
            cfg["mcp_instances"] = [
                i
                for i in instances
                if not (i.get("pid") == target_pid and i.get("port") == target_port)
            ]

        try:
            _atomic_update_config(mut)
        except Exception:
            pass

    @staticmethod
    def list_mcp_instances() -> list[dict]:
        """Read the cluster registry (filters dead pids)."""
        cfg = _read_config()
        instances = cfg.get("mcp_instances", [])
        return [i for i in instances if _pid_alive(i.get("pid"))]

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

        # MSG_REQUEST: extension is calling US (notifications/elementSelected,
        # etc.). Acknowledge so the protocol doesn't block.
        if msg_type == MSG_REQUEST:
            req_id = payload.get("id")
            method = payload.get("method", "")
            # Update last_active
            cid = self._ws_to_id.get(websocket)
            if cid and cid in self._clients:
                self._clients[cid].last_active = time.time()
            # Notifications are fire-and-forget; everything else gets a stub
            # acknowledgement (caller can still install custom handlers via
            # ``on_request`` if needed).
            if req_id is not None:
                await websocket.send(encode(MSG_RESPONSE, {"id": req_id, "result": {"ack": True, "method": method}}))
            return

        logger.debug("zap: unknown msg type 0x%02x", msg_type)

    def _next_req_id(self) -> str:
        self._req_counter += 1
        return f"py-{self._req_counter}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pid_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError as e:
        # ESRCH = no such process; EPERM = exists but not ours
        return e.errno == errno.EPERM


# ---------------------------------------------------------------------------
# Process-wide singleton (one ZAP server per hanzo-mcp)
# ---------------------------------------------------------------------------


_singleton: Optional[ZapServer] = None
_singleton_lock = asyncio.Lock()


async def get_or_start_server(
    *,
    host: str = "127.0.0.1",
    ports: Optional[list[int]] = None,
    agent_label: Optional[str] = None,
) -> Optional[ZapServer]:
    """Return the process-wide ZAP server, starting it if needed.

    Returns ``None`` if no port could be bound (other MCPs hold all 5).
    """
    global _singleton
    async with _singleton_lock:
        if _singleton is not None and _singleton.port is not None:
            return _singleton
        srv = ZapServer(host=host, ports=ports, agent_label=agent_label)
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
    "DEFAULT_ZAP_PORTS",
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
