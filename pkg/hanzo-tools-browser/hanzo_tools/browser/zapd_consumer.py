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

import fcntl
import os
import shutil
import socket
import struct
import subprocess
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from zap import frame
from zap.client import ZapClient


def socket_path() -> str:
    """The brand-neutral zapd socket; delegates to the canonical resolver."""
    return frame.socket_path()


# ── Auto-launch: connect-or-spawn the one shared zapd router ────────────────
#
# hanzo-mcp is a zapd *consumer*. If no router is listening yet (fresh login,
# no browser has triggered the native host), the first browser call spawns it —
# exactly as the Rust native host does (`zapd/src/host.rs::connect_or_spawn`).
#
# Singleton discipline is *not reinvented here*. The authoritative single-
# instance guard lives in zapd itself: `broker::bind` flock-serializes the
# connect-check + unlink-stale + bind, so N racing spawns converge to exactly
# one router (losers exit `AddrInUse`; see zapd's `concurrent_spawn` test). This
# consumer adds only a thin *spawn* lock so concurrent MCP calls / multiple MCP
# processes don't each fork a doomed router: whoever holds it spawns once, the
# rest find the now-live socket. Two orthogonal locks, two different files —
# never zapd's own `zapd.lock` (holding that across our poll would deadlock its
# bind). The live-socket probe is the reuse path; the flock is the spawn path.

_RUN_DIR = os.path.expanduser("~/.zap/run")
_SPAWN_LOCK = os.path.join(_RUN_DIR, "zapd.spawn.lock")
_LOG = os.path.join(_RUN_DIR, "zapd.log")
_SPAWN_WAIT_S = 10.0  # max time to wait for a freshly-spawned router to bind


def _socket_live(path: str) -> bool:
    """True iff a live listener owns ``path`` — mirrors zapd's own bind probe.

    A bare AF_UNIX connect (no HELLO) is the cheapest liveness test; zapd sees a
    clean EOF and drops the connection. A stale socket file refuses connect().
    """
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        s.connect(path)
        return True
    except OSError:
        return False
    finally:
        s.close()


def _find_zapd() -> Optional[str]:
    """Locate the zapd binary: ``ZAPD_BIN`` → PATH → the standard install dirs."""
    override = os.environ.get("ZAPD_BIN")
    if override and os.access(override, os.X_OK):
        return override
    found = shutil.which("zapd")
    if found:
        return found
    for cand in (
        os.path.expanduser("~/.local/bin/zapd"),
        "/usr/local/bin/zapd",
        "/opt/homebrew/bin/zapd",
    ):
        if os.access(cand, os.X_OK):
            return cand
    return None


@contextmanager
def _spawn_lock() -> Iterator[bool]:
    """Advisory cross-process lock so only one spawner runs at a time.

    Yields True if the lock was acquired (so the caller may spawn), False if the
    run dir/lock file can't be opened (caller falls back to a best-effort spawn;
    zapd's own bind guard still guarantees a single router either way).
    """
    try:
        os.makedirs(_RUN_DIR, mode=0o700, exist_ok=True)
        fd = os.open(_SPAWN_LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        yield False
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield True
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _spawn_zapd(zapd: str) -> None:
    """Spawn the router detached (own session), logging to ``~/.zap/run/zapd.log``.

    ``start_new_session`` + null stdin + redirected stdout/stderr fully detach it
    from this MCP process so the router survives the triggering call — the Python
    peer of the Rust host's ``process_group(0)`` detach.
    """
    log = open(_LOG, "ab")
    try:
        subprocess.Popen(
            [zapd],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
            close_fds=True,
        )
    finally:
        log.close()


def ensure_zapd() -> bool:
    """Ensure the shared zapd router is listening; spawn it if not. Idempotent.

    Reuse-first: a live socket short-circuits. Otherwise take the spawn lock,
    re-check (another caller may have just won), spawn zapd, and poll until it
    binds. Returns True once the socket is live, False if zapd can't be found or
    fails to come up.
    """
    path = socket_path()
    if _socket_live(path):
        return True
    zapd = _find_zapd()
    if zapd is None:
        return False
    with _spawn_lock():
        # Re-probe under the lock: a concurrent caller may have already spawned.
        if _socket_live(path):
            return True
        _spawn_zapd(zapd)
        deadline = time.monotonic() + _SPAWN_WAIT_S
        while time.monotonic() < deadline:
            if _socket_live(path):
                return True
            time.sleep(0.1)
    return _socket_live(path)


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
        import os

        self.agent_id = agent_id or f"consumer:hanzo-mcp/{os.getpid()}"
        self._client: Optional[ZapClient] = None

    def connect(self) -> bool:
        if self._client is not None:
            return True
        # Lazy, idempotent connect-or-spawn: try the live router first; if it's
        # absent, ensure_zapd() spawns the singleton and we retry exactly once.
        for attempt in (0, 1):
            try:
                self._client = ZapClient.connect(
                    id=self.agent_id, role="consumer", brand="hanzo", timeout=5.0
                )
                return True
            except OSError:
                self._client = None
                if attempt == 0 and ensure_zapd():
                    continue
                return False
        return False

    def list_providers(self, brand: str = "") -> list:
        if not self.connect():
            return []
        assert self._client is not None
        provs = self._client.providers_list(brand=brand)
        return [{"id": p.id, "role": p.role, "brand": p.brand, "caps": p.caps} for p in provs]

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
        if not self.connect():
            raise RuntimeError("zapd not reachable")
        assert self._client is not None
        return self._client.route(provider_id, _encode_cmd(method, params), timeout=timeout)

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
