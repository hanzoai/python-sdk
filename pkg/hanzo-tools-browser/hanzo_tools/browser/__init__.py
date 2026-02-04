"""Browser automation tools for Hanzo AI.

High-performance async browser automation using Playwright.
Supports shared browser instance for low latency and cross-MCP sharing via CDP.

Integration with Hanzo Browser Extension:
    The CDP bridge server starts automatically when browser tools are registered.
    The browser extension connects to ws://localhost:9223/cdp automatically.
    No manual setup required - just install the extension and use hanzo-mcp.
"""

import asyncio
import logging
import os
import threading
from typing import Optional

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry
from hanzo_tools.browser.browser_tool import (
    PLAYWRIGHT_AVAILABLE,
    BrowserPool,
    BrowserTool,
    browser_tool,
    create_browser_tool,
    launch_browser_server,
)

logger = logging.getLogger(__name__)

# CDP Bridge for browser extension integration
try:
    from hanzo_tools.browser.cdp_bridge_server import (
        CDPBridgeServer,
        CDPBridgeClient,
        WEBSOCKETS_AVAILABLE as CDP_BRIDGE_AVAILABLE,
    )
except ImportError:
    CDP_BRIDGE_AVAILABLE = False
    CDPBridgeServer = None
    CDPBridgeClient = None

# Global CDP bridge server instance (singleton)
_cdp_bridge_server: Optional["CDPBridgeServer"] = None
_cdp_bridge_thread: Optional[threading.Thread] = None
_cdp_bridge_loop: Optional[asyncio.AbstractEventLoop] = None

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
    # CDP Bridge (for browser extension integration)
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
    except Exception:
        pass


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
            name="cdp-bridge-server"
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
                    _cdp_bridge_server.stop(),
                    _cdp_bridge_loop
                )
        except Exception:
            pass

    _cdp_bridge_server = None
    _cdp_bridge_thread = None
    _cdp_bridge_loop = None


def register_browser_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register browser tools with the MCP server.

    This also auto-starts the CDP bridge server for browser extension
    integration. The extension can connect to ws://localhost:9223/cdp
    and control browser tabs.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional arguments (headless, cdp_endpoint, cdp_bridge)

    Returns:
        List of registered tools
    """
    headless = kwargs.get("headless", True)
    cdp_endpoint = kwargs.get("cdp_endpoint")

    # Auto-start CDP bridge for browser extension integration
    auto_cdp_bridge = kwargs.get("cdp_bridge", True)
    if auto_cdp_bridge and CDP_BRIDGE_AVAILABLE:
        start_cdp_bridge()

    tool = create_browser_tool(headless=headless, cdp_endpoint=cdp_endpoint)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all browser tools with the MCP server.

    This is the standard entry point called by the tool discovery system.
    Auto-starts CDP bridge for browser extension integration.
    """
    return register_browser_tools(mcp_server, **kwargs)
