"""High-performance async browser automation using Playwright.

Features:
- Async-first: All operations non-blocking
- Shared browser pool: Low latency, reuse across calls
- CDP connection: Cross-MCP browser sharing
- Connection pooling: Multiple pages for parallel work

Basic usage:
    tool = create_browser_tool()
    tool.register(mcp_server)

Cross-MCP sharing:
    # Terminal 1: Launch persistent browser
    endpoint = await launch_browser_server(port=9222)
    
    # MCP instances connect via:
    # BROWSER_CDP_ENDPOINT=http://localhost:9222
"""

from hanzo_mcp.tools.browser.browser_tool import (
    BrowserTool,
    BrowserPool,
    create_browser_tool,
    launch_browser_server,
    PLAYWRIGHT_AVAILABLE,
)

__all__ = [
    "BrowserTool",
    "BrowserPool", 
    "create_browser_tool",
    "launch_browser_server",
    "PLAYWRIGHT_AVAILABLE",
]
