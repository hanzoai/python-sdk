"""Browser automation tools — decomplected surface.

Three orthogonal MCP tools, all default-enabled, all disable-able by env:

  * ``browser``    — high-level action surface. Auto-routes through the
                     in-process ZAP server (browser extension), the legacy
                     CDP HTTP bridge, or Playwright. Disable with
                     ``HANZO_BROWSER_TOOL_DISABLED=1``.

  * ``cdp``        — raw Chrome DevTools Protocol method dispatch. Same
                     transports as ``browser`` minus the Playwright fallback.
                     Disable with ``HANZO_CDP_TOOL_DISABLED=1``.

  * ``playwright`` — Playwright-pinned action surface. Same actions as
                     ``browser`` but never touches the extension or CDP
                     bridge. Disable with ``HANZO_PLAYWRIGHT_TOOL_DISABLED=1``.

Independent transport knobs (orthogonal to which tools are surfaced):

  * ``HANZO_ZAP_DISABLED=1``         — don't auto-start the ZAP server.
  * ``HANZO_CDP_BRIDGE_ENABLED=1``   — opt back into the legacy HTTP bridge.
  * ``BROWSER_TRANSPORT=zap|http|auto`` — pin transport (default ``auto``).
  * ``BROWSER_BACKEND=firefox|chrome|extension|playwright|auto`` — backend
                                          preference for ``browser``.

Lifecycle (ZAP server, CDP bridge threads) lives in ``lifecycle.py``.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

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
from hanzo_tools.browser.cdp_tool import CdpTool
from hanzo_tools.browser.playwright_tool import PlaywrightTool
from hanzo_tools.browser.lifecycle import (
    CDP_BRIDGE_AVAILABLE,
    ensure_zap_server,
    start_cdp_bridge,
    stop_cdp_bridge,
    stop_zap_server,
)
from hanzo_tools.browser.zap_server import (
    ZapClient,
    ZapServer,
    get_or_start_server,
    get_server,
    shutdown_server,
)

if TYPE_CHECKING:
    from hanzo_tools.browser.cdp_bridge_server import (
        CDPBridgeClient,
        CDPBridgeServer,
    )

# Re-export CDP-bridge classes when available (legacy callers).
try:
    from hanzo_tools.browser.cdp_bridge_server import (
        CDPBridgeClient,
        CDPBridgeServer,
    )
except ImportError:  # pragma: no cover
    CDPBridgeClient = None  # type: ignore[assignment]
    CDPBridgeServer = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# === Tools registry — gated by env ====================================

def _env_disabled(*names: str) -> bool:
    return any(os.environ.get(n, "").lower() in ("1", "true", "yes") for n in names)


def _resolve_tools() -> list[type[BaseTool]]:
    """Build TOOLS list at import time based on env flags.

    Each tool is independently disable-able. Default: all three on.
    """
    tools: list[type[BaseTool]] = []

    if not _env_disabled("HANZO_BROWSER_TOOL_DISABLED"):
        tools.append(BrowserTool)
    if not _env_disabled("HANZO_CDP_TOOL_DISABLED"):
        tools.append(CdpTool)
    if not _env_disabled("HANZO_PLAYWRIGHT_TOOL_DISABLED"):
        tools.append(PlaywrightTool)

    return tools


TOOLS: list[type[BaseTool]] = _resolve_tools()


# === Registration entry point ==========================================

def register_browser_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register browser tools with the MCP server.

    Starts the in-process ZAP server (unless ``HANZO_ZAP_DISABLED=1``) so
    the browser extension can discover this MCP via mDNS. The legacy CDP
    HTTP bridge (port 9223/9224) stays off by default — opt in with
    ``HANZO_CDP_BRIDGE_ENABLED=1`` or ``cdp_bridge=True`` kwarg.

    Which tools get registered is controlled by env flags:
      * HANZO_BROWSER_TOOL_DISABLED
      * HANZO_CDP_TOOL_DISABLED
      * HANZO_PLAYWRIGHT_TOOL_DISABLED
    """
    headless = kwargs.get("headless", True)
    cdp_endpoint = kwargs.get("cdp_endpoint")
    backend = kwargs.get("backend")

    # Canonical lifecycle: in-process ZAP server.
    if backend != "playwright":
        ensure_zap_server()

    # Optional legacy lifecycle: CDP HTTP bridge.
    if kwargs.get(
        "cdp_bridge",
        os.environ.get("HANZO_CDP_BRIDGE_ENABLED", "").lower() in ("1", "true", "yes"),
    ) and CDP_BRIDGE_AVAILABLE and backend != "playwright":
        start_cdp_bridge()

    registered: list[BaseTool] = []
    for tool_class in TOOLS:
        if tool_class is BrowserTool:
            tool = create_browser_tool(
                headless=headless, cdp_endpoint=cdp_endpoint, backend=backend
            )
        elif tool_class is PlaywrightTool:
            # PlaywrightTool forces backend internally; respect headless+endpoint.
            tool = PlaywrightTool(headless=headless, cdp_endpoint=cdp_endpoint)
        else:
            # CdpTool, future peers — no-arg constructor.
            tool = tool_class()
        ToolRegistry.register_tool(mcp_server, tool)
        registered.append(tool)
    return registered


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Standard entry point called by tool-discovery hosts."""
    return register_browser_tools(mcp_server, **kwargs)


__all__ = [
    # Tools (the three peers)
    "BrowserTool",
    "CdpTool",
    "PlaywrightTool",
    # Factory + module-level instance (existing public API)
    "browser_tool",
    "create_browser_tool",
    # Browser pool
    "BrowserPool",
    "launch_browser_server",
    # ZAP (canonical)
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
    # Lifecycle (now in lifecycle.py)
    "ensure_zap_server",
    "stop_zap_server",
    # Availability check
    "PLAYWRIGHT_AVAILABLE",
    # Backend helper
    "get_backend",
    # Registration
    "TOOLS",
    "register_browser_tools",
    "register_tools",
]
