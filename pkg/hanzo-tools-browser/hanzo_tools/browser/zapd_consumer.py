"""hanzo-mcp as a zapd consumer — native ZAP, no in-process server.

The browser tool no longer hosts anything. It connects to the one shared local
router at ``~/.zap/run/zapd.sock`` as a *consumer*, lists providers, and routes
opaque commands to a ``browser:*`` provider. No WebSocket, no mDNS, no CDP
bridge, no :9224, no Playwright fallback for native-browser mode.

The router envelope and its control bodies (HELLO/WELCOME/PROVIDERS/ROUTE/…) are
NOT reimplemented here — they come from the canonical ``zap`` package
(``zap.frame`` + :class:`zap.ZapClient`), the one Python copy of the wire. This
module is a thin *policy* layer over that client: lazy connect, provider
resolution for ``browser:*``, and the method+params convenience for routing.

The only codec that lives here is the end-to-end **browser command payload**
(:func:`_encode_cmd`). The router forwards it opaquely; the peer that decodes it
is the browser extension (``extension/.../shared/native-zap.ts``), whose
``decodeCmd`` reads an *untagged* ``method + params(key→u32-len value)`` body.
That is deliberately NOT ``zap.frame.encode_cmd`` — the canonical helper inserts
a per-value type tag (to round-trip str vs bytes between Python peers) which the
extension does not read. Encoding with the tagged helper would shift every
param by one byte and corrupt the command, so this peer keeps the untagged form.
"""
from __future__ import annotations

import os
import shutil
import socket as _socket
import struct
import subprocess
import time
from typing import Optional

from zap import frame
from zap.client import ZapClient


def socket_path() -> str:
    """The brand-neutral zapd socket; delegates to the canonical resolver."""
    return frame.socket_path()


def _socket_live(path: str) -> bool:
    """True iff a listener currently accepts connections on the UDS at ``path``."""
    if not path or not os.path.exists(path):
        return False
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        s.connect(path)
        return True
    except OSError:
        return False
    finally:
        s.close()


def _find_zapd() -> Optional[str]:
    """Locate the one ``zapd`` binary. ``ZAP_ZAPD``/``ZAPD_BIN`` override, then
    PATH, then the standard install prefixes (install.sh drops it in
    ~/.local/bin), then a local source checkout's release build."""
    for env in ("ZAP_ZAPD", "ZAPD_BIN"):
        p = os.environ.get(env)
        if p and os.path.exists(p):
            return p
    hit = shutil.which("zapd")
    if hit:
        return hit
    for c in (
        "~/.local/bin/zapd",
        "~/.cargo/bin/zapd",
        "/usr/local/bin/zapd",
        "~/work/zapd/target/release/zapd",
    ):
        c = os.path.expanduser(c)
        if os.path.exists(c):
            return c
    return None


def ensure_zapd_running(timeout: float = 6.0) -> bool:
    """Guarantee the shared zapd router is listening, auto-starting it if not.

    This mirrors zapd's own host-mode connect-or-spawn (``host.rs``): a ZAP
    consumer never needs a human to have started the daemon. The OS unit
    (systemd/launchd, and socket-activation) is the primary auto-starter; this
    is the no-service fallback so the tool self-heals on a bare machine.

    Idempotent and race-safe by construction: the router is a *singleton* — it
    binds the well-known socket behind an advisory lock (``broker.rs``), so any
    number of processes may launch ``zapd`` concurrently and every loser exits
    cleanly. There is therefore no consumer-side lock here — the one-and-only
    singleton invariant lives in zapd, not in each SDK. Returns True once the
    socket accepts connections, False if ``zapd`` can't be found or is slow.
    """
    sock = socket_path()
    if _socket_live(sock):
        return True
    exe = _find_zapd()
    if not exe:
        return False
    try:
        subprocess.Popen(
            [exe, "--log", "info"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # detach so the router outlives this process
        )
    except OSError:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _socket_live(sock):
            return True
        time.sleep(0.1)
    return False


def _encode_cmd(method: str, params: dict) -> bytes:
    """Untagged browser command body — peer of the extension's ``decodeCmd``.

    Layout (little-endian): ``method(u16 len + bytes)`` then ``u16`` param count,
    each param ``key(u16 len + bytes) + value(u32 len + bytes)``. No type tag —
    see the module docstring for why this is not ``frame.encode_cmd``.
    """
    b = frame._put_str(method) + struct.pack("<H", len(params))
    for k, v in params.items():
        vb = v.encode() if isinstance(v, str) else bytes(v)
        b += frame._put_str(k) + struct.pack("<I", len(vb)) + vb
    return b


class ZapdConsumer:
    """A persistent consumer connection to the local zapd router."""

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"consumer:hanzo-mcp/{os.getpid()}"
        self._client: Optional[ZapClient] = None

    def _dial(self) -> bool:
        try:
            self._client = ZapClient.connect(
                id=self.agent_id, role="consumer", brand="hanzo", timeout=5.0
            )
            return True
        except OSError:
            self._client = None
            return False

    def connect(self) -> bool:
        if self._client is not None:
            return True
        if self._dial():
            return True
        # zapd wasn't listening. Auto-start the shared singleton router and dial
        # once more, so the browser tool "just works" with no manual daemon and
        # no knowledge that zapd exists. ensure_zapd_running is a no-op when the
        # OS unit already has it up; the singleton invariant lives in zapd, so a
        # spawn race is safe.
        if not ensure_zapd_running():
            return False
        return self._dial()

    def list_providers(self, brand: str = "") -> list:
        # Self-heal: a cached client whose socket died (e.g. the router was
        # restarted) raises BrokenPipeError/OSError on use. Drop it and
        # reconnect ONCE rather than staying wedged forever.
        for attempt in (1, 2):
            if not self.connect():
                return []
            assert self._client is not None
            try:
                provs = self._client.providers_list(brand=brand)
                return [{"id": p.id, "role": p.role, "brand": p.brand, "caps": p.caps} for p in provs]
            except (BrokenPipeError, ConnectionError, OSError):
                self.close()
                if attempt == 2:
                    return []
        return []

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
        # Self-heal on a dead cached socket (see list_providers): reconnect once.
        for attempt in (1, 2):
            if not self.connect():
                raise RuntimeError("zapd not reachable")
            assert self._client is not None
            try:
                return self._client.route(provider_id, _encode_cmd(method, params), timeout=timeout)
            except (BrokenPipeError, ConnectionError, OSError):
                self.close()
                if attempt == 2:
                    raise
        raise RuntimeError("zapd not reachable")

    def close(self):
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None


_consumer: Optional[ZapdConsumer] = None


def get_consumer() -> Optional[ZapdConsumer]:
    """Return the shared consumer if zapd is reachable, else None."""
    global _consumer
    if _consumer is None:
        _consumer = ZapdConsumer()
    return _consumer if _consumer.connect() else None
