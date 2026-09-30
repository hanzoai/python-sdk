"""Browser automation tools for Hanzo AI, over the ZAP router.

    [Browser ext] --door (ws, paired)--> [zapd, embedded] <--seat-- [hanzo-mcp] --stdio--> [Agent]

Every ZAP process embeds the router and the kernel elects one by lock; there is
no daemon. hanzo-mcp takes the seat ``mcp/hanzo-<pid>``, and the Hanzo
extension, paired once (``hanzo-mcp pair``), is a ``browser/<host>/<name>``
node that answers the commands routed to it.

Three peer tools are exposed, all sharing one transport (``zapd_consumer``):
- ``browser``    — high-level, action-oriented (navigate/click/screenshot/tabs …).
                   Auto-routes through the extension over zapd; falls back to
                   Playwright only for actions the extension can't serve.
- ``cdp``        — low-level, method-oriented (send any CDP method by name).
- ``playwright`` — the same action surface as ``browser`` but pinned to the
                   Playwright backend (never touches the extension).
"""

import logging
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
from hanzo_tools.browser.cdp_tool import CdpTool
from hanzo_tools.browser.playwright_tool import PlaywrightTool
from hanzo_tools.browser.zapd_consumer import ZapdConsumer, get_consumer

logger = logging.getLogger(__name__)

# Tools list for entry point discovery (see pyproject [hanzo.tools]).
TOOLS = [BrowserTool, CdpTool, PlaywrightTool]

__all__ = [
    # Tools (the three peers)
    "BrowserTool",
    "CdpTool",
    "PlaywrightTool",
    # Factory + module-level instance (existing public API)
    "browser_tool",
    "create_browser_tool",
    # Browser pool / Playwright server
    "BrowserPool",
    "launch_browser_server",
    # zapd consumer (the one canonical transport)
    "ZapdConsumer",
    "get_consumer",
    # Availability check
    "PLAYWRIGHT_AVAILABLE",
    # Backend helper
    "get_backend",
    # Registration
    "TOOLS",
    "register_browser_tools",
    "register_tools",
]


def register_browser_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register the browser tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Forwarded to the browser tool (headless, cdp_endpoint, backend)

    Returns:
        List of registered tools
    """
    headless = kwargs.get("headless", True)
    cdp_endpoint = kwargs.get("cdp_endpoint")
    backend = kwargs.get("backend")

    tools: list[BaseTool] = [
        create_browser_tool(headless=headless, cdp_endpoint=cdp_endpoint, backend=backend),
        CdpTool(),
        PlaywrightTool(headless=headless, cdp_endpoint=cdp_endpoint),
    ]
    for tool in tools:
        ToolRegistry.register_tool(mcp_server, tool)
    return tools


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all browser tools with the MCP server.

    Standard entry point called by the tool discovery system.
    """
    return register_browser_tools(mcp_server, **kwargs)
