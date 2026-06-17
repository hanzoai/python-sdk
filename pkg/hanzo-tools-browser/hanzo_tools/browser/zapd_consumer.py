"""hanzo-mcp as a zapd consumer — native ZAP, no in-process server.

The browser tool no longer hosts anything. It connects to the one shared local
router at ``~/.zap/run/zapd.sock`` as a *consumer*, lists providers, and routes
opaque commands to a ``browser:*`` provider. No WebSocket, no mDNS, no CDP
bridge, no :9224, no Playwright fallback for native-browser mode.

The wire is the binary ZAP router envelope (mirrors zapd's ``frame.rs``); the
browser command payload is the compact binary codec shared with the extension.
"""
from __future__ import annotations

import os
import socket
import struct
import threading
from typing import Optional

# Envelope types (match frame.rs).
HELLO, WELCOME, PROVIDERS_LIST, PROVIDERS = 1, 2, 3, 4
PEER_CONNECTED, PEER_DISCONNECTED, ERROR = 5, 6, 7
ROUTE, RESPONSE, EVENT = 16, 17, 18
ROLE_CONSUMER = 2


def socket_path() -> str:
    p = os.environ.get("ZAP_SOCK")
    if p:
        return p
    xrd = os.environ.get("XDG_RUNTIME_DIR")
    if xrd:
        return os.path.join(xrd, "zap", "zapd.sock")
    return os.path.expanduser("~/.zap/run/zapd.sock")


def _put_str(s: str) -> bytes:
    b = s.encode()
    return struct.pack("<H", len(b)) + b


def _encode_frame(typ, frm, to, payload=b"", flags=0) -> bytes:
    fb, tb = frm.encode(), to.encode()
    body = struct.pack("<BHHHI", typ, flags, len(fb), len(tb), len(payload)) + fb + tb + payload
    return struct.pack("<I", len(body)) + body


def _hello_payload(role, brand, caps) -> bytes:
    b = bytes([role]) + _put_str(brand) + struct.pack("<H", len(caps))
    for c in caps:
        b += _put_str(c)
    return b


def _encode_cmd(method: str, params: dict) -> bytes:
    b = _put_str(method) + struct.pack("<H", len(params))
    for k, v in params.items():
        vb = v.encode() if isinstance(v, str) else bytes(v)
        b += _put_str(k) + struct.pack("<I", len(vb)) + vb
    return b


def _parse_providers(pay: bytes):
    (n,) = struct.unpack_from("<H", pay, 0)
    o = 2
    out = []
    for _ in range(n):
        (idl,) = struct.unpack_from("<H", pay, o); o += 2
        pid = pay[o : o + idl].decode(); o += idl
        role = pay[o]; o += 1
        (bl,) = struct.unpack_from("<H", pay, o); o += 2
        brand = pay[o : o + bl].decode(); o += bl
        (cn,) = struct.unpack_from("<H", pay, o); o += 2
        caps = []
        for _ in range(cn):
            (cl,) = struct.unpack_from("<H", pay, o); o += 2
            caps.append(pay[o : o + cl].decode()); o += cl
        out.append({"id": pid, "role": role, "brand": brand, "caps": caps})
    return out


class ZapdConsumer:
    """A persistent consumer connection to the local zapd router."""

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"consumer:hanzo-mcp/{os.getpid()}"
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        if self._sock is not None:
            return True
        try:
            s = socket.socket(socket.AF_UNIX)
            s.settimeout(5)
            s.connect(socket_path())
            s.sendall(_encode_frame(HELLO, self.agent_id, "", _hello_payload(ROLE_CONSUMER, "hanzo", [])))
            self._sock = s
            self._read_until(WELCOME)
            return True
        except OSError:
            self._sock = None
            return False

    def _recvn(self, n) -> bytes:
        buf = b""
        while len(buf) < n:
            c = self._sock.recv(n - len(buf))
            if not c:
                raise EOFError("zapd closed")
            buf += c
        return buf

    def _read_frame(self) -> dict:
        (length,) = struct.unpack("<I", self._recvn(4))
        buf = self._recvn(length)
        typ, flags, fl, tl, pl = struct.unpack_from("<BHHHI", buf, 0)
        o = 11
        frm = buf[o : o + fl].decode(); o += fl
        to = buf[o : o + tl].decode(); o += tl
        return {"t": typ, "from": frm, "to": to, "payload": buf[o : o + pl]}

    def _read_until(self, want, from_id=None) -> dict:
        for _ in range(100):
            f = self._read_frame()
            if f["t"] == want and (from_id is None or f["from"] == from_id):
                return f
            if f["t"] == ERROR:
                raise RuntimeError(f["payload"].decode(errors="replace"))
        raise TimeoutError(f"no frame type {want}")

    def list_providers(self, brand: str = "") -> list:
        with self._lock:
            if not self.connect():
                return []
            payload = _put_str(brand) if brand else b""
            self._sock.sendall(_encode_frame(PROVIDERS_LIST, self.agent_id, "", payload))
            f = self._read_until(PROVIDERS)
            return _parse_providers(f["payload"])

    def resolve_browser(self, browser: Optional[str], client_id: Optional[str]) -> Optional[str]:
        provs = [p for p in self.list_providers() if p["id"].startswith("browser:")]
        if client_id:
            for p in provs:
                if p["id"] == client_id:
                    return p["id"]
        if browser:
            for p in provs:
                # match "browser:chrome/..." against browser="chrome"
                if p["id"].split(":", 1)[1].split("/", 1)[0] == browser.lower():
                    return p["id"]
            return None
        return provs[0]["id"] if provs else None

    def route(self, provider_id: str, method: str, params: dict, timeout: float = 30.0) -> bytes:
        with self._lock:
            if not self.connect():
                raise RuntimeError("zapd not reachable")
            self._sock.settimeout(timeout)
            self._sock.sendall(_encode_frame(ROUTE, self.agent_id, provider_id, _encode_cmd(method, params)))
            f = self._read_until(RESPONSE, from_id=provider_id)
            return f["payload"]

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None


_consumer: Optional[ZapdConsumer] = None


def get_consumer() -> Optional[ZapdConsumer]:
    """Return the shared consumer if zapd is reachable, else None."""
    global _consumer
    if _consumer is None:
        _consumer = ZapdConsumer()
    return _consumer if _consumer.connect() else None
