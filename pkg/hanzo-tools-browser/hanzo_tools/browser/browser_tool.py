"""High-performance async browser automation tool using Playwright.

Design goals:
- Async-first: All operations are non-blocking
- Shared browser instance: Reuse browser across calls (low latency)
- Connection pooling: Multiple pages/contexts for parallel work
- Cross-MCP sharing: Connect to existing browser via CDP endpoint
- Full Playwright API: Complete surface area coverage
- Touch support: Mobile device emulation with touch events
- Network control: Intercept, mock, and monitor requests

PARALLEL AGENTS ARCHITECTURE:
- BrowserPool is a singleton - one Chrome process per MCP server
- Each agent can use `new_context` to get an isolated browser context
- Contexts have separate: cookies, localStorage, sessionStorage, cache
- Tabs within same context share state (use for same-session workflows)
- For true multi-process sharing, launch Chrome with CDP and connect:
    BROWSER_CDP_ENDPOINT=http://localhost:9222 hanzo-mcp
"""

import os
import re
import json
import base64
import asyncio
import logging
from typing import Any, Union, Literal, ClassVar, Optional, Annotated
from pathlib import Path
from dataclasses import field, dataclass

from pydantic import Field
from mcp.server import FastMCP

from hanzo_tools.core import BaseTool

# Playwright import with graceful fallback
try:
    from playwright.async_api import (
        Page,
        Route,
        Dialog,
        Browser,
        Locator,
        Request,
        Download,
        Response,
        Playwright,
        BrowserContext,
        ConsoleMessage,
        async_playwright,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Page = BrowserContext = Playwright = None
    Route = Request = Response = Dialog = ConsoleMessage = Download = Locator = None

logger = logging.getLogger(__name__)


async def _check_extension() -> bool:
    """Check if Hanzo browser extension is connected."""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:9224/status", timeout=aiohttp.ClientTimeout(total=1)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("connected", False)
    except Exception:
        pass
    return False


async def _extension_command(action: str, **kwargs) -> Optional[dict]:
    """Send command to Hanzo browser extension."""
    try:
        import aiohttp

        # Filter out None values
        payload = {"action": action}
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:9224",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.debug(f"Extension command failed: {e}")
    return None


# Device presets - user-friendly aliases + specific devices
DEVICES = {
    # User-friendly aliases
    "mobile": {
        "viewport": {"width": 390, "height": 844},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "tablet": {
        "viewport": {"width": 1024, "height": 1366},
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "laptop": {
        "viewport": {"width": 1440, "height": 900},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "device_scale_factor": 2,
        "is_mobile": False,
        "has_touch": False,
    },
    "desktop": {  # Alias for laptop
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    # Specific devices
    "iphone_14": {
        "viewport": {"width": 390, "height": 844},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "iphone_15_pro": {
        "viewport": {"width": 393, "height": 852},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "pixel_7": {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
    },
    "ipad_pro": {
        "viewport": {"width": 1024, "height": 1366},
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "galaxy_s23": {
        "viewport": {"width": 360, "height": 780},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
}


Action = Annotated[
    Literal[
        # === Core Page Navigation & Lifecycle ===
        "navigate",  # goto(url)
        "set_content",  # setContent(html)
        "content",  # content() - get full HTML
        "url",  # url() - get current URL
        "title",  # title() - get page title
        "reload",  # reload()
        "go_back",  # goBack()
        "go_forward",  # goForward()
        "close",  # close page/browser
        # === Input - Click/Type ===
        "click",  # click(selector)
        "dblclick",  # dblclick(selector)
        "type",  # type(selector, text) - character by character
        "fill",  # fill(selector, text) - instant, clears first
        "clear",  # clear input
        "press",  # press key combo (Ctrl+A, Enter, etc.)
        # === Input - Forms ===
        "select_option",  # select dropdown option
        "check",  # check checkbox/radio
        "uncheck",  # uncheck checkbox
        "upload",  # set_input_files
        # === Mouse ===
        "hover",  # hover(selector)
        "drag",  # drag_and_drop(source, target)
        "mouse_move",  # mouse.move(x, y)
        "mouse_down",  # mouse.down()
        "mouse_up",  # mouse.up()
        "mouse_wheel",  # mouse.wheel(dx, dy)
        "scroll",  # scroll element into view or scroll by delta
        # === Touch (Mobile) ===
        "tap",  # tap(selector) - touch tap
        "swipe",  # swipe gesture
        "pinch",  # pinch zoom
        # === Locator Creation ===
        "locator",  # Create locator (CSS, text, role, xpath)
        "frame_locator",  # frameLocator(selector)
        # === Built-in Locators (get_by_*) ===
        "get_by_role",  # getByRole(role, {name})
        "get_by_text",  # getByText(text)
        "get_by_label",  # getByLabel(text)
        "get_by_placeholder",  # getByPlaceholder(text)
        "get_by_test_id",  # getByTestId(id)
        "get_by_alt_text",  # getByAltText(text)
        "get_by_title",  # getByTitle(text)
        # === Locator Composition ===
        "first",  # locator.first
        "last",  # locator.last
        "nth",  # locator.nth(index)
        "filter",  # locator.filter({has, hasText, hasNotText})
        "all",  # locator.all() - get all matching
        "count",  # locator.count()
        # === Content Extraction ===
        "get_text",  # textContent()
        "get_inner_text",  # innerText()
        "get_attribute",  # getAttribute(name)
        "get_value",  # inputValue()
        "get_html",  # innerHTML() or content()
        "get_bounding_box",  # boundingBox()
        # === State Checks ===
        "is_visible",  # isVisible()
        "is_enabled",  # isEnabled()
        "is_checked",  # isChecked()
        "is_hidden",  # isHidden()
        "is_editable",  # isEditable()
        # === Assertions (expect) ===
        "expect_visible",  # expect(loc).toBeVisible()
        "expect_hidden",  # expect(loc).toBeHidden()
        "expect_enabled",  # expect(loc).toBeEnabled()
        "expect_text",  # expect(loc).toHaveText()
        "expect_value",  # expect(loc).toHaveValue()
        "expect_checked",  # expect(loc).toBeChecked()
        "expect_url",  # expect(page).toHaveURL()
        "expect_title",  # expect(page).toHaveTitle()
        "expect_count",  # expect(loc).toHaveCount()
        "expect_attribute",  # expect(loc).toHaveAttribute()
        # === Page Actions ===
        "screenshot",  # screenshot()
        "pdf",  # pdf()
        "snapshot",  # accessibility.snapshot()
        "evaluate",  # evaluate(js)
        "focus",  # focus(selector)
        "blur",  # blur()
        # === Wait Primitives ===
        "wait",  # waitForSelector or sleep
        "wait_for_load",  # waitForLoadState(networkidle, etc)
        "wait_for_url",  # waitForURL(pattern)
        "wait_for_event",  # waitForEvent(event) - request, response, download, filechooser, popup
        "wait_for_request",  # waitForRequest(pattern)
        "wait_for_response",  # waitForResponse(pattern)
        "wait_for_function",  # waitForFunction(js)
        # === Viewport & Device ===
        "viewport",  # setViewportSize
        "emulate",  # emulate device (mobile, tablet, laptop)
        "geolocation",  # setGeolocation
        "permissions",  # grantPermissions
        # === Network Interception ===
        "route",  # route(pattern, handler) - mock/block
        "unroute",  # unroute(pattern)
        # === Storage & Cookies ===
        "cookies",  # cookies() or addCookies()
        "clear_cookies",  # clearCookies()
        "storage",  # localStorage/sessionStorage
        "storage_state",  # storageState() - save/load auth
        # === Events & Handlers ===
        "on",  # page.on(event, handler)
        "off",  # removeListener
        # === Dialogs ===
        "dialog",  # handle pending dialog
        # === Frames ===
        "frame",  # switch to frame
        "main_frame",  # back to main frame
        # === File Chooser & Downloads ===
        "file_chooser",  # waitForEvent('filechooser')
        "download",  # waitForEvent('download')
        # === Console & Errors ===
        "console",  # get console messages
        "errors",  # get page errors
        # === Browser/Context Management ===
        "new_page",  # context.newPage()
        "new_context",  # browser.newContext() - isolated session
        "new_tab",  # alias for new_page
        "close_tab",  # close current page
        "tabs",  # list/switch tabs
        "connect",  # connect via CDP
        "set_headless",  # toggle headless/headed
        "status",  # get browser status
        # === Debug/Tracing ===
        "trace_start",  # tracing.start()
        "trace_stop",  # tracing.stop()
        "highlight",  # highlight element for debugging
    ],
    Field(description="Browser action to perform"),
]


@dataclass
class BrowserState:
    """Track browser state for debugging and monitoring."""

    console_messages: list[dict] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    routes: dict[str, dict] = field(default_factory=dict)
    event_handlers: dict[str, list] = field(default_factory=dict)
    tracing: bool = False
    pending_dialog: Any = None
    pending_download: Any = None
    pending_file_chooser: Any = None


class BrowserPool:
    """Shared browser instance pool for high-performance automation.

    ARCHITECTURE FOR PARALLEL AGENTS:
    - Singleton per MCP process - one Chrome, many contexts
    - new_context() creates isolated sessions (separate cookies/storage)
    - Tabs share context state, contexts are isolated
    - For multi-process sharing, use CDP endpoint
    """

    _instance: ClassVar[Optional["BrowserPool"]] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._pages: list[Page] = []
        self._contexts: list[BrowserContext] = []
        self._headless: bool = True
        self._cdp_endpoint: Optional[str] = None
        self._initialized: bool = False
        self._state: BrowserState = BrowserState()
        self._device: Optional[str] = None

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

    def _setup_page_listeners(self, page: Page) -> None:
        """Set up event listeners for a page."""
        # Console messages
        page.on(
            "console",
            lambda msg: self._state.console_messages.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                    "location": getattr(msg, "location", None),
                }
            ),
        )

        # Page errors
        page.on("pageerror", lambda err: self._state.page_errors.append(str(err)))

        # Dialogs
        async def handle_dialog(dialog: Dialog):
            self._state.pending_dialog = dialog

        page.on("dialog", handle_dialog)

        # Downloads
        def handle_download(download: Download):
            self._state.pending_download = download

        page.on("download", handle_download)

        # File chooser
        def handle_filechooser(file_chooser):
            self._state.pending_file_chooser = file_chooser

        page.on("filechooser", handle_filechooser)

    async def ensure_browser(
        self,
        headless: bool = True,
        cdp_endpoint: Optional[str] = None,
        device: Optional[str] = None,
    ) -> Page:
        """Ensure browser is running, return current page."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        needs_init = (
            not self._initialized
            or self._page is None
            or self._browser is None
            or self._cdp_endpoint != cdp_endpoint
            or self._device != device
        )

        if needs_init:
            if self._initialized:
                await self.close()

            self._playwright = await async_playwright().start()
            self._headless = headless
            self._cdp_endpoint = cdp_endpoint
            self._device = device
            self._state = BrowserState()

            device_settings = DEVICES.get(device) if device else None

            if cdp_endpoint:
                logger.info(f"Connecting to browser at {cdp_endpoint}")
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    cdp_endpoint
                )
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
                    context_opts = {"viewport": {"width": 1280, "height": 720}}
                    if device_settings:
                        context_opts.update(device_settings)
                    self._context = await self._browser.new_context(**context_opts)
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

                context_opts = {
                    "viewport": {"width": 1440, "height": 900},
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
                if device_settings:
                    context_opts.update(device_settings)

                self._context = await self._browser.new_context(**context_opts)
                self._contexts = [self._context]
                self._page = await self._context.new_page()
                self._pages = [self._page]

            self._setup_page_listeners(self._page)
            self._initialized = True
            logger.info(f"Browser initialized (device={device or 'laptop'})")

        return self._page

    async def new_context(
        self, device: Optional[str] = None, **kwargs
    ) -> BrowserContext:
        """Create a new isolated browser context for parallel agents."""
        if not self._browser:
            raise RuntimeError("Browser not initialized")

        context_opts = {}
        if device and device in DEVICES:
            context_opts.update(DEVICES[device])
        context_opts.update(kwargs)

        context = await self._browser.new_context(**context_opts)
        self._contexts.append(context)
        return context

    async def new_page(
        self, url: Optional[str] = None, context: Optional[BrowserContext] = None
    ) -> Page:
        """Open a new page in specified or current context."""
        ctx = context or self._context
        if not ctx:
            raise RuntimeError("Browser not initialized")
        page = await ctx.new_page()
        self._setup_page_listeners(page)
        self._pages.append(page)
        self._page = page
        if url:
            await page.goto(url)
        return page

    async def close_page(self, index: Optional[int] = None) -> None:
        """Close a page by index (default: current page)."""
        if not self._pages:
            return

        idx = (
            index
            if index is not None
            else self._pages.index(self._page) if self._page in self._pages else -1
        )
        if 0 <= idx < len(self._pages):
            page = self._pages.pop(idx)
            await page.close()
            if self._pages:
                self._page = self._pages[min(idx, len(self._pages) - 1)]
            else:
                self._page = None

    async def switch_page(self, index: int) -> Page:
        """Switch to page by index."""
        if 0 <= index < len(self._pages):
            self._page = self._pages[index]
            await self._page.bring_to_front()
            return self._page
        raise ValueError(f"Invalid page index: {index}")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._state.tracing and self._context:
            try:
                await self._context.tracing.stop()
            except Exception:
                pass

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
        self._contexts = []
        self._playwright = None
        self._initialized = False
        self._state = BrowserState()
        logger.info("Browser closed")

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def pages(self) -> list[Page]:
        return self._pages

    @property
    def state(self) -> BrowserState:
        return self._state


class BrowserTool(BaseTool):
    """Complete browser automation with full Playwright API surface area.

    PARALLEL AGENTS:
    Use `new_context` action to create isolated sessions.
    Each context has separate cookies, storage, and cache.
    One Chrome process, many parallel agent sessions.

    DEVICES:
    - mobile, tablet, laptop (user-friendly)
    - iphone_14, iphone_15_pro, pixel_7, galaxy_s23, ipad_pro (specific)
    """

    name = "browser"

    def __init__(self, headless: bool = True, cdp_endpoint: Optional[str] = None):
        self.headless = headless
        self.cdp_endpoint = cdp_endpoint or os.environ.get("BROWSER_CDP_ENDPOINT")
        self.timeout = 30000

    @property
    def description(self) -> str:
        return """Complete browser automation with full Playwright API.

DISPLAY INSTRUCTIONS: Show results as bullet points.
• navigate: Navigated to [url] (status: [status])
• click/tap: [action] on [selector]
• expect_*: ✓ Assertion passed / ✗ Assertion failed
• screenshot: Captured [size] bytes

PARALLEL AGENTS:
- Use `new_context` for isolated sessions
- One Chrome, many parallel agent contexts

DEVICES: mobile, tablet, laptop, iphone_14, pixel_7, ipad_pro

CATEGORIES:
- Navigation: navigate, set_content, content, url, title, reload, go_back/forward
- Input: click, dblclick, type, fill, clear, press
- Forms: select_option, check, uncheck, upload
- Mouse: hover, drag, mouse_move/down/up, mouse_wheel, scroll
- Touch: tap, swipe, pinch
- Locators: locator, get_by_role/text/label/placeholder/test_id/alt_text/title
- Composition: first, last, nth, filter, all, count
- Content: get_text, get_inner_text, get_attribute, get_value, get_html, get_bounding_box
- State: is_visible/hidden/enabled/editable/checked
- Assertions: expect_visible/hidden/enabled/text/value/checked/url/title/count/attribute
- Wait: wait, wait_for_load/url/event/request/response/function
- Page: screenshot, pdf, snapshot, evaluate, focus, blur
- Device: viewport, emulate, geolocation, permissions
- Network: route (mock/block), unroute
- Storage: cookies, clear_cookies, storage, storage_state
- Events: on, off
- Dialogs: dialog
- Files: file_chooser, download
- Browser: new_page, new_context, new_tab, close_tab, tabs, status
- Debug: trace_start/stop, highlight, console, errors
"""

    async def _get_page(self, device: Optional[str] = None) -> Page:
        """Get page from shared pool."""
        pool = await BrowserPool.get_instance()
        return await pool.ensure_browser(
            headless=self.headless,
            cdp_endpoint=self.cdp_endpoint,
            device=device,
        )

    def _get_locator(
        self, page: Page, selector: str, frame: Optional[str] = None
    ) -> Locator:
        """Get a locator, optionally within a frame."""
        if frame:
            return page.frame_locator(frame).locator(selector)
        return page.locator(selector)

    async def call(self, ctx, action: str, **kwargs) -> dict[str, Any]:
        """Execute browser action."""
        return await self.execute(action=action, **kwargs)

    async def execute(
        self,
        action: str,
        # Selectors
        url: Optional[str] = None,
        selector: Optional[str] = None,
        ref: Optional[str] = None,
        target_selector: Optional[str] = None,
        # Text/Values
        text: Optional[str] = None,
        value: Optional[str] = None,
        key: Optional[str] = None,
        code: Optional[str] = None,
        html: Optional[str] = None,
        attribute: Optional[str] = None,
        # Locator options
        role: Optional[str] = None,
        name: Optional[str] = None,
        exact: bool = False,
        # Locator composition
        index: Optional[int] = None,
        has_text: Optional[str] = None,
        has_not_text: Optional[str] = None,
        has: Optional[str] = None,  # Nested selector
        # Files
        files: Optional[list[str]] = None,
        # Mouse/Touch
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: Optional[str] = None,
        delta_x: Optional[int] = None,
        delta_y: Optional[int] = None,
        direction: Optional[str] = None,
        distance: Optional[int] = None,
        scale: Optional[float] = None,
        # Viewport/Device
        width: Optional[int] = None,
        height: Optional[int] = None,
        device: Optional[str] = None,
        # Geolocation
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy: Optional[float] = None,
        # Permissions
        permission: Optional[str] = None,
        # Network
        pattern: Optional[str] = None,
        response: Optional[Union[dict, str]] = None,
        status_code: Optional[int] = None,
        block: bool = False,
        # Wait/Assert options
        state: Optional[str] = None,
        event: Optional[str] = None,
        expected: Optional[str] = None,
        not_: bool = False,  # For negative assertions
        # Options
        timeout: Optional[int] = None,
        full_page: bool = False,
        tab_index: Optional[int] = None,
        cdp_endpoint: Optional[str] = None,
        headless: Optional[bool] = None,
        # Storage
        cookies: Optional[list[dict]] = None,
        storage_type: Optional[str] = None,
        storage_data: Optional[dict] = None,
        # Auth
        auth_file: Optional[str] = None,
        # Dialog
        accept: bool = True,
        prompt_text: Optional[str] = None,
        # Frame
        frame: Optional[str] = None,
        # Trace
        trace_path: Optional[str] = None,
        # Filter
        level: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute browser action with full Playwright API support.

        Automatically uses Hanzo browser extension if connected,
        falling back to Playwright for headless automation.
        """
        timeout = timeout or self.timeout
        sel = selector or ref

        # === TRY EXTENSION FIRST ===
        extension_actions = {
            "navigate",
            "screenshot",
            "click",
            "fill",
            "evaluate",
            "tabs",
            "status",
        }
        if action in extension_actions:
            ext_result = await _extension_command(
                action,
                url=url,
                selector=sel,
                text=text,
                value=value,
                code=code,
                expression=code,
                full_page=full_page,
            )
            if ext_result is not None and "error" not in ext_result:
                # Normalize response
                if "result" in ext_result:
                    ext_result = ext_result["result"]
                return {"success": True, "source": "extension", **ext_result}

        # === FALL BACK TO PLAYWRIGHT ===
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "error": "Browser extension not connected and Playwright not installed. "
                "Either connect the Hanzo browser extension or install Playwright: "
                "pip install playwright && playwright install chromium",
                "action": action,
            }

        pool = await BrowserPool.get_instance()

        try:
            # === Connection ===
            if action == "connect":
                endpoint = cdp_endpoint or self.cdp_endpoint
                if not endpoint:
                    return {"error": "cdp_endpoint required"}
                page = await pool.ensure_browser(
                    headless=self.headless, cdp_endpoint=endpoint
                )
                return {
                    "success": True,
                    "connected": True,
                    "endpoint": endpoint,
                    "url": page.url,
                }

            # === Device Emulation ===
            if action == "emulate":
                if not device:
                    return {
                        "error": f"device required. Available: {list(DEVICES.keys())}"
                    }
                if device not in DEVICES:
                    return {
                        "error": f"Unknown device. Available: {list(DEVICES.keys())}"
                    }
                page = await pool.ensure_browser(
                    headless=self.headless,
                    cdp_endpoint=self.cdp_endpoint,
                    device=device,
                )
                settings = DEVICES[device]
                return {"success": True, "device": device, **settings}

            page = await self._get_page(device)

            # === Core Page Navigation & Lifecycle ===
            if action == "navigate":
                if not url:
                    return {"error": "url required"}
                resp = await page.goto(
                    url, timeout=timeout, wait_until=state or "domcontentloaded"
                )
                return {
                    "success": True,
                    "url": page.url,
                    "title": await page.title(),
                    "status": resp.status if resp else None,
                }

            elif action == "set_content":
                if not html:
                    return {"error": "html required"}
                await page.set_content(html, timeout=timeout)
                return {"success": True, "set_content": True}

            elif action == "content":
                return {"success": True, "html": await page.content()}

            elif action == "url":
                return {"success": True, "url": page.url}

            elif action == "title":
                return {"success": True, "title": await page.title()}

            elif action == "reload":
                resp = await page.reload(timeout=timeout)
                return {
                    "success": True,
                    "url": page.url,
                    "status": resp.status if resp else None,
                }

            elif action == "go_back":
                resp = await page.go_back(timeout=timeout)
                return {"success": True, "url": page.url, "navigated": resp is not None}

            elif action == "go_forward":
                resp = await page.go_forward(timeout=timeout)
                return {"success": True, "url": page.url, "navigated": resp is not None}

            # === Input ===
            elif action == "click":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.click(timeout=timeout, button=button or "left")
                return {"success": True, "clicked": sel}

            elif action == "dblclick":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.dblclick(timeout=timeout)
                return {"success": True, "double_clicked": sel}

            elif action == "type":
                if not sel or text is None:
                    return {"error": "selector and text required"}
                loc = self._get_locator(page, sel, frame)
                await loc.type(text, timeout=timeout)
                return {"success": True, "typed": len(text), "selector": sel}

            elif action == "fill":
                if not sel or text is None:
                    return {"error": "selector and text required"}
                loc = self._get_locator(page, sel, frame)
                await loc.fill(text, timeout=timeout)
                return {"success": True, "filled": sel}

            elif action == "clear":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.clear(timeout=timeout)
                return {"success": True, "cleared": sel}

            elif action == "press":
                if not key:
                    return {"error": "key required"}
                if sel:
                    loc = self._get_locator(page, sel, frame)
                    await loc.press(key, timeout=timeout)
                else:
                    await page.keyboard.press(key)
                return {"success": True, "pressed": key}

            # === Forms ===
            elif action == "select_option":
                if not sel or value is None:
                    return {"error": "selector and value required"}
                loc = self._get_locator(page, sel, frame)
                selected = await loc.select_option(
                    value if isinstance(value, list) else [value], timeout=timeout
                )
                return {"success": True, "selected": selected}

            elif action == "check":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.check(timeout=timeout)
                return {"success": True, "checked": sel}

            elif action == "uncheck":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.uncheck(timeout=timeout)
                return {"success": True, "unchecked": sel}

            elif action == "upload":
                if not sel or not files:
                    return {"error": "selector and files required"}
                loc = self._get_locator(page, sel, frame)
                await loc.set_input_files(files, timeout=timeout)
                return {"success": True, "uploaded": len(files)}

            # === Mouse ===
            elif action == "hover":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.hover(timeout=timeout)
                return {"success": True, "hovered": sel}

            elif action == "drag":
                if not sel or not target_selector:
                    return {"error": "selector and target_selector required"}
                await page.drag_and_drop(sel, target_selector, timeout=timeout)
                return {"success": True, "dragged": sel, "to": target_selector}

            elif action == "mouse_move":
                if x is None or y is None:
                    return {"error": "x and y required"}
                await page.mouse.move(x, y)
                return {"success": True, "moved_to": {"x": x, "y": y}}

            elif action == "mouse_down":
                await page.mouse.down(button=button or "left")
                return {"success": True, "button_down": button or "left"}

            elif action == "mouse_up":
                await page.mouse.up(button=button or "left")
                return {"success": True, "button_up": button or "left"}

            elif action == "mouse_wheel":
                await page.mouse.wheel(delta_x or 0, delta_y or 0)
                return {
                    "success": True,
                    "scrolled": {"delta_x": delta_x or 0, "delta_y": delta_y or 0},
                }

            elif action == "scroll":
                if sel:
                    loc = self._get_locator(page, sel, frame)
                    await loc.scroll_into_view_if_needed(timeout=timeout)
                    return {"success": True, "scrolled_to": sel}
                else:
                    await page.evaluate(
                        f"window.scrollBy({delta_x or 0}, {delta_y or 300})"
                    )
                    return {
                        "success": True,
                        "scrolled": {
                            "delta_x": delta_x or 0,
                            "delta_y": delta_y or 300,
                        },
                    }

            # === Touch ===
            elif action == "tap":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.tap(timeout=timeout)
                return {"success": True, "tapped": sel}

            elif action == "swipe":
                if not sel or not direction:
                    return {"error": "selector and direction required"}
                loc = self._get_locator(page, sel, frame)
                box = await loc.bounding_box()
                if not box:
                    return {"error": "Element not visible"}
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                dist = distance or 200
                offsets = {
                    "left": (-dist, 0),
                    "right": (dist, 0),
                    "up": (0, -dist),
                    "down": (0, dist),
                }
                dx, dy = offsets.get(direction, (0, 0))
                await page.touchscreen.tap(cx, cy)
                await page.mouse.move(cx, cy)
                await page.mouse.down()
                await page.mouse.move(cx + dx, cy + dy, steps=10)
                await page.mouse.up()
                return {"success": True, "swiped": sel, "direction": direction}

            elif action == "pinch":
                if not sel:
                    return {"error": "selector required"}
                zoom = scale or 0.5
                await page.evaluate(
                    f"""(sel) => {{
                    const el = document.querySelector(sel);
                    if (el) el.dispatchEvent(new WheelEvent('wheel', {{deltaY: {"-100" if zoom > 1 else "100"}, ctrlKey: true, bubbles: true}}));
                }}""",
                    sel,
                )
                return {"success": True, "pinched": sel, "scale": zoom}

            # === Locator Creation ===
            elif action == "locator":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                cnt = await loc.count()
                return {
                    "success": True,
                    "selector": sel,
                    "count": cnt,
                    "visible": await loc.first.is_visible() if cnt > 0 else False,
                }

            elif action == "frame_locator":
                if not sel:
                    return {"error": "selector required"}
                # Just validate frame exists
                frame_loc = page.frame_locator(sel)
                return {
                    "success": True,
                    "frame": sel,
                    "note": "Use frame parameter in subsequent actions",
                }

            # === Built-in Locators ===
            elif action == "get_by_role":
                if not role:
                    return {"error": "role required"}
                loc = page.get_by_role(role, name=name, exact=exact)
                cnt = await loc.count()
                return {"success": True, "role": role, "name": name, "count": cnt}

            elif action == "get_by_text":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_text(text, exact=exact)
                return {"success": True, "text": text, "count": await loc.count()}

            elif action == "get_by_label":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_label(text, exact=exact)
                return {"success": True, "label": text, "count": await loc.count()}

            elif action == "get_by_placeholder":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_placeholder(text, exact=exact)
                return {
                    "success": True,
                    "placeholder": text,
                    "count": await loc.count(),
                }

            elif action == "get_by_test_id":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_test_id(text)
                return {"success": True, "test_id": text, "count": await loc.count()}

            elif action == "get_by_alt_text":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_alt_text(text, exact=exact)
                return {"success": True, "alt_text": text, "count": await loc.count()}

            elif action == "get_by_title":
                if not text:
                    return {"error": "text required"}
                loc = page.get_by_title(text, exact=exact)
                return {"success": True, "title": text, "count": await loc.count()}

            # === Locator Composition ===
            elif action == "first":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame).first
                visible = await loc.is_visible()
                return {"success": True, "first": True, "visible": visible}

            elif action == "last":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame).last
                visible = await loc.is_visible()
                return {"success": True, "last": True, "visible": visible}

            elif action == "nth":
                if not sel or index is None:
                    return {"error": "selector and index required"}
                loc = self._get_locator(page, sel, frame).nth(index)
                visible = await loc.is_visible()
                return {"success": True, "nth": index, "visible": visible}

            elif action == "filter":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                filter_opts = {}
                if has_text:
                    filter_opts["has_text"] = has_text
                if has_not_text:
                    filter_opts["has_not_text"] = has_not_text
                if has:
                    filter_opts["has"] = page.locator(has)
                if filter_opts:
                    loc = loc.filter(**filter_opts)
                return {"success": True, "filtered": True, "count": await loc.count()}

            elif action == "all":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                elements = await loc.all()
                results = []
                for i, el in enumerate(elements):
                    results.append(
                        {
                            "index": i,
                            "visible": await el.is_visible(),
                            "text": await el.text_content(),
                        }
                    )
                return {
                    "success": True,
                    "count": len(results),
                    "elements": results[:20],
                }  # Limit to 20

            elif action == "count":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {"success": True, "count": await loc.count()}

            # === Content Extraction ===
            elif action == "get_text":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "text": await loc.text_content(timeout=timeout),
                }

            elif action == "get_inner_text":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "inner_text": await loc.inner_text(timeout=timeout),
                }

            elif action == "get_attribute":
                if not sel or not attribute:
                    return {"error": "selector and attribute required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "attribute": attribute,
                    "value": await loc.get_attribute(attribute, timeout=timeout),
                }

            elif action == "get_value":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "value": await loc.input_value(timeout=timeout),
                }

            elif action == "get_html":
                if sel:
                    loc = self._get_locator(page, sel, frame)
                    return {
                        "success": True,
                        "html": await loc.inner_html(timeout=timeout),
                    }
                return {"success": True, "html": await page.content()}

            elif action == "get_bounding_box":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                box = await loc.bounding_box(timeout=timeout)
                return (
                    {"success": True, "bounding_box": box}
                    if box
                    else {"error": "Element not visible"}
                )

            # === State Checks ===
            elif action == "is_visible":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "visible": await loc.is_visible(timeout=timeout),
                }

            elif action == "is_hidden":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {"success": True, "hidden": await loc.is_hidden(timeout=timeout)}

            elif action == "is_enabled":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "enabled": await loc.is_enabled(timeout=timeout),
                }

            elif action == "is_editable":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "editable": await loc.is_editable(timeout=timeout),
                }

            elif action == "is_checked":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "checked": await loc.is_checked(timeout=timeout),
                }

            # === Assertions (expect) ===
            elif action.startswith("expect_"):
                from playwright.async_api import expect

                if action == "expect_url":
                    pattern = expected or url or pattern
                    if not pattern:
                        return {"error": "expected URL pattern required"}
                    try:
                        await expect(page).to_have_url(
                            re.compile(pattern) if "*" in pattern else pattern,
                            timeout=timeout,
                        )
                        return {"success": True, "assertion": "url", "passed": True}
                    except Exception as e:
                        return {
                            "success": False,
                            "assertion": "url",
                            "passed": False,
                            "error": str(e),
                        }

                elif action == "expect_title":
                    pattern = expected or text
                    if not pattern:
                        return {"error": "expected title required"}
                    try:
                        await expect(page).to_have_title(
                            re.compile(pattern) if "*" in pattern else pattern,
                            timeout=timeout,
                        )
                        return {"success": True, "assertion": "title", "passed": True}
                    except Exception as e:
                        return {
                            "success": False,
                            "assertion": "title",
                            "passed": False,
                            "error": str(e),
                        }

                elif not sel:
                    return {"error": "selector required for element assertions"}

                loc = self._get_locator(page, sel, frame)
                assertion_type = action.replace("expect_", "")

                try:
                    if assertion_type == "visible":
                        if not_:
                            await expect(loc).not_to_be_visible(timeout=timeout)
                        else:
                            await expect(loc).to_be_visible(timeout=timeout)
                    elif assertion_type == "hidden":
                        if not_:
                            await expect(loc).not_to_be_hidden(timeout=timeout)
                        else:
                            await expect(loc).to_be_hidden(timeout=timeout)
                    elif assertion_type == "enabled":
                        if not_:
                            await expect(loc).not_to_be_enabled(timeout=timeout)
                        else:
                            await expect(loc).to_be_enabled(timeout=timeout)
                    elif assertion_type == "text":
                        if not expected and not text:
                            return {"error": "expected text required"}
                        exp = expected or text
                        if not_:
                            await expect(loc).not_to_have_text(exp, timeout=timeout)
                        else:
                            await expect(loc).to_have_text(exp, timeout=timeout)
                    elif assertion_type == "value":
                        if not expected and not value:
                            return {"error": "expected value required"}
                        exp = expected or value
                        if not_:
                            await expect(loc).not_to_have_value(exp, timeout=timeout)
                        else:
                            await expect(loc).to_have_value(exp, timeout=timeout)
                    elif assertion_type == "checked":
                        if not_:
                            await expect(loc).not_to_be_checked(timeout=timeout)
                        else:
                            await expect(loc).to_be_checked(timeout=timeout)
                    elif assertion_type == "count":
                        if index is None:
                            return {"error": "index (expected count) required"}
                        await expect(loc).to_have_count(index, timeout=timeout)
                    elif assertion_type == "attribute":
                        if not attribute or not expected:
                            return {"error": "attribute and expected required"}
                        if not_:
                            await expect(loc).not_to_have_attribute(
                                attribute, expected, timeout=timeout
                            )
                        else:
                            await expect(loc).to_have_attribute(
                                attribute, expected, timeout=timeout
                            )
                    else:
                        return {"error": f"Unknown assertion: {assertion_type}"}

                    return {
                        "success": True,
                        "assertion": assertion_type,
                        "passed": True,
                        "selector": sel,
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "assertion": assertion_type,
                        "passed": False,
                        "selector": sel,
                        "error": str(e),
                    }

            # === Page Actions ===
            elif action == "screenshot":
                opts = {"full_page": full_page, "type": "png"}
                if sel:
                    loc = self._get_locator(page, sel, frame)
                    data = await loc.screenshot(**opts)
                else:
                    data = await page.screenshot(**opts)
                return {
                    "success": True,
                    "format": "png",
                    "size": len(data),
                    "base64": base64.b64encode(data).decode(),
                }

            elif action == "pdf":
                data = await page.pdf()
                return {
                    "success": True,
                    "format": "pdf",
                    "size": len(data),
                    "base64": base64.b64encode(data).decode(),
                }

            elif action == "snapshot":
                return {
                    "success": True,
                    "url": page.url,
                    "title": await page.title(),
                    "snapshot": await page.accessibility.snapshot(),
                }

            elif action == "evaluate":
                if not code:
                    return {"error": "code required"}
                result = await page.evaluate(code)
                return {"success": True, "result": result}

            elif action == "focus":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.focus(timeout=timeout)
                return {"success": True, "focused": sel}

            elif action == "blur":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.blur(timeout=timeout)
                return {"success": True, "blurred": sel}

            elif action == "highlight":
                if not sel:
                    return {"error": "selector required"}
                loc = self._get_locator(page, sel, frame)
                await loc.highlight()
                return {"success": True, "highlighted": sel}

            # === Wait Primitives ===
            elif action == "wait":
                if sel:
                    loc = self._get_locator(page, sel, frame)
                    await loc.wait_for(timeout=timeout, state=state or "visible")
                    return {"success": True, "found": sel}
                elif timeout:
                    await asyncio.sleep(timeout / 1000)
                    return {"success": True, "waited_ms": timeout}
                return {"error": "selector or timeout required"}

            elif action == "wait_for_load":
                await page.wait_for_load_state(state or "load", timeout=timeout)
                return {"success": True, "state": state or "load"}

            elif action == "wait_for_url":
                if not pattern and not url:
                    return {"error": "pattern or url required"}
                await page.wait_for_url(pattern or url, timeout=timeout)
                return {"success": True, "url": page.url}

            elif action == "wait_for_event":
                if not event:
                    return {
                        "error": "event required (request, response, download, filechooser, popup)"
                    }
                result = await page.wait_for_event(event, timeout=timeout)
                if event == "request":
                    return {
                        "success": True,
                        "event": event,
                        "url": result.url,
                        "method": result.method,
                    }
                elif event == "response":
                    return {
                        "success": True,
                        "event": event,
                        "url": result.url,
                        "status": result.status,
                    }
                elif event == "download":
                    return {
                        "success": True,
                        "event": event,
                        "filename": result.suggested_filename,
                    }
                return {"success": True, "event": event}

            elif action == "wait_for_request":
                if not pattern:
                    return {"error": "pattern required"}
                req = await page.wait_for_request(pattern, timeout=timeout)
                return {"success": True, "url": req.url, "method": req.method}

            elif action == "wait_for_response":
                if not pattern:
                    return {"error": "pattern required"}
                resp = await page.wait_for_response(pattern, timeout=timeout)
                return {"success": True, "url": resp.url, "status": resp.status}

            elif action == "wait_for_function":
                if not code:
                    return {"error": "code (JavaScript function) required"}
                await page.wait_for_function(code, timeout=timeout)
                return {"success": True, "function_returned_truthy": True}

            # === Viewport/Device ===
            elif action == "viewport":
                if width is None or height is None:
                    return {"success": True, "viewport": page.viewport_size}
                await page.set_viewport_size({"width": width, "height": height})
                return {"success": True, "viewport": {"width": width, "height": height}}

            elif action == "geolocation":
                if latitude is None or longitude is None:
                    return {"error": "latitude and longitude required"}
                await pool._context.set_geolocation(
                    {
                        "latitude": latitude,
                        "longitude": longitude,
                        "accuracy": accuracy or 100,
                    }
                )
                return {
                    "success": True,
                    "geolocation": {"lat": latitude, "lon": longitude},
                }

            elif action == "permissions":
                if not permission:
                    return {"error": "permission required"}
                await pool._context.grant_permissions([permission])
                return {"success": True, "granted": permission}

            # === Network ===
            elif action == "route":
                if not pattern:
                    return {"error": "pattern required"}

                async def handle(route: Route):
                    if block:
                        await route.abort()
                    elif response:
                        body = (
                            json.dumps(response)
                            if isinstance(response, dict)
                            else response
                        )
                        await route.fulfill(
                            status=status_code or 200,
                            content_type="application/json",
                            body=body,
                        )
                    else:
                        await route.continue_()

                await page.route(pattern, handle)
                pool._state.routes[pattern] = {
                    "block": block,
                    "mock": response is not None,
                }
                return {"success": True, "route": pattern}

            elif action == "unroute":
                if not pattern:
                    return {"error": "pattern required"}
                await page.unroute(pattern)
                pool._state.routes.pop(pattern, None)
                return {"success": True, "unrouted": pattern}

            # === Storage ===
            elif action == "cookies":
                if cookies:
                    await pool._context.add_cookies(cookies)
                    return {"success": True, "set_cookies": len(cookies)}
                return {"success": True, "cookies": await pool._context.cookies()}

            elif action == "clear_cookies":
                await pool._context.clear_cookies()
                return {"success": True, "cleared_cookies": True}

            elif action == "storage":
                st = storage_type or "local"
                store = "localStorage" if st == "local" else "sessionStorage"
                if storage_data:
                    for k, v in storage_data.items():
                        await page.evaluate(
                            f"{store}.setItem('{k}', '{json.dumps(v) if isinstance(v, (dict, list)) else v}')"
                        )
                    return {"success": True, "set_keys": list(storage_data.keys())}
                return {
                    "success": True,
                    "data": await page.evaluate(
                        f"Object.fromEntries(Object.entries({store}))"
                    ),
                }

            elif action == "storage_state":
                if not auth_file:
                    return {"error": "auth_file required"}
                path = Path(auth_file)
                if path.exists():
                    storage = json.loads(path.read_text())
                    await pool._context.add_cookies(storage.get("cookies", []))
                    return {"success": True, "loaded": auth_file}
                storage_state = await pool._context.storage_state()
                path.write_text(json.dumps(storage_state, indent=2))
                return {"success": True, "saved": auth_file}

            # === Events ===
            elif action == "on":
                if not event:
                    return {"error": "event required"}
                # Events are auto-handled by _setup_page_listeners
                return {
                    "success": True,
                    "listening": event,
                    "note": "Use console/errors/dialog actions to retrieve captured events",
                }

            elif action == "off":
                return {
                    "success": True,
                    "note": "Event listeners managed automatically",
                }

            # === Dialogs ===
            elif action == "dialog":
                if pool._state.pending_dialog:
                    d = pool._state.pending_dialog
                    if accept:
                        await d.accept(prompt_text or "")
                    else:
                        await d.dismiss()
                    pool._state.pending_dialog = None
                    return {
                        "success": True,
                        "type": d.type,
                        "message": d.message,
                        "accepted": accept,
                    }
                return {"error": "No pending dialog"}

            # === Frames ===
            elif action == "frame":
                if not sel:
                    return {"error": "selector required for frame"}
                return {
                    "success": True,
                    "frame": sel,
                    "note": "Use frame parameter in subsequent actions",
                }

            elif action == "main_frame":
                return {"success": True, "frame": "main"}

            # === File Chooser & Downloads ===
            elif action == "file_chooser":
                if pool._state.pending_file_chooser:
                    fc = pool._state.pending_file_chooser
                    if files:
                        await fc.set_files(files)
                        pool._state.pending_file_chooser = None
                        return {"success": True, "uploaded": len(files)}
                    return {
                        "success": True,
                        "file_chooser_pending": True,
                        "multiple": fc.is_multiple,
                    }
                return {"error": "No pending file chooser. Trigger an upload first."}

            elif action == "download":
                if pool._state.pending_download:
                    d = pool._state.pending_download
                    path = await d.path()
                    pool._state.pending_download = None
                    return {
                        "success": True,
                        "filename": d.suggested_filename,
                        "path": str(path) if path else None,
                        "url": d.url,
                    }
                # Trigger download by clicking
                if sel:
                    async with page.expect_download(timeout=timeout) as dl:
                        await page.click(sel)
                    d = await dl.value
                    return {
                        "success": True,
                        "filename": d.suggested_filename,
                        "url": d.url,
                    }
                return {"error": "No pending download and no selector to click"}

            # === Console/Errors ===
            elif action == "console":
                msgs = pool._state.console_messages
                if level:
                    msgs = [m for m in msgs if m["type"] == level]
                return {
                    "success": True,
                    "messages": msgs[-50:],
                    "count": len(msgs),
                }  # Last 50

            elif action == "errors":
                return {
                    "success": True,
                    "errors": pool._state.page_errors[-20:],
                    "count": len(pool._state.page_errors),
                }

            # === Browser/Context ===
            elif action == "close":
                await pool.close()
                return {"success": True, "closed": True}

            elif action == "new_page" or action == "new_tab":
                new_page = await pool.new_page(url)
                return {
                    "success": True,
                    "page_index": len(pool.pages) - 1,
                    "url": new_page.url,
                }

            elif action == "new_context":
                context = await pool.new_context(device=device)
                page = await context.new_page()
                pool._page = page
                pool._pages.append(page)
                pool._setup_page_listeners(page)
                if url:
                    await page.goto(url)
                return {
                    "success": True,
                    "context": "new",
                    "device": device,
                    "isolated": True,
                    "url": page.url,
                }

            elif action == "close_tab":
                await pool.close_page(tab_index)
                return {"success": True, "remaining_pages": len(pool.pages)}

            elif action == "tabs":
                if tab_index is not None:
                    try:
                        page = await pool.switch_page(tab_index)
                        return {
                            "success": True,
                            "switched_to": tab_index,
                            "url": page.url,
                        }
                    except ValueError as e:
                        return {"error": str(e)}
                return {
                    "success": True,
                    "count": len(pool.pages),
                    "tabs": [
                        {"index": i, "url": p.url} for i, p in enumerate(pool.pages)
                    ],
                }

            elif action == "set_headless":
                new_headless = headless if headless is not None else not pool._headless
                current_url = page.url if page else None
                old_mode = "headless" if pool._headless else "headed"
                await pool.close()
                self.headless = new_headless
                page = await pool.ensure_browser(headless=new_headless)
                if current_url and current_url != "about:blank":
                    await page.goto(current_url)
                return {
                    "success": True,
                    "previous_mode": old_mode,
                    "current_mode": "headless" if new_headless else "headed",
                }

            elif action == "status":
                return {
                    "success": True,
                    "initialized": pool._initialized,
                    "headless": pool._headless,
                    "device": pool._device,
                    "pages": len(pool.pages),
                    "contexts": len(pool._contexts),
                    "current_url": page.url if page else None,
                    "console_messages": len(pool._state.console_messages),
                    "errors": len(pool._state.page_errors),
                    "routes": list(pool._state.routes.keys()),
                    "tracing": pool._state.tracing,
                }

            # === Debug ===
            elif action == "trace_start":
                if pool._state.tracing:
                    return {"error": "Tracing already active"}
                await pool._context.tracing.start(
                    screenshots=True, snapshots=True, sources=True
                )
                pool._state.tracing = True
                return {"success": True, "tracing": True}

            elif action == "trace_stop":
                if not pool._state.tracing:
                    return {"error": "Tracing not active"}
                path = trace_path or f"trace-{int(asyncio.get_event_loop().time())}.zip"
                await pool._context.tracing.stop(path=path)
                pool._state.tracing = False
                return {"success": True, "trace_path": path}

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
            url: Annotated[Optional[str], Field(description="URL")] = None,
            selector: Annotated[
                Optional[str], Field(description="CSS/XPath selector")
            ] = None,
            ref: Annotated[
                Optional[str], Field(description="Alias for selector")
            ] = None,
            target_selector: Annotated[
                Optional[str], Field(description="Target for drag")
            ] = None,
            text: Annotated[
                Optional[str], Field(description="Text for type/fill/locators")
            ] = None,
            value: Annotated[
                Optional[str], Field(description="Value for select/assertions")
            ] = None,
            key: Annotated[Optional[str], Field(description="Key for press")] = None,
            code: Annotated[Optional[str], Field(description="JavaScript code")] = None,
            html: Annotated[
                Optional[str], Field(description="HTML for set_content")
            ] = None,
            attribute: Annotated[
                Optional[str], Field(description="Attribute name")
            ] = None,
            role: Annotated[Optional[str], Field(description="ARIA role")] = None,
            name: Annotated[Optional[str], Field(description="Accessible name")] = None,
            exact: Annotated[bool, Field(description="Exact text match")] = False,
            index: Annotated[
                Optional[int], Field(description="Index for nth/count")
            ] = None,
            has_text: Annotated[
                Optional[str], Field(description="Filter by text")
            ] = None,
            has_not_text: Annotated[
                Optional[str], Field(description="Filter excluding text")
            ] = None,
            has: Annotated[
                Optional[str], Field(description="Filter by nested selector")
            ] = None,
            files: Annotated[
                Optional[list[str]], Field(description="Files for upload")
            ] = None,
            x: Annotated[Optional[int], Field(description="X coordinate")] = None,
            y: Annotated[Optional[int], Field(description="Y coordinate")] = None,
            button: Annotated[Optional[str], Field(description="Mouse button")] = None,
            delta_x: Annotated[
                Optional[int], Field(description="Horizontal delta")
            ] = None,
            delta_y: Annotated[
                Optional[int], Field(description="Vertical delta")
            ] = None,
            direction: Annotated[
                Optional[str], Field(description="Swipe direction")
            ] = None,
            distance: Annotated[
                Optional[int], Field(description="Swipe distance")
            ] = None,
            scale: Annotated[Optional[float], Field(description="Pinch scale")] = None,
            width: Annotated[Optional[int], Field(description="Viewport width")] = None,
            height: Annotated[
                Optional[int], Field(description="Viewport height")
            ] = None,
            device: Annotated[
                Optional[str], Field(description="Device: mobile, tablet, laptop")
            ] = None,
            latitude: Annotated[
                Optional[float], Field(description="Geo latitude")
            ] = None,
            longitude: Annotated[
                Optional[float], Field(description="Geo longitude")
            ] = None,
            permission: Annotated[
                Optional[str], Field(description="Permission to grant")
            ] = None,
            pattern: Annotated[Optional[str], Field(description="URL pattern")] = None,
            response: Annotated[
                Optional[dict], Field(description="Mock response")
            ] = None,
            status_code: Annotated[
                Optional[int], Field(description="Mock status")
            ] = None,
            block: Annotated[bool, Field(description="Block request")] = False,
            state: Annotated[
                Optional[str], Field(description="Load state/wait state")
            ] = None,
            event: Annotated[Optional[str], Field(description="Event name")] = None,
            expected: Annotated[
                Optional[str], Field(description="Expected value for assertions")
            ] = None,
            not_: Annotated[bool, Field(description="Negate assertion")] = False,
            timeout: Annotated[Optional[int], Field(description="Timeout ms")] = None,
            full_page: Annotated[
                bool, Field(description="Full page screenshot")
            ] = False,
            tab_index: Annotated[Optional[int], Field(description="Tab index")] = None,
            cdp_endpoint: Annotated[
                Optional[str], Field(description="CDP endpoint")
            ] = None,
            headless: Annotated[
                Optional[bool], Field(description="Headless mode")
            ] = None,
            cookies: Annotated[
                Optional[list[dict]], Field(description="Cookies")
            ] = None,
            storage_type: Annotated[
                Optional[str], Field(description="local/session")
            ] = None,
            storage_data: Annotated[
                Optional[dict], Field(description="Storage data")
            ] = None,
            auth_file: Annotated[
                Optional[str], Field(description="Auth state file")
            ] = None,
            accept: Annotated[bool, Field(description="Accept dialog")] = True,
            prompt_text: Annotated[
                Optional[str], Field(description="Dialog text")
            ] = None,
            frame: Annotated[Optional[str], Field(description="Frame selector")] = None,
            trace_path: Annotated[
                Optional[str], Field(description="Trace output")
            ] = None,
            level: Annotated[Optional[str], Field(description="Console level")] = None,
        ) -> dict[str, Any]:
            """Complete browser automation with full Playwright API surface area."""
            return await tool_instance.execute(
                action=action,
                url=url,
                selector=selector,
                ref=ref,
                target_selector=target_selector,
                text=text,
                value=value,
                key=key,
                code=code,
                html=html,
                attribute=attribute,
                role=role,
                name=name,
                exact=exact,
                index=index,
                has_text=has_text,
                has_not_text=has_not_text,
                has=has,
                files=files,
                x=x,
                y=y,
                button=button,
                delta_x=delta_x,
                delta_y=delta_y,
                direction=direction,
                distance=distance,
                scale=scale,
                width=width,
                height=height,
                device=device,
                latitude=latitude,
                longitude=longitude,
                permission=permission,
                pattern=pattern,
                response=response,
                status_code=status_code,
                block=block,
                state=state,
                event=event,
                expected=expected,
                not_=not_,
                timeout=timeout,
                full_page=full_page,
                tab_index=tab_index,
                cdp_endpoint=cdp_endpoint,
                headless=headless,
                cookies=cookies,
                storage_type=storage_type,
                storage_data=storage_data,
                auth_file=auth_file,
                accept=accept,
                prompt_text=prompt_text,
                frame=frame,
                trace_path=trace_path,
                level=level,
            )


def create_browser_tool(
    headless: bool = True, cdp_endpoint: Optional[str] = None
) -> BrowserTool:
    """Create a browser tool instance."""
    return BrowserTool(headless=headless, cdp_endpoint=cdp_endpoint)


async def launch_browser_server(port: int = 9222, headless: bool = False) -> str:
    """Launch a persistent browser server for cross-MCP sharing."""
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
