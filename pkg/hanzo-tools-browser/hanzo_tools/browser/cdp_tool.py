"""Raw Chrome DevTools Protocol method dispatch — zapd-native.

Peer of ``browser`` (action-oriented). ``cdp`` is *method-oriented*: it sends a
CDP method by name with raw params straight to a connected browser provider over
the shared local zapd router (``~/.zap/run/zapd.sock``). Same backing transport
as ``browser`` — no in-process server, no :9224 HTTP bridge, no Playwright
fallback. The method name goes on the wire verbatim (``Target.getTargets``,
``Page.navigate`` …) so the extension's CDP dispatch handles it directly; there
is no ``{"action": "cdp"}`` envelope to misroute.

Use ``browser`` for high-level verbs (navigate, click, screenshot).
Use ``cdp`` when you need a CDP method the high-level surface doesn't expose.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any, Union, Optional, Annotated

from pydantic import Field
from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, capture
from hanzo_tools.core.unified import _result_to_mcp
from hanzo_tools.browser.browser_tool import _extract_b64
from hanzo_tools.browser.zapd_consumer import get_consumer

logger = logging.getLogger(__name__)


# Sugared actions → the bare CDP method they map to.
_SUGARED: dict[str, str] = {
    "tabs": "Target.getTargets",
    "status": "Browser.getVersion",
    "list_browsers": "",  # handled locally via the zapd provider list
}


async def _route_cdp(
    method: str,
    params: Optional[dict],
    *,
    target_browser: Optional[str] = None,
    tab_id: Union[str, int, None] = None,
    client_id: Optional[str] = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Route a raw CDP method to a browser provider via the local zapd router.

    Mirrors ``browser_tool._extension_command`` but sends the method name
    verbatim instead of mapping a high-level action. One transport, one codec.
    """
    import asyncio

    consumer = get_consumer()
    if consumer is None:
        return {"error": "zapd not reachable (~/.zap/run/zapd.sock)", "transport": "native-zap", "method": method}

    try:
        provider = await asyncio.to_thread(consumer.resolve_browser, target_browser, client_id)
    except Exception as e:
        return {"error": str(e), "transport": "native-zap", "method": method}
    if not provider:
        return {"error": "no browser provider connected over zapd", "transport": "native-zap", "method": method}

    wire: dict[str, Any] = dict(params or {})
    if tab_id is not None:
        wire.setdefault("tabId", tab_id)
    str_params = {k: (v if isinstance(v, str) else str(v)) for k, v in wire.items() if v is not None}

    try:
        raw = await asyncio.to_thread(consumer.route, provider, method, str_params, timeout)
    except Exception as e:
        return {"error": str(e), "transport": "native-zap", "method": method}

    text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else raw
    meta = {"transport": "native-zap", "source": "zapd", "provider": provider, "method": method}
    # Raw dispatch, but a capture is still a capture: it goes to a file and comes
    # back as pixels, never as base64 in the JSON text. Same door as every other
    # tool. Pass CDP's own format/quality (and maxWidth) in params to steer it.
    if method.endswith("captureScreenshot") and isinstance(text, str):
        b64 = _extract_b64(text)
        if b64:
            try:
                data = base64.b64decode(b64)
                fmt = "jpeg" if data[:3] == b"\xff\xd8\xff" else "png"
                return {**capture(data, fmt=fmt), **meta}
            except Exception as e:
                logger.warning(f"cdp capture decode failed ({e}); returning raw")
    return {"success": True, **meta, "result": text}


async def _list_browsers() -> dict[str, Any]:
    """List browser providers connected to the local zapd router."""
    import asyncio

    consumer = get_consumer()
    if consumer is None:
        return {"error": "zapd not reachable (~/.zap/run/zapd.sock)", "transport": "native-zap"}
    try:
        provs = await asyncio.to_thread(consumer.list_providers)
    except Exception as e:
        return {"error": str(e), "transport": "native-zap"}
    browsers = [p for p in provs if p.get("id", "").startswith("browser:")]
    return {"success": True, "transport": "native-zap", "browsers": browsers, "count": len(browsers)}


CdpAction = Annotated[
    str,
    Field(description="CDP action: send | tabs | status | list_browsers"),
]


class CdpTool(BaseTool):
    """Raw Chrome DevTools Protocol method dispatch — peer of ``browser``."""

    name = "cdp"

    @property
    def description(self) -> str:
        return """Raw Chrome DevTools Protocol dispatch — peer of `browser`.

ACTIONS:
- send       : send a CDP method (method=, params=, tab_id=, target_browser=)
- tabs       : Target.getTargets — list connected tabs
- status     : Browser.getVersion — connection + version
- list_browsers : list extension providers (firefox/chrome/safari/edge) connected

Page.captureScreenshot answers with a downscaled JPEG (~1280px, q70) by default
to save context; the full-resolution capture is saved to a file whose path is
returned. Pass params={"format":"png","maxWidth":0} for pixel detail.

EXAMPLES:
- cdp(action="send", method="Page.navigate", params={"url": "https://example.com"})
- cdp(action="send", method="Runtime.evaluate", params={"expression": "document.title"})
- cdp(action="tabs")
- cdp(action="status")

Use `browser` for high-level verbs (navigate, click, screenshot).
"""

    async def call(self, ctx, action: str = "send", **kwargs) -> dict[str, Any]:
        return await self.execute(action=action, **kwargs)

    async def execute(
        self,
        action: str = "send",
        method: Optional[str] = None,
        params: Optional[dict] = None,
        tab_id: Optional[Union[str, int]] = None,
        target_browser: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        t = float(timeout) if timeout else 30.0

        if action == "list_browsers":
            return await _list_browsers()

        if action in _SUGARED:
            return await _route_cdp(
                _SUGARED[action], {},
                target_browser=target_browser, tab_id=tab_id, client_id=client_id, timeout=t,
            )

        if action == "send":
            if not method:
                return {"error": "method required for action=send (e.g. 'Page.navigate')", "action": "send"}
            return await _route_cdp(
                method, params,
                target_browser=target_browser, tab_id=tab_id, client_id=client_id, timeout=t,
            )

        return {"error": f"unknown action '{action}'. Try: send, tabs, status, list_browsers"}

    def register(self, mcp_server: FastMCP) -> None:
        """Register the cdp tool with an MCP server."""
        tool_instance = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def cdp(
            action: CdpAction = "send",
            method: Annotated[
                Optional[str],
                Field(description="CDP method name (e.g. 'Page.navigate', 'Runtime.evaluate')"),
            ] = None,
            params: Annotated[
                Optional[dict],
                Field(description="CDP method params"),
            ] = None,
            tab_id: Annotated[
                Optional[Union[str, int]],
                Field(description="Target tab id (string or int)"),
            ] = None,
            target_browser: Annotated[
                Optional[str],
                Field(description="Provider filter: firefox|chrome|safari|edge"),
            ] = None,
            client_id: Annotated[
                Optional[str],
                Field(description="Specific extension client id"),
            ] = None,
            timeout: Annotated[
                Optional[float],
                Field(description="Per-call timeout (seconds)"),
            ] = None,
        ) -> Any:
            result = await tool_instance.execute(
                action=action,
                method=method,
                params=params,
                tab_id=tab_id,
                target_browser=target_browser,
                client_id=client_id,
                timeout=timeout,
            )
            return _result_to_mcp(result)
