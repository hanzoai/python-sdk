"""Lifecycle helpers for the browser package: ZAP server + legacy CDP bridge.

Decomplected out of ``__init__.py`` so the package's namespace is a pure
re-export surface. The MCP server (or any host) imports ``_ensure_zap_server``
and ``start_cdp_bridge`` from here when it wants the long-lived background
threads bound. Tools themselves never touch lifecycle directly.

Two background lifecycles, isolated:

  * ZAP server  — canonical. One MCP = one ZAP server bound to the lowest
                  free port from 9999..9995. Browser extension discovers
                  it via mDNS. Lifetime = MCP lifetime.

  * CDP bridge  — legacy HTTP fallback on :9223/:9224 for non-ZAP clients.
                  Opt-in: ``HANZO_CDP_BRIDGE_ENABLED=1``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from hanzo_tools.browser.cdp_bridge_server import CDPBridgeServer

logger = logging.getLogger(__name__)

# CDP bridge availability check
try:
    from hanzo_tools.browser.cdp_bridge_server import (
        WEBSOCKETS_AVAILABLE as CDP_BRIDGE_AVAILABLE,
        CDPBridgeServer,
    )
except ImportError:  # pragma: no cover
    CDP_BRIDGE_AVAILABLE = False
    CDPBridgeServer = None  # type: ignore[assignment]

# === Global state (one of each per process) ============================

_zap_thread: Optional[threading.Thread] = None
_zap_loop: Optional[asyncio.AbstractEventLoop] = None
_zap_started_event: Optional[threading.Event] = None

_cdp_bridge_server: Optional["CDPBridgeServer"] = None
_cdp_bridge_thread: Optional[threading.Thread] = None
_cdp_bridge_loop: Optional[asyncio.AbstractEventLoop] = None


# === ZAP (canonical) ====================================================


def _run_zap_server(host: str) -> None:
    """Run the ZAP server in a dedicated background thread."""
    global _zap_loop, _zap_started_event

    from hanzo_tools.browser.zap_server import get_or_start_server

    _zap_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_zap_loop)

    async def _bootstrap() -> None:
        srv = await get_or_start_server(
            host=host,
            agent_label=os.environ.get("HANZO_AGENT_LABEL"),
        )
        if _zap_started_event is not None:
            _zap_started_event.set()
        if srv is None:
            return
        while True:
            await asyncio.sleep(3600)

    try:
        _zap_loop.run_until_complete(_bootstrap())
    except Exception as e:
        logger.error("ZAP server thread crashed: %s", e, exc_info=True)


def ensure_zap_server() -> bool:
    """Start the in-process ZAP server if not already running.

    Returns True if the server is alive after this call.
    Idempotent — safe to call multiple times.
    """
    global _zap_thread, _zap_started_event

    if _zap_thread is not None and _zap_thread.is_alive():
        from hanzo_tools.browser.zap_server import get_server

        return get_server() is not None

    if os.environ.get("HANZO_ZAP_DISABLED", "").lower() in ("1", "true", "yes"):
        return False

    host = os.environ.get("HANZO_ZAP_HOST", "127.0.0.1")

    _zap_started_event = threading.Event()
    _zap_thread = threading.Thread(
        target=_run_zap_server,
        args=(host,),
        daemon=True,
        name="hanzo-zap-server",
    )
    _zap_thread.start()
    _zap_started_event.wait(timeout=2.0)

    from hanzo_tools.browser.zap_server import get_server

    return get_server() is not None


def stop_zap_server() -> None:
    """Stop the in-process ZAP server (best-effort, non-blocking)."""
    global _zap_thread, _zap_loop, _zap_started_event

    if _zap_loop is not None:
        try:
            from hanzo_tools.browser.zap_server import shutdown_server

            asyncio.run_coroutine_threadsafe(shutdown_server(), _zap_loop)
        except Exception:
            pass
    _zap_loop = None
    _zap_thread = None
    _zap_started_event = None


# === CDP bridge (legacy) ===============================================


def _run_cdp_bridge_server(host: str, port: int) -> None:
    """Run CDP bridge server in a background thread."""
    global _cdp_bridge_server, _cdp_bridge_loop

    _cdp_bridge_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_cdp_bridge_loop)

    _cdp_bridge_server = CDPBridgeServer(host=host, port=port)  # type: ignore[misc]

    async def run() -> None:
        await _cdp_bridge_server.start()  # type: ignore[union-attr]
        while True:
            await asyncio.sleep(1)

    try:
        _cdp_bridge_loop.run_until_complete(run())
    except Exception as e:
        logger.error("CDP bridge server crashed: %s", e, exc_info=True)


def start_cdp_bridge(host: str = "localhost", port: int = 9223) -> bool:
    """Start the legacy CDP bridge server (opt-in fallback transport).

    Enables HTTP communication between hanzo-mcp's tools (port 9224) and
    the Hanzo browser extension (WebSocket on `port`, default 9223).
    Set ``HANZO_CDP_BRIDGE_DISABLED=1`` to refuse to start.
    """
    global _cdp_bridge_thread

    if os.environ.get("HANZO_CDP_BRIDGE_DISABLED", "").lower() in ("1", "true", "yes"):
        return False
    if not CDP_BRIDGE_AVAILABLE:
        return False
    if _cdp_bridge_thread is not None and _cdp_bridge_thread.is_alive():
        return True

    host = os.environ.get("HANZO_CDP_BRIDGE_HOST", host)
    port = int(os.environ.get("HANZO_CDP_BRIDGE_PORT", str(port)))

    try:
        _cdp_bridge_thread = threading.Thread(
            target=_run_cdp_bridge_server,
            args=(host, port),
            daemon=True,
            name="cdp-bridge-server",
        )
        _cdp_bridge_thread.start()
        logger.info("CDP bridge started on ws://%s:%d", host, port)
        return True
    except Exception as e:
        logger.warning("Failed to start CDP bridge: %s", e)
        return False


def stop_cdp_bridge() -> None:
    """Stop the CDP bridge server."""
    global _cdp_bridge_server, _cdp_bridge_thread, _cdp_bridge_loop

    if _cdp_bridge_loop is not None and _cdp_bridge_server is not None:
        try:
            asyncio.run_coroutine_threadsafe(
                _cdp_bridge_server.stop(), _cdp_bridge_loop
            )
        except Exception:
            pass
    _cdp_bridge_server = None
    _cdp_bridge_thread = None
    _cdp_bridge_loop = None


__all__ = [
    "CDP_BRIDGE_AVAILABLE",
    "ensure_zap_server",
    "stop_zap_server",
    "start_cdp_bridge",
    "stop_cdp_bridge",
]
