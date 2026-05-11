"""Browser automation tools for Hanzo AI.

Two-process architecture (since 0.5.0):

    [Browser ext] --ZAP/WS--> [hanzo-mcp (this Python pkg)] --stdio--> [Agent]

The hanzo-mcp process hosts a ZAP server on an OS-assigned ephemeral port
and advertises it via mDNS under ``_hanzo._tcp.local.`` (HIP-0069).
Browser extensions browse mDNS and connect directly. No node bridge is
in the critical path, no well-known port pool, no lockfile arbitration.

Legacy HTTP bridge (cdp_bridge_server.py on :9223/9224) is retained as an
opt-in fallback for non-ZAP MCP clients. Enable with
``HANZO_CDP_BRIDGE_ENABLED=1``.
"""

import os
import asyncio
import logging
import threading
from typing import Optional

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.browser.browser_tool import (
    PLAYWRIGHT_AVAILABLE,
    BrowserPool,
    BrowserTool,
    get_backend,
    _load_config,
    _save_config,
    browser_tool,
    create_browser_tool,
    launch_browser_server,
)
from hanzo_tools.browser.zap_server import (
    ZapClient,
    ZapServer,
    get_or_start_server,
    get_server,
    shutdown_server,
)

logger = logging.getLogger(__name__)

# CDP Bridge for browser extension integration (legacy, opt-in)
try:
    from hanzo_tools.browser.cdp_bridge_server import (
        WEBSOCKETS_AVAILABLE as CDP_BRIDGE_AVAILABLE,
        CDPBridgeClient,
        CDPBridgeServer,
    )
except ImportError:
    CDP_BRIDGE_AVAILABLE = False
    CDPBridgeServer = None
    CDPBridgeClient = None

# Global CDP bridge server instance (singleton, legacy path)
_cdp_bridge_server: Optional["CDPBridgeServer"] = None
_cdp_bridge_thread: Optional[threading.Thread] = None
_cdp_bridge_loop: Optional[asyncio.AbstractEventLoop] = None

# Global ZAP server lifecycle (canonical path)
_zap_thread: Optional[threading.Thread] = None
_zap_loop: Optional[asyncio.AbstractEventLoop] = None
_zap_started_event: Optional[threading.Event] = None

# Tools list for entry point discovery
TOOLS = [BrowserTool]

__all__ = [
    # Main tool
    "BrowserTool",
    "browser_tool",
    "create_browser_tool",
    # Browser pool
    "BrowserPool",
    "launch_browser_server",
    # ZAP (canonical, since 0.5.0)
    "ZapServer",
    "ZapClient",
    "get_or_start_server",
    "get_server",
    "shutdown_server",
    # CDP Bridge (legacy fallback)
    "CDPBridgeServer",
    "CDPBridgeClient",
    "CDP_BRIDGE_AVAILABLE",
    "start_cdp_bridge",
    "stop_cdp_bridge",
    # Availability check
    "PLAYWRIGHT_AVAILABLE",
    # Registration
    "TOOLS",
    "register_browser_tools",
    "register_tools",
]


def _run_zap_server(host: str) -> None:
    """Run the ZAP server in a dedicated background thread.

    The MCP's main loop is owned by FastMCP/stdio; we keep ZAP isolated so
    its websockets server has its own asyncio event loop and never fights
    with stdio for cycles. The thread lives for the MCP's lifetime.
    """
    global _zap_loop, _zap_started_event

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
        # Idle forever; the websockets server owns its own tasks.
        while True:
            await asyncio.sleep(3600)

    try:
        _zap_loop.run_until_complete(_bootstrap())
    except Exception as e:
        logger.error("ZAP server thread crashed: %s", e, exc_info=True)


def _ensure_zap_server() -> bool:
    """Start the in-process ZAP server if not already running.

    Returns True if the server is alive after this call.
    """
    global _zap_thread, _zap_started_event

    if _zap_thread is not None and _zap_thread.is_alive():
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

    # Wait for bind result so callers see a determinate state.
    _zap_started_event.wait(timeout=2.0)
    return get_server() is not None


def stop_zap_server() -> None:
    """Stop the in-process ZAP server (best-effort, non-blocking)."""
    global _zap_thread, _zap_loop, _zap_started_event

    if _zap_loop is not None:
        try:
            asyncio.run_coroutine_threadsafe(shutdown_server(), _zap_loop)
        except Exception:
            pass
    _zap_loop = None
    _zap_thread = None
    _zap_started_event = None


def _run_cdp_bridge_server(host: str, port: int) -> None:
    """Run CDP bridge server in a background thread."""
    global _cdp_bridge_server, _cdp_bridge_loop

    _cdp_bridge_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_cdp_bridge_loop)

    _cdp_bridge_server = CDPBridgeServer(host=host, port=port)

    async def run():
        await _cdp_bridge_server.start()
        # Keep running until stopped
        while True:
            await asyncio.sleep(1)

    try:
        _cdp_bridge_loop.run_until_complete(run())
    except Exception as e:
        logger.error(f"CDP bridge server crashed: {e}", exc_info=True)


def start_cdp_bridge(
    host: str = "localhost",
    port: int = 9223,
    auto_start: bool = True,
) -> bool:
    """Start the CDP bridge server for browser extension integration.

    The CDP bridge enables communication between:
    - hanzo-mcp's browser tool (via HTTP API on port 9224)
    - Hanzo browser extension (via WebSocket on port 9223)

    Args:
        host: Host to bind to (default: localhost)
        port: WebSocket port (default: 9223, HTTP API on 9224)
        auto_start: Whether to auto-start (can be disabled via env var)

    Returns:
        True if bridge started, False otherwise
    """
    global _cdp_bridge_thread

    # Check if disabled via environment
    if os.environ.get("HANZO_CDP_BRIDGE_DISABLED", "").lower() in ("1", "true", "yes"):
        logger.debug("CDP bridge disabled via environment")
        return False

    if not CDP_BRIDGE_AVAILABLE:
        logger.debug("CDP bridge not available (websockets not installed)")
        return False

    if _cdp_bridge_thread is not None and _cdp_bridge_thread.is_alive():
        logger.debug("CDP bridge already running")
        return True

    # Override from environment
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
        logger.info(f"CDP bridge started on ws://{host}:{port}")
        return True
    except Exception as e:
        logger.warning(f"Failed to start CDP bridge: {e}")
        return False


def stop_cdp_bridge() -> None:
    """Stop the CDP bridge server."""
    global _cdp_bridge_server, _cdp_bridge_thread, _cdp_bridge_loop

    if _cdp_bridge_loop is not None:
        try:
            if _cdp_bridge_server is not None:
                asyncio.run_coroutine_threadsafe(
                    _cdp_bridge_server.stop(), _cdp_bridge_loop
                )
        except Exception:
            pass

    _cdp_bridge_server = None
    _cdp_bridge_thread = None
    _cdp_bridge_loop = None


def register_browser_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register browser tools with the MCP server.

    Auto-starts the ZAP server (canonical path) so the Hanzo browser
    extension can discover this MCP and dispatch actions to it directly.
    The legacy CDP bridge (port 9223/9224) is opt-in via
    ``HANZO_CDP_BRIDGE_ENABLED=1`` or ``cdp_bridge=True`` kwarg.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional arguments (headless, cdp_endpoint, backend, cdp_bridge)

    Returns:
        List of registered tools
    """
    headless = kwargs.get("headless", True)
    cdp_endpoint = kwargs.get("cdp_endpoint")
    backend = kwargs.get("backend")

    # Canonical path: in-process ZAP server.
    if backend != "playwright":
        _ensure_zap_server()

    # Legacy CDP bridge (opt-in only).
    enable_cdp_bridge = kwargs.get(
        "cdp_bridge",
        os.environ.get("HANZO_CDP_BRIDGE_ENABLED", "").lower() in ("1", "true", "yes"),
    )
    if enable_cdp_bridge and CDP_BRIDGE_AVAILABLE and backend != "playwright":
        start_cdp_bridge()

    tool = create_browser_tool(
        headless=headless, cdp_endpoint=cdp_endpoint, backend=backend
    )
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all browser tools with the MCP server.

    This is the standard entry point called by the tool discovery system.
    Auto-starts CDP bridge for browser extension integration.
    """
    return register_browser_tools(mcp_server, **kwargs)
