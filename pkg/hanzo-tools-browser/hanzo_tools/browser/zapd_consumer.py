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

import struct
from typing import Optional

from zap import frame
from zap.client import ZapClient


def socket_path() -> str:
    """The brand-neutral zapd socket; delegates to the canonical resolver."""
    return frame.socket_path()


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
        try:
            self._client = ZapClient.connect(
                id=self.agent_id, role="consumer", brand="hanzo", timeout=5.0
            )
            return True
        except OSError:
            self._client = None
            return False

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
