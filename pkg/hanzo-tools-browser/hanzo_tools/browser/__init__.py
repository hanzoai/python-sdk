"""Browser automation tools for Hanzo AI.

High-performance async browser automation using Playwright.
Supports shared browser instance for low latency and cross-MCP sharing via CDP.

Integration with Hanzo Browser Extension:
    # Start the CDP bridge server
    python -m hanzo_tools.browser.cdp_bridge_server
    
    # The browser extension connects to ws://localhost:9223/cdp
    # hanzo-mcp can then control browser tabs through the extension
"""

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
    # Availability check
    "PLAYWRIGHT_AVAILABLE",
    # Registration
    "TOOLS",
    "register_browser_tools",
    "register_tools",
]


def register_browser_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register browser tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional arguments (headless, cdp_endpoint)

    Returns:
        List of registered tools
    """
    headless = kwargs.get("headless", True)
    cdp_endpoint = kwargs.get("cdp_endpoint")

    tool = create_browser_tool(headless=headless, cdp_endpoint=cdp_endpoint)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all browser tools with the MCP server.

    This is the standard entry point called by the tool discovery system.
    """
    return register_browser_tools(mcp_server, **kwargs)
