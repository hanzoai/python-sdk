"""High-performance async browser automation tool using Playwright.

Design goals:
- Async-first: All operations are non-blocking
- Shared browser instance: Reuse browser across calls (low latency)
- Connection pooling: Multiple pages/contexts for parallel work
- Cross-MCP sharing: Connect to existing browser via CDP endpoint
"""

import asyncio
import base64
import os
from typing import Annotated, Any, Literal, Optional, ClassVar
from pathlib import Path
import logging

from pydantic import Field
from mcp.server import FastMCP

from hanzo_tools.core import BaseTool

# Playwright import with graceful fallback
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Page = BrowserContext = Playwright = None

logger = logging.getLogger(__name__)


Action = Annotated[
    Literal[
        "navigate",      # Go to URL
        "click",         # Click element
        "type",          # Type text into element
        "fill",          # Fill form field (clears first)
        "press",         # Press key
        "screenshot",    # Take screenshot
        "snapshot",      # Get accessibility tree
        "evaluate",      # Run JavaScript
        "wait",          # Wait for selector or time
        "close",         # Close browser
        "tabs",          # List/switch tabs
        "connect",       # Connect to existing browser (CDP)
    ],
    Field(description="Browser action to perform"),
]


class BrowserPool:
    """Shared browser instance pool for high-performance automation.

    Features:
    - Singleton browser instance across all MCP calls
    - Connection to remote browser via CDP (cross-MCP sharing)
    - Context pooling for parallel operations
    - Automatic cleanup on shutdown
    """

    _instance: ClassVar[Optional["BrowserPool"]] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._pages: list[Page] = []
        self._headless: bool = True
        self._cdp_endpoint: Optional[str] = None
        self._initialized: bool = False

    @classmethod
    async def get_instance(cls) -> "BrowserPool":
        """Get or create the singleton browser pool."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = BrowserPool()
            return cls._instance

    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown the browser pool."""
        async with cls._lock:
            if cls._instance is not None:
                await cls._instance.close()
                cls._instance = None

    async def ensure_browser(
        self,
        headless: bool = True,
        cdp_endpoint: Optional[str] = None,
    ) -> Page:
        """Ensure browser is running, return current page."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        needs_init = (
            not self._initialized or
            self._page is None or
            self._browser is None or
            self._cdp_endpoint != cdp_endpoint
        )

        if needs_init:
            if self._initialized:
                await self.close()

            self._playwright = await async_playwright().start()
            self._headless = headless
            self._cdp_endpoint = cdp_endpoint

            if cdp_endpoint:
                logger.info(f"Connecting to browser at {cdp_endpoint}")
                self._browser = await self._playwright.chromium.connect_over_cdp(cdp_endpoint)
                contexts = self._browser.contexts
                if contexts:
                    self._context = contexts[0]
                    pages = self._context.pages
                    if pages:
                        self._page = pages[0]
                        self._pages = list(pages)
                    else:
                        self._page = await self._context.new_page()
                        self._pages = [self._page]
                else:
                    self._context = await self._browser.new_context(
                        viewport={"width": 1280, "height": 720},
                    )
                    self._page = await self._context.new_page()
                    self._pages = [self._page]
            else:
                self._browser = await self._playwright.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                )
                self._context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                )
                self._page = await self._context.new_page()
                self._pages = [self._page]

            self._initialized = True
            logger.info("Browser initialized")

        return self._page

    async def new_tab(self) -> Page:
        """Open a new tab and switch to it."""
        if not self._context:
            raise RuntimeError("Browser not initialized")
        page = await self._context.new_page()
        self._pages.append(page)
        self._page = page
        return page

    async def switch_tab(self, index: int) -> Page:
        """Switch to tab by index."""
        if 0 <= index < len(self._pages):
            self._page = self._pages[index]
            return self._page
        raise ValueError(f"Invalid tab index: {index}")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")

        self._browser = None
        self._context = None
        self._page = None
        self._pages = []
        self._playwright = None
        self._initialized = False
        logger.info("Browser closed")

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def pages(self) -> list[Page]:
        return self._pages


class BrowserTool(BaseTool):
    """Unified browser automation tool.

    High-performance, async-first browser automation.
    Uses shared browser pool for low latency.
    """

    name = "browser"

    def __init__(self, headless: bool = True, cdp_endpoint: Optional[str] = None):
        self.headless = headless
        self.cdp_endpoint = cdp_endpoint or os.environ.get("BROWSER_CDP_ENDPOINT")
        self.timeout = 30000

    @property
    def description(self) -> str:
        return """Unified browser automation with Playwright.

High-performance, async-first browser automation.
Uses shared browser instance for low latency.
Supports CDP connection for cross-MCP browser sharing.

Actions:
- navigate: Go to URL (requires url)
- click: Click element (requires selector)
- type: Type text (requires selector, text)
- fill: Fill form field (requires selector, text)
- press: Press key (requires key, optional selector)
- screenshot: Take screenshot (optional full_page)
- snapshot: Get accessibility tree
- evaluate: Run JavaScript (requires code)
- wait: Wait for selector or time
- close: Close browser
- tabs: List or switch tabs
- connect: Connect to existing browser via CDP

Examples:
    browser(action="navigate", url="https://example.com")
    browser(action="click", selector="button#submit")
    browser(action="screenshot", full_page=True)
    browser(action="connect", cdp_endpoint="http://localhost:9222")
"""

    async def _get_page(self) -> Page:
        """Get page from shared pool."""
        pool = await BrowserPool.get_instance()
        return await pool.ensure_browser(
            headless=self.headless,
            cdp_endpoint=self.cdp_endpoint,
        )

    async def call(
        self,
        ctx,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        ref: Optional[str] = None,
        text: Optional[str] = None,
        key: Optional[str] = None,
        code: Optional[str] = None,
        timeout: Optional[int] = None,
        full_page: bool = False,
        tab_index: Optional[int] = None,
        cdp_endpoint: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute browser action."""
        return await self.execute(
            action=action,
            url=url,
            selector=selector,
            ref=ref,
            text=text,
            key=key,
            code=code,
            timeout=timeout,
            full_page=full_page,
            tab_index=tab_index,
            cdp_endpoint=cdp_endpoint,
        )

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        ref: Optional[str] = None,
        text: Optional[str] = None,
        key: Optional[str] = None,
        code: Optional[str] = None,
        timeout: Optional[int] = None,
        full_page: bool = False,
        tab_index: Optional[int] = None,
        cdp_endpoint: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute browser action."""
        pool = await BrowserPool.get_instance()
        timeout = timeout or self.timeout
        sel = selector or ref

        try:
            if action == "connect":
                endpoint = cdp_endpoint or self.cdp_endpoint
                if not endpoint:
                    return {"error": "cdp_endpoint required for connect"}
                page = await pool.ensure_browser(
                    headless=self.headless,
                    cdp_endpoint=endpoint,
                )
                return {
                    "success": True,
                    "connected": True,
                    "endpoint": endpoint,
                    "url": page.url if page else None,
                }

            page = await self._get_page()

            if action == "navigate":
                if not url:
                    return {"error": "url required for navigate"}
                response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                return {
                    "success": True,
                    "url": page.url,
                    "title": await page.title(),
                    "status": response.status if response else None,
                }

            elif action == "click":
                if not sel:
                    return {"error": "selector required for click"}
                await page.click(sel, timeout=timeout)
                return {"success": True, "clicked": sel}

            elif action == "type":
                if not sel or text is None:
                    return {"error": "selector and text required for type"}
                await page.type(sel, text, timeout=timeout)
                return {"success": True, "typed": len(text), "selector": sel}

            elif action == "fill":
                if not sel or text is None:
                    return {"error": "selector and text required for fill"}
                await page.fill(sel, text, timeout=timeout)
                return {"success": True, "filled": sel}

            elif action == "press":
                if not key:
                    return {"error": "key required for press"}
                if sel:
                    await page.press(sel, key, timeout=timeout)
                else:
                    await page.keyboard.press(key)
                return {"success": True, "pressed": key}

            elif action == "screenshot":
                screenshot_bytes = await page.screenshot(
                    full_page=full_page,
                    type="png",
                )
                return {
                    "success": True,
                    "format": "png",
                    "base64": base64.b64encode(screenshot_bytes).decode(),
                    "url": page.url,
                }

            elif action == "snapshot":
                tree = await page.accessibility.snapshot()
                return {
                    "success": True,
                    "url": page.url,
                    "title": await page.title(),
                    "snapshot": tree,
                }

            elif action == "evaluate":
                if not code:
                    return {"error": "code required for evaluate"}
                result = await page.evaluate(code)
                return {"success": True, "result": result}

            elif action == "wait":
                if sel:
                    await page.wait_for_selector(sel, timeout=timeout)
                    return {"success": True, "found": sel}
                elif timeout:
                    await asyncio.sleep(timeout / 1000)
                    return {"success": True, "waited_ms": timeout}
                else:
                    return {"error": "selector or timeout required for wait"}

            elif action == "close":
                await pool.close()
                return {"success": True, "closed": True}

            elif action == "tabs":
                if tab_index is not None:
                    try:
                        page = await pool.switch_tab(tab_index)
                        return {
                            "success": True,
                            "switched_to": tab_index,
                            "url": page.url,
                        }
                    except ValueError as e:
                        return {"error": str(e)}
                else:
                    return {
                        "success": True,
                        "count": len(pool.pages),
                        "tabs": [
                            {"index": i, "url": p.url}
                            for i, p in enumerate(pool.pages)
                        ],
                    }

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.exception(f"Browser action failed: {action}")
            return {"error": str(e), "action": action}

    def register(self, mcp_server: FastMCP) -> None:
        """Register the browser tool with an MCP server."""
        tool_instance = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def browser(
            action: Action,
            url: Annotated[Optional[str], Field(description="URL for navigate action")] = None,
            selector: Annotated[Optional[str], Field(description="CSS selector for element")] = None,
            ref: Annotated[Optional[str], Field(description="Element reference (alias for selector)")] = None,
            text: Annotated[Optional[str], Field(description="Text for type/fill actions")] = None,
            key: Annotated[Optional[str], Field(description="Key for press action")] = None,
            code: Annotated[Optional[str], Field(description="JavaScript for evaluate")] = None,
            timeout: Annotated[Optional[int], Field(description="Timeout in ms")] = None,
            full_page: Annotated[bool, Field(description="Full page screenshot")] = False,
            tab_index: Annotated[Optional[int], Field(description="Tab index for tabs action")] = None,
            cdp_endpoint: Annotated[Optional[str], Field(description="CDP endpoint for connect action")] = None,
        ) -> dict[str, Any]:
            """Unified browser automation tool (async, high-performance)."""
            return await tool_instance.execute(
                action=action,
                url=url,
                selector=selector,
                ref=ref,
                text=text,
                key=key,
                code=code,
                timeout=timeout,
                full_page=full_page,
                tab_index=tab_index,
                cdp_endpoint=cdp_endpoint,
            )


def create_browser_tool(headless: bool = True, cdp_endpoint: Optional[str] = None) -> BrowserTool:
    """Create a browser tool instance."""
    return BrowserTool(headless=headless, cdp_endpoint=cdp_endpoint)


async def launch_browser_server(port: int = 9222, headless: bool = False) -> str:
    """Launch a persistent browser server for cross-MCP sharing.

    This launches Chrome with remote debugging enabled.
    Multiple MCP instances can connect to this browser.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed")

    pw = await async_playwright().start()
    await pw.chromium.launch(
        headless=headless,
        args=[
            f"--remote-debugging-port={port}",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )

    endpoint = f"http://localhost:{port}"
    logger.info(f"Browser server launched at {endpoint}")

    return endpoint


# Default tool instance
browser_tool = BrowserTool()
