"""hanzo-mcp's seat on the ZAP router.

Every process that speaks ZAP embeds the router (``zapd.embed()``) and the
kernel elects one of them by lock; there is no daemon to start. This process
stands for router and takes the seat ``mcp/hanzo-<pid>``. A browser is a
``browser/<host>/<name>`` node, paired once through the router's door
(``hanzo-mcp pair``), and a command reaches it with ``Node.call``.

The one codec here is the browser command payload (:func:`_encode_cmd`). The
router forwards it opaquely; the extension's ``decodeCmd`` reads it.
"""

from __future__ import annotations

import os
import struct
from typing import Optional

import zapd

BROWSER = "browser/"

# What a caller is told when no browser is on the router.
UNPAIRED = (
    "no browser on the ZAP router: run `hanzo-mcp pair` and paste the code into "
    "the Hanzo extension's popup"
)


def _put_str(s: str) -> bytes:
    b = s.encode()
    return struct.pack("<H", len(b)) + b


def _encode_cmd(method: str, params: dict) -> bytes:
    """The browser command body, peer of the extension's ``decodeCmd``.

    Little-endian: ``method(u16 len + bytes)``, ``u16`` param count, then each
    param ``key(u16 len + bytes) + value(u32 len + bytes)``.
    """
    b = _put_str(method) + struct.pack("<H", len(params))
    for k, v in params.items():
        vb = v.encode() if isinstance(v, str) else bytes(v)
        b += _put_str(k) + struct.pack("<I", len(vb)) + vb
    return b


def pair(reset: bool = False) -> str:
    """This user's pairing code for the browser extension; ``reset`` rotates it."""
    return zapd.pair(reset=reset)


class ZapdConsumer:
    """This process's node on the router, and the browsers it can reach."""

    def __init__(self, name: Optional[str] = None):
        zapd.embed()
        self.node = zapd.Node(name or f"mcp/hanzo-{os.getpid()}")

    @property
    def id(self) -> str:
        return self.node.id

    def list_providers(self) -> list[dict]:
        """Every node on the router: ``{"id", "role", "brand", "caps", "attrs"}``."""
        return [dict(n) for n in self.node.nodes()]

    def browsers(self) -> list[dict]:
        return [n for n in self.list_providers() if n["id"].startswith(BROWSER)]

    def resolve_browser(self, browser: Optional[str], client_id: Optional[str]) -> Optional[str]:
        """The browser to address: ``client_id`` exactly, else the first whose
        engine or name is ``browser``, else the first one."""
        found = self.browsers()
        if client_id:
            return next((b["id"] for b in found if b["id"] == client_id), None)
        if browser:
            want = browser.lower()
            for b in found:
                name = b["id"].rsplit("/", 1)[-1]
                if b.get("attrs", {}).get("engine") == want or name.split("-", 1)[0] == want:
                    return b["id"]
            return None
        return found[0]["id"] if found else None

    def route(self, provider_id: str, method: str, params: dict, timeout: float = 30.0) -> bytes:
        return self.node.call(provider_id, _encode_cmd(method, params), timeout=timeout)


_consumer: Optional[ZapdConsumer] = None


def get_consumer() -> ZapdConsumer:
    """This process's seat, taken on first use (hanzo-mcp takes it at startup)."""
    global _consumer
    if _consumer is None:
        _consumer = ZapdConsumer()
    return _consumer
