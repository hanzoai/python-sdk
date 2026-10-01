"""The `browser` tool: the user's own browser through the Hanzo extension, or a
headless Playwright Chromium when none is connected.

An agent drives a page with the extension's snapshot → ref engine: `snapshot`
prints the accessibility tree with a ref on every actionable node, and click,
fill, type, press … take those refs. The surface is progressive: the schema
carries the core actions, and `help` serves the rest from ACTIONS, the one
table that names, routes and documents every action.

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
import inspect
import logging
from typing import Any, Union, ClassVar, Optional, Annotated
from pathlib import Path
from dataclasses import field, dataclass

from pydantic import Field
from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, capture
from hanzo_tools.core.unified import _result_to_mcp

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


def _load_config() -> dict:
    """Load browser config from ~/.hanzo/extension/config.json."""
    config_path = Path.home() / ".hanzo" / "extension" / "config.json"
    try:
        if config_path.exists():
            return json.loads(config_path.read_text())
    except Exception:
        pass
    return {}


def _save_config(config: dict) -> None:
    """Save browser config to ~/.hanzo/extension/config.json."""
    config_dir = Path.home() / ".hanzo" / "extension"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    try:
        config_path.write_text(json.dumps(config, indent=2))
    except Exception as e:
        logger.warning(f"Failed to save config: {e}")


def _extract_b64(text: str) -> Optional[str]:
    """Pull the base64 payload out of a screenshot response — whether it's raw
    base64, a data: URL, or JSON under data/base64/screenshot (incl. a nested
    CDP ``{"result": {"data": ...}}``). Returns None when no payload is found."""
    if not text:
        return None
    t = text.strip()
    if t.startswith("{"):
        try:
            obj = json.loads(t)
        except Exception:
            return None
        if isinstance(obj, dict):
            for k in ("data", "base64", "screenshot"):
                v = obj.get(k)
                if isinstance(v, str) and v:
                    return v.split(",", 1)[-1] if v.startswith("data:") else v
            r = obj.get("result")
            if isinstance(r, dict):
                for k in ("data", "base64", "screenshot"):
                    v = r.get(k)
                    if isinstance(v, str) and v:
                        return v.split(",", 1)[-1] if v.startswith("data:") else v
        return None
    if t.startswith("data:image"):
        return t.split(",", 1)[-1]
    _alpha = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
    if len(t) > 100 and set(t[:256]) <= _alpha:
        return t
    return None


def get_backend() -> str:
    """Get configured browser backend.

    Priority: BROWSER_BACKEND env var > ~/.hanzo/extension/config.json > "auto"

    Values: firefox | chrome | extension | playwright | auto
    """
    # Env var takes precedence
    env_val = os.environ.get("BROWSER_BACKEND", "").strip().lower()
    if env_val in ("firefox", "chrome", "extension", "playwright", "auto"):
        return env_val

    # Then config file
    config = _load_config()
    file_val = config.get("backend", "").strip().lower()
    if file_val in ("firefox", "chrome", "extension", "playwright", "auto"):
        return file_val

    return "auto"


def _normalize_tab_id(tab_id: Union[str, int, None]) -> Union[str, int, None]:
    """Strip ``tab-`` prefix and coerce to int when possible."""
    if tab_id is None:
        return None
    t = tab_id
    if isinstance(t, str) and t.startswith("tab-"):
        t = t[4:]
    try:
        return int(t)
    except (TypeError, ValueError):
        return t


async def _check_extension(browser: Optional[str] = None) -> bool:
    """Whether a browser is on this user's ZAP router."""
    import asyncio

    from hanzo_tools.browser.zapd_consumer import get_consumer

    try:
        return await asyncio.to_thread(get_consumer().resolve_browser, browser, None) is not None
    except Exception:
        return False


def _zap_method_for(action: str) -> str:
    """The extension method that serves ``action`` (``annotate``: a labelled screenshot)."""
    return "hanzo.annotate" if action == "annotate" else ACTIONS[action].wire


def _zap_params(
    action: str,
    *,
    tab_id: Union[str, int, None] = None,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    label: Optional[str] = None,
    value: Optional[str] = None,
    code: Optional[str] = None,
    expression: Optional[str] = None,
    full_page: Optional[bool] = None,
    max_width: Optional[int] = None,
    quality: Optional[int] = None,
    full_res: Optional[bool] = None,
    **rest,
) -> dict:
    """Translate the extension-tool kwargs into wire params."""
    params: dict[str, Any] = {}
    if action in ("screenshot", "annotate"):
        # Shrink where the pixels are. A 4480x1440 PNG is ~740 KB of base64 on the
        # router hop; asking the browser for a 1280px JPEG means that
        # payload is never built, let alone carried.
        params["format"] = "png" if full_res else "jpeg"
        if quality is not None:
            params["quality"] = quality
        if max_width is not None and not full_res:
            params["maxWidth"] = max_width
    if url is not None:
        params["url"] = url
    if selector is not None:
        params["selector"] = selector
    if value is not None:
        params["value"] = value
    if text is not None:
        params["text"] = text
    if label is not None:
        params["label"] = label
    expr = code or expression
    if expr is not None:
        params["expression"] = expr
    if full_page:
        params["fullPage"] = full_page
    norm_tab = _normalize_tab_id(tab_id)
    if norm_tab is not None:
        params["tabId"] = norm_tab
    op = ACTIONS[action].act if action in ACTIONS else None
    if op:
        params["op"] = op
    # Forward the action-specific fields the extension reads, under its names.
    wire_names = {"delta_x": "dx", "delta_y": "dy"}
    for k, v in rest.items():
        if v is None or v is False:
            continue
        if k in {
            "key", "index", "tab_index", "timeout", "state", "level", "attribute",
            "interactive", "compact", "depth", "urls", "outline", "filter", "delta_x", "delta_y",
        }:
            params[wire_names.get(k, k)] = v
    # Every wire value is a string; a flag reads "true", never Python's "True".
    return {k: ("true" if v else "false") if isinstance(v, bool) else v for k, v in params.items()}


# Current BiDi browsing context (active tab) for the Firefox backend.
_bidi_current_context: Optional[str] = None


async def _bidi_dispatch(
    action: str,
    *,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    code: Optional[str] = None,
    key: Optional[str] = None,
    detail: Optional[dict] = None,
) -> Optional[dict[str, Any]]:
    """Drive Firefox via WebDriver BiDi (real navigation + trusted input).

    Returns a normalized result dict, or ``None`` to fall through to the
    extension / Playwright backends when BiDi isn't available (Firefox not
    launched with --remote-debugging-port) or the action isn't BiDi-mapped.
    """
    global _bidi_current_context
    try:
        from hanzo_tools.browser.bidi_client import get_or_connect
    except Exception:
        return None
    client = await get_or_connect(port=9222)
    if client is None:
        return None

    async def _ctx() -> str:
        global _bidi_current_context
        ctxs = await client.list_contexts()
        ids = [c.get("context") for c in ctxs if c.get("context")]
        if _bidi_current_context in ids:
            return _bidi_current_context
        _bidi_current_context = ids[0] if ids else await client.create_context("tab")
        return _bidi_current_context

    def _val(ev: dict) -> Any:
        return (ev or {}).get("result", {}).get("value")

    try:
        if action == "navigate":
            c = await _ctx()
            await client.navigate(c, url or "about:blank")
            return {"success": True, "source": "bidi", "url": await client.get_url(c)}
        if action == "new_tab":
            _bidi_current_context = await client.create_context("tab")
            if url:
                await client.navigate(_bidi_current_context, url)
            return {"success": True, "source": "bidi", "tab": _bidi_current_context}
        if action == "click":
            c = await _ctx()
            r = await client.click_selector(c, selector or "")
            return {"success": bool(r.get("clicked")), "source": "bidi", **r}
        if action in ("type", "fill"):
            c = await _ctx()
            if selector:
                await client.click_selector(c, selector)
            await client.input_insert_text(c, text or "")
            return {"success": True, "source": "bidi"}
        if action == "press":
            c = await _ctx()
            await client.input_key_press(c, key or "Enter")
            return {"success": True, "source": "bidi"}
        if action == "screenshot":
            c = await _ctx()
            data = base64.b64decode(await client.capture_screenshot(c))
            return {**capture(data, fmt="png", **(detail or {})), "source": "bidi"}
        if action == "evaluate":
            c = await _ctx()
            return {"success": True, "source": "bidi", "result": _val(await client.script_evaluate(c, code or ""))}
        if action == "get_text":
            c = await _ctx()
            return {"success": True, "source": "bidi", "text": _val(await client.script_evaluate(c, "document.body ? document.body.innerText : ''"))}
        if action == "get_html":
            c = await _ctx()
            return {"success": True, "source": "bidi", "html": _val(await client.script_evaluate(c, "document.documentElement.outerHTML"))}
        if action == "url":
            c = await _ctx()
            return {"success": True, "source": "bidi", "url": await client.get_url(c)}
        if action == "title":
            c = await _ctx()
            return {"success": True, "source": "bidi", "title": _val(await client.script_evaluate(c, "document.title"))}
        if action == "tabs":
            ctxs = await client.list_contexts()
            return {"success": True, "source": "bidi",
                    "tabs": [{"context": c.get("context"), "url": c.get("url")} for c in ctxs]}
    except Exception as e:
        return {"error": str(e), "source": "bidi"}
    return None  # unmapped action → fall through to extension / Playwright


async def _extension_command(
    action: str,
    browser: Optional[str] = None,
    tab_id: Optional[Union[str, int]] = None,
    client_id: Optional[str] = None,
    detail: Optional[dict] = None,
    **kwargs,
) -> Optional[dict]:
    """Route a browser command to a ``browser/…`` node on this user's ZAP router."""
    import asyncio

    from hanzo_tools.browser.zapd_consumer import UNPAIRED, get_consumer

    try:
        consumer = get_consumer()
        provider = await asyncio.to_thread(consumer.resolve_browser, browser, client_id)
    except Exception as e:
        return {"error": str(e), "transport": "native-zap"}
    if not provider:
        return {"error": UNPAIRED, "transport": "native-zap"}

    detail = detail or {}
    method = _zap_method_for(action)
    params = _zap_params(action, tab_id=tab_id, **detail, **kwargs) or {}
    str_params = {k: (v if isinstance(v, str) else str(v)) for k, v in params.items() if v is not None}
    try:
        raw = await asyncio.to_thread(consumer.route, provider, method, str_params)
    except Exception as e:
        return {"error": str(e), "transport": "native-zap"}

    text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else raw
    # A screenshot comes back as (JSON-wrapped) base64. Base64 in the JSON text
    # is charged to the agent's context by the character, so a capture never travels
    # that way: capture() writes the bytes to a file and returns a ToolImage that
    # register() turns into a native MCP ImageContent block the client SEES.
    if action in ("screenshot", "annotate") and isinstance(text, str):
        b64 = _extract_b64(text)
        if b64:
            try:
                data = base64.b64decode(b64)
                meta = {"transport": "native-zap", "source": "zapd", "provider": provider}
                # Trust the bytes, not the provider's label — the extension picks
                # the encoding and older builds report it inconsistently.
                fmt = "jpeg" if data[:3] == b"\xff\xd8\xff" else "png"
                out = {**capture(data, fmt=fmt, path=kwargs.get("path"), **detail), **meta}
                if action == "annotate":
                    out["legend"] = json.loads(text).get("legend", [])
                return out
            except Exception as e:  # fall back to raw on any decode failure
                logger.warning(f"native-zap capture decode failed ({e}); returning raw")
    return {"success": True, "transport": "native-zap", "source": "zapd", "provider": provider, "result": text}


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


@dataclass(frozen=True)
class Op:
    """One browser action: its help topic, one-line usage, and the extension
    method that serves it (``None``: headless Playwright only). ``act`` names the
    page-engine op for actions the extension answers with ``hanzo.act``."""

    topic: str
    usage: str
    wire: Optional[str] = None
    act: Optional[str] = None


# Every action, once. The schema, the routing, the wire method and `help` are
# all read from here, so an action cannot exist in one and not the others.
ACTIONS: dict[str, Op] = {
    # core: the default surface, and the loop an agent drives a page with
    "navigate": Op("core", "url: open a URL; returns once it has loaded", "hanzo.navigate"),
    "snapshot": Op("core", "[interactive] [compact] [depth] [selector] [args.urls]: the accessibility tree, [ref=eN] on every node you can act on", "hanzo.snapshot"),
    "click": Op("core", "selector: click a ref (@e2) or CSS selector; refused when another element covers it", "hanzo.act", "click"),
    "fill": Op("core", "selector, text: replace a field's value", "hanzo.act", "fill"),
    "type": Op("core", "text [selector]: type key by key into the element, or the focused one", "hanzo.act", "type"),
    "press": Op("core", "key [selector]: Enter, Tab, Escape, ArrowDown, Control+a", "hanzo.act", "press"),
    "read": Op("core", "[outline] [filter]: the page as markdown, as the signed-in user sees it", "hanzo.read"),
    "screenshot": Op("core", "[annotate] [args.full_page] [args.full_res] [args.path]: the viewport, downscaled unless full_res; annotate boxes each ref, label [N] = @eN, and returns the legend", "hanzo.screenshot"),
    "evaluate": Op("core", "code: run JavaScript in the page and return its value", "Runtime.evaluate"),
    "wait": Op("core", "selector | text [args.state=hidden] | timeout: until it shows (or goes), or for ms", "hanzo.wait"),
    "tabs": Op("core", "open tabs; tab_id targets one in any action", "Target.getTargets"),
    "help": Op("core", "[topic]: every other action, with how to call it"),
    # interact: more ways to act on a ref or CSS selector
    "dblclick": Op("interact", "selector", "hanzo.act", "dblclick"),
    "hover": Op("interact", "selector", "hanzo.act", "hover"),
    "focus": Op("interact", "selector", "hanzo.act", "focus"),
    "select": Op("interact", "selector, args.value: choose a <select> option by value or label", "hanzo.act", "select"),
    "check": Op("interact", "selector: check a checkbox or radio (no-op when already checked)", "hanzo.act", "check"),
    "uncheck": Op("interact", "selector", "hanzo.act", "uncheck"),
    "scroll": Op("interact", "args.delta_x, args.delta_y [selector]: scroll the page, or an element, by pixels", "hanzo.act", "scroll"),
    "scroll_into_view": Op("interact", "selector", "hanzo.act", "scrollIntoView"),
    "get_text": Op("interact", "selector: rendered text; a field's value", "hanzo.act", "text"),
    "get_attribute": Op("interact", "selector, args.attribute", "hanzo.act", "attribute"),
    "count": Op("interact", "selector: how many elements a CSS selector matches", "hanzo.act", "count"),
    "upload": Op("interact", "selector, args.files: set a file input's files"),
    "drag": Op("interact", "selector, args.target_selector"),
    "blur": Op("interact", "selector"),
    "tap": Op("interact", "selector: a touch tap"),
    "swipe": Op("interact", "selector, args.direction [args.distance]"),
    "pinch": Op("interact", "selector [args.scale]"),
    "mouse_move": Op("interact", "args.x, args.y"),
    "mouse_down": Op("interact", "[args.button]"),
    "mouse_up": Op("interact", "[args.button]"),
    # navigation
    "go_back": Op("navigation", "back one page", "Page.goBack"),
    "go_forward": Op("navigation", "forward one page", "Page.goForward"),
    "reload": Op("navigation", "reload the page", "Page.reload"),
    "url": Op("navigation", "the tab's URL", "hanzo.url"),
    "title": Op("navigation", "the tab's title", "hanzo.title"),
    "set_content": Op("navigation", "args.html: replace the page's HTML"),
    # tabs and browsers
    "new_tab": Op("tabs", "[url]: open a tab", "Target.createTarget"),
    "close_tab": Op("tabs", "tab_id (Playwright: args.tab_index)", "Target.closeTarget"),
    "select_tab": Op("tabs", "tab_id (Playwright: args.tab_index): bring a tab to the front", "Target.activateTarget"),
    "browsers": Op("tabs", "connected browsers; target_browser picks one"),
    "status": Op("tabs", "the browser behind this tool", "Browser.getVersion"),
    "close": Op("tabs", "close the Playwright browser"),
    "new_context": Op("tabs", "[url] [args.device]: an isolated Playwright session (own cookies and storage)"),
    "connect": Op("tabs", "args.cdp_endpoint: attach Playwright to a running Chrome"),
    "set_headless": Op("tabs", "[args.headless]: relaunch Playwright headed or headless"),
    # page: content and state
    "get_html": Op("page", "[selector]: an element's HTML, or the page's", "hanzo.getHTML"),
    "get_bounding_box": Op("page", "selector"),
    "pdf": Op("page", "[args.path]: print the page to PDF"),
    "is_visible": Op("page", "selector"),
    "is_enabled": Op("page", "selector"),
    "is_editable": Op("page", "selector"),
    "is_checked": Op("page", "selector"),
    "highlight": Op("page", "selector: outline an element on screen"),
    # assert: fail unless the page matches (args.not_ negates)
    "expect_visible": Op("assert", "selector"),
    "expect_hidden": Op("assert", "selector"),
    "expect_enabled": Op("assert", "selector"),
    "expect_checked": Op("assert", "selector"),
    "expect_text": Op("assert", "selector, args.expected"),
    "expect_value": Op("assert", "selector, args.expected"),
    "expect_attribute": Op("assert", "selector, args.attribute, args.expected"),
    "expect_count": Op("assert", "selector, args.index (the count)"),
    "expect_url": Op("assert", "args.expected (glob with *)"),
    "expect_title": Op("assert", "args.expected (glob with *)"),
    # storage
    "cookies": Op("storage", "the page's cookies (Playwright: args.cookies sets them)", "hanzo.getCookies"),
    "clear_cookies": Op("storage", "delete every cookie"),
    "storage": Op("storage", "[args.storage_type=local|session] [args.storage_data]: read or write web storage"),
    "storage_state": Op("storage", "args.auth_file: save cookies and storage there, or load them when it exists"),
    # network
    "route": Op("network", "args.pattern [args.block] [args.response] [args.status_code]: block or mock requests"),
    "unroute": Op("network", "args.pattern"),
    "wait_for_request": Op("network", "args.pattern"),
    "wait_for_response": Op("network", "args.pattern"),
    # emulation
    "viewport": Op("emulation", "[args.width, args.height]: read or set the viewport"),
    "emulate": Op("emulation", "args.device: mobile, tablet, laptop, iphone_14, pixel_7, ipad_pro …"),
    "geolocation": Op("emulation", "args.latitude, args.longitude"),
    "permissions": Op("emulation", "args.permission: grant it"),
    # debug and events
    "console": Op("debug", "[args.level]: the page's console messages"),
    "errors": Op("debug", "uncaught page errors"),
    "dialog": Op("debug", "[args.accept] [args.prompt_text]: answer a pending alert/confirm/prompt"),
    "file_chooser": Op("debug", "[args.files]: answer a pending file chooser"),
    "download": Op("debug", "[selector]: the pending download, or click selector and take its download"),
    "wait_for_load": Op("debug", "[args.state=load|domcontentloaded|networkidle]"),
    "wait_for_url": Op("debug", "args.pattern"),
    "wait_for_function": Op("debug", "code: until the JavaScript returns truthy"),
    "wait_for_event": Op("debug", "args.event: request, response, download, filechooser, popup"),
    "trace_start": Op("debug", "record a Playwright trace"),
    "trace_stop": Op("debug", "[args.trace_path]"),
}

CORE = tuple(name for name, op in ACTIONS.items() if op.topic == "core")
TOPICS = tuple(dict.fromkeys(op.topic for op in ACTIONS.values()))

# The extension's page engine answers these as JSON the tool unpacks.
_ENGINE = {"hanzo.navigate", "hanzo.snapshot", "hanzo.read", "hanzo.act", "hanzo.wait"}
# A snapshot ref: @e2 (or e2).
_REF = re.compile(r"^@?e\d+$")

LOOP = """The loop: snapshot, act on refs, snapshot again when the page changes.
  browser(action="navigate", url="https://example.com")
  browser(action="snapshot", interactive=true)     - button "Sign in" [ref=e2]
  browser(action="click", selector="@e2")
  browser(action="fill", selector="@e3", text="me@example.com")
  browser(action="press", key="Enter")
  browser(action="read", filter="pricing")         the page as markdown
  browser(action="screenshot", annotate=true)      labels [N] on the image = @eN
A ref stays valid while its element is on the page, across snapshots. After a
navigation, or when an element was removed, the ref is refused: snapshot again.
A click on an element covered by a consent banner, modal or overlay is refused
and names the cover: act on the cover, then snapshot again.
selector takes a ref (@e2) or a CSS selector. Parameters outside the core
schema go in args, e.g. browser(action="select", selector="@e4", args={"value": "Weekly"})."""


def _help(topic: Optional[str] = None) -> str:
    """The progressive half of the surface: the loop, then every action past the
    core by topic; ``topic`` narrows it to one (``core`` included)."""
    if topic and topic not in TOPICS:
        return f"No topic {topic!r}. Topics: {', '.join(TOPICS)}."
    lines = [] if topic else [LOOP, ""]
    for t in [topic] if topic else TOPICS[1:]:
        lines.append(t)
        for name, op in ACTIONS.items():
            if op.topic != t:
                continue
            only = "" if op.wire or name in ("help", "browsers") else "  (Playwright)"
            lines.append(f"  {name:<18}{op.usage}{only}".rstrip())
    lines.append("")
    lines.append('(Playwright): headless Playwright only, not the connected browser.')
    lines.append(f'browser(action="help", topic="…") shows one of: {", ".join(TOPICS)}.')
    return "\n".join(lines)


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


DESCRIPTION = """Drive a browser: the user's own, signed in, through the Hanzo extension (headless Playwright when none is connected).

Loop: snapshot, act on a ref, snapshot again when the page changes.
  snapshot interactive=true        - button "Sign in" [ref=e2]
  click selector="@e2"   fill selector="@e3" text="me@x.com"   press key="Enter"
  read                             the page as markdown (outline=true, filter="…")
  screenshot annotate=true         every ref boxed, label [N] = @eN
selector takes a ref (@e2) or a CSS selector. A stale ref, or a click on an
element under a banner or modal, is refused with what to do next.

action="help" lists everything else (hover, select, check, scroll, back, cookies,
network, emulation, assertions …); their parameters go in args."""


def _answer(action: str, ext: dict[str, Any]) -> Union[str, dict[str, Any]]:
    """The extension's reply as the tool's: a refusal is an error, a tree or a
    page is plain text, an engine result is its fields."""
    text = ext.get("result")
    if isinstance(text, str) and text.startswith("ERR:"):
        return {"error": text[4:], "action": action}
    if isinstance(text, str) and ACTIONS[action].wire in _ENGINE:
        data = json.loads(text)
        if action == "snapshot":
            return f"{data['title']} — {data['url']} ({data['refs']} refs)\n{data['tree']}"
        if action == "read":
            return f"{data['title']} — {data['url']}\n\n{data['markdown']}"
        return {"success": True, **data}
    return {"success": True, "source": "extension", **ext}


class BrowserTool(BaseTool):
    """A browser for agents: the user's own through the Hanzo extension, or a
    headless Playwright Chromium.

    The surface is progressive. The MCP schema carries the CORE actions and
    their parameters; ``help`` serves the rest from ACTIONS, whose parameters
    travel in ``args``. ``new_context`` gives a parallel agent its own
    Playwright session (cookies, storage, cache).
    """

    name = "browser"

    def __init__(
        self,
        headless: bool = True,
        cdp_endpoint: Optional[str] = None,
        backend: Optional[str] = None,
    ):
        self.headless = headless
        self.cdp_endpoint = cdp_endpoint or os.environ.get("BROWSER_CDP_ENDPOINT")
        self.backend = backend or get_backend()
        self.timeout = 30000
        # No server to start: commands reach the browser through this user's
        # ZAP router, via zapd_consumer.

    @property
    def description(self) -> str:
        return DESCRIPTION

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

    async def call(self, ctx, action: str, **kwargs) -> Union[str, dict[str, Any]]:
        """Execute browser action."""
        return await self.execute(action=action, **kwargs)

    async def execute(
        self,
        action: str,
        # Target and input
        url: Optional[str] = None,
        selector: Optional[str] = None,
        target_selector: Optional[str] = None,
        text: Optional[str] = None,
        value: Optional[str] = None,
        key: Optional[str] = None,
        code: Optional[str] = None,
        html: Optional[str] = None,
        attribute: Optional[str] = None,
        # snapshot / read / screenshot / help
        interactive: bool = False,
        compact: bool = False,
        depth: Optional[int] = None,
        urls: bool = False,
        outline: bool = False,
        filter: Optional[str] = None,
        annotate: bool = False,
        topic: Optional[str] = None,
        # Counts and indexes
        index: Optional[int] = None,
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
        # Capture detail
        path: Optional[str] = None,
        max_width: int = 1280,
        quality: int = 70,
        full_res: bool = False,
        tab_index: Optional[int] = None,
        tab_id: Optional[Union[str, int]] = None,
        client_id: Optional[str] = None,
        target_browser: Optional[str] = None,
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
    ) -> Union[str, dict[str, Any]]:
        """Run one action: on the connected browser through the extension when
        it serves the action, else on headless Playwright.

        snapshot, read and help answer text; everything else a dict.
        """
        spec = ACTIONS.get(action)
        if spec is None:
            return {"error": f"Unknown action {action!r}. Core: {', '.join(CORE)}. action=\"help\" lists the rest."}
        if action == "help":
            return _help(topic)
        pause = timeout
        timeout = timeout or self.timeout
        sel = selector
        by_ref = bool(sel and _REF.match(sel.strip()))
        # How much pixel detail comes back inline. Travels together to every
        # capture site so all three backends answer a screenshot the same way.
        detail = {"max_width": max_width, "quality": quality, "full_res": full_res}

        # === LOCAL ACTIONS ===
        if action == "browsers":
            from hanzo_tools.browser.zapd_consumer import get_consumer

            try:
                browsers = await asyncio.to_thread(get_consumer().browsers)
            except Exception as e:
                return {"error": str(e), "transport": "native-zap"}
            return {"success": True, "transport": "native-zap", "browsers": browsers, "count": len(browsers)}

        # A wait with nothing to wait for is a pause; no browser needs asking.
        if action == "wait" and not sel and not text and pause:
            await asyncio.sleep(pause / 1000)
            return {"success": True, "waited_ms": pause}

        # === BiDi FAST-PATH (Firefox via WebDriver BiDi) ===
        # When the firefox backend is targeted and Firefox exposes a BiDi remote
        # agent (launched with --remote-debugging-port=9222), drive it directly:
        # real navigation + TRUSTED input, no CDP (Firefox is BiDi-only). Refs and
        # labelled screenshots belong to the extension's page engine, so those
        # never take this path. Falls through when BiDi is unavailable or the
        # action isn't BiDi-mapped.
        bidi_target = target_browser or (self.backend if self.backend == "firefox" else None)
        if bidi_target == "firefox" and not by_ref and not annotate:
            bidi_res = await _bidi_dispatch(
                action, url=url, selector=sel, text=text, code=code, key=key, detail=detail
            )
            if bidi_res is not None:
                return bidi_res

        # === BACKEND-AWARE ROUTING ===
        backend = self.backend
        # Resolve browser filter from backend preference. Per-call override
        # (target_browser) wins over global backend so a single MCP session
        # can address Chrome and Firefox at different moments.
        browser_filter = (target_browser or
                          (backend if backend in ("firefox", "chrome") else None))
        wire = "annotate" if action == "screenshot" and annotate else action
        if action == "scroll" and delta_x is None and delta_y is None:
            delta_y = 300

        if backend != "playwright" and spec.wire:
            ext_result = await _extension_command(
                wire,
                browser=browser_filter,
                tab_id=tab_id,
                client_id=client_id,
                detail=detail,
                path=path,
                url=url,
                selector=sel or ("html" if action == "get_html" else None),
                text=text,
                value=value,
                code=code,
                expression=code,
                full_page=full_page,
                key=key,
                index=index,
                tab_index=tab_index,
                timeout=pause,
                state=state,
                level=level,
                attribute=attribute,
                interactive=interactive,
                compact=compact,
                depth=depth,
                urls=urls,
                outline=outline,
                filter=filter,
                delta_x=delta_x,
                delta_y=delta_y,
            )
            if "error" not in ext_result:
                return _answer(action, ext_result)

            # Refs and labels exist only in the extension, an explicit backend
            # means that browser, and a connected browser's own failure is the
            # answer: Playwright stands in only when no browser is connected.
            if (backend in ("firefox", "chrome", "extension") or by_ref or wire == "annotate"
                    or await _check_extension(browser=browser_filter)):
                return {"error": ext_result["error"], "action": action, "backend": backend}

        if by_ref:
            return {"error": f"{sel} is a snapshot ref, and refs come from the Hanzo extension; "
                             "on headless Playwright pass a CSS selector.", "action": action}
        if wire == "annotate":
            return {"error": "annotate labels refs, which come from the Hanzo extension.", "action": action}

        # === FALL BACK TO PLAYWRIGHT ===
        if not PLAYWRIGHT_AVAILABLE:
            ext_connected = await _check_extension(browser=browser_filter)
            if ext_connected:
                msg = (f"Action '{action}' runs on headless Playwright, which is not installed: "
                       f"pip install playwright && playwright install chromium")
            else:
                msg = ("No browser: the Hanzo extension is not connected and Playwright is not installed. "
                       "Connect the extension, or: pip install playwright && playwright install chromium")
            return {"error": msg, "action": action}

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
                if text is None:
                    return {"error": "text required"}
                if sel:
                    await self._get_locator(page, sel, frame).press_sequentially(text, timeout=timeout)
                else:
                    await page.keyboard.type(text)
                return {"success": True, "typed": len(text), "selector": sel}

            elif action == "fill":
                if not sel or text is None:
                    return {"error": "selector and text required"}
                loc = self._get_locator(page, sel, frame)
                await loc.fill(text, timeout=timeout)
                return {"success": True, "filled": sel}

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
            elif action == "select":
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

            elif action == "scroll":
                d = [delta_x or 0, delta_y or 0]
                if sel:
                    await self._get_locator(page, sel, frame).evaluate("(e, d) => e.scrollBy(d[0], d[1])", d)
                else:
                    await page.evaluate("(d) => window.scrollBy(d[0], d[1])", d)
                return {"success": True, "scrolled": {"delta_x": d[0], "delta_y": d[1]}}

            elif action == "scroll_into_view":
                if not sel:
                    return {"error": "selector required"}
                await self._get_locator(page, sel, frame).scroll_into_view_if_needed(timeout=timeout)
                return {"success": True, "scrolled_to": sel}

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
                field = await loc.evaluate("e => ['input', 'textarea', 'select'].includes(e.localName)", timeout=timeout)
                text_of = loc.input_value if field else loc.inner_text
                return {"success": True, "text": await text_of(timeout=timeout)}

            elif action == "get_attribute":
                if not sel or not attribute:
                    return {"error": "selector and attribute required"}
                loc = self._get_locator(page, sel, frame)
                return {
                    "success": True,
                    "attribute": attribute,
                    "value": await loc.get_attribute(attribute, timeout=timeout),
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
                return capture(data, fmt="png", path=path, **detail)

            elif action == "pdf":
                return capture(await page.pdf(), fmt="pdf", path=path)

            elif action == "snapshot":
                tree = await (self._get_locator(page, sel, frame) if sel else page.locator("body")).aria_snapshot(timeout=timeout)
                return f"{await page.title()} — {page.url} (headless Playwright: no refs, act with CSS selectors)\n{tree}"

            elif action == "read":
                return f"{await page.title()} — {page.url}\n\n{await page.inner_text('body', timeout=timeout)}"

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
                if sel or text:
                    loc = self._get_locator(page, sel, frame) if sel else page.get_by_text(text).first
                    await loc.wait_for(timeout=timeout, state=state or "visible")
                    return {"success": True, "met": True}
                await page.wait_for_load_state("load", timeout=timeout)
                return {"success": True, "loaded": True}

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

            elif action == "new_tab":
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

            elif action == "select_tab":
                if tab_index is None:
                    return {"error": "args.tab_index required"}
                try:
                    page = await pool.switch_page(tab_index)
                except ValueError as e:
                    return {"error": str(e)}
                return {"success": True, "switched_to": tab_index, "url": page.url}

            elif action == "tabs":
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
        """Register the browser tool: the core parameters typed, the rest in ``args``."""
        tool_instance = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def browser(
            action: Annotated[str, Field(description=f"{', '.join(CORE)}; help lists the rest")],
            selector: Annotated[Optional[str], Field(description="Element: a snapshot ref (@e2) or a CSS selector")] = None,
            url: Annotated[Optional[str], Field(description="navigate: the URL")] = None,
            text: Annotated[Optional[str], Field(description="fill/type: the text; wait: text to appear")] = None,
            key: Annotated[Optional[str], Field(description="press: Enter, Tab, Escape, ArrowDown, Control+a")] = None,
            code: Annotated[Optional[str], Field(description="evaluate: JavaScript")] = None,
            interactive: Annotated[bool, Field(description="snapshot: interactive elements only, flat")] = False,
            compact: Annotated[bool, Field(description="snapshot: drop empty structure")] = False,
            depth: Annotated[Optional[int], Field(description="snapshot: tree depth limit")] = None,
            outline: Annotated[bool, Field(description="read: headings only")] = False,
            filter: Annotated[Optional[str], Field(description="read: only sections that mention this")] = None,
            annotate: Annotated[bool, Field(description="screenshot: box every ref, label [N] = @eN")] = False,
            timeout: Annotated[Optional[int], Field(description="wait: milliseconds")] = None,
            tab_id: Annotated[Optional[str], Field(description="Tab from tabs; default the active tab")] = None,
            target_browser: Annotated[Optional[str], Field(description="chrome | firefox, when several are connected")] = None,
            topic: Annotated[Optional[str], Field(description="help: one topic")] = None,
            args: Annotated[Optional[dict], Field(description="Parameters of non-core actions, as help names them")] = None,
        ) -> Any:
            extra = dict(args or {})
            unknown = sorted(set(extra) - _ARGS)
            if unknown:
                return _result_to_mcp({"error": f"Unknown args {unknown}. Typed parameters go outside args; action=\"help\" names each action's args."})
            result = await tool_instance.execute(
                action=action, selector=selector, url=url, text=text, key=key, code=code,
                interactive=interactive, compact=compact, depth=depth, outline=outline, filter=filter,
                annotate=annotate, timeout=timeout, tab_id=tab_id, target_browser=target_browser, topic=topic,
                **extra,
            )
            # Text (a tree, a page, help) goes out as text; a dict as JSON, with any
            # capture as a native image block rather than base64 in the text.
            return result if isinstance(result, str) else _result_to_mcp(result)


# What `args` may carry: every execute() parameter the schema does not type.
_ARGS = frozenset(inspect.signature(BrowserTool.execute).parameters) - {
    "self", "action", "selector", "url", "text", "key", "code", "interactive", "compact", "depth",
    "outline", "filter", "annotate", "timeout", "tab_id", "target_browser", "topic",
}


def create_browser_tool(
    headless: bool = True,
    cdp_endpoint: Optional[str] = None,
    backend: Optional[str] = None,
) -> BrowserTool:
    """Create a browser tool instance."""
    return BrowserTool(headless=headless, cdp_endpoint=cdp_endpoint, backend=backend)


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
