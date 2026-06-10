"""Raw Chrome DevTools Protocol method dispatch.

Decomplected from BrowserTool: `browser` is *action-oriented* (high-level
verbs like `navigate`, `click`); `cdp` is *method-oriented* (sends a CDP
method by name with raw params). Same backing transports (in-process ZAP
server → legacy HTTP bridge), no Playwright fallback — for that, use
`browser` or `playwright`.

Use this tool when you need a CDP method the high-level surface doesn't
expose, want to inspect raw protocol responses, or are wiring something
to the protocol directly.

Example::

    cdp(action="send", method="Page.navigate", params={"url": "https://example.com"})
    cdp(action="send", method="Runtime.evaluate", params={"expression": "1+1"})
    cdp(action="tabs")          # list connected tabs (Target.getTargets)
    cdp(action="status")        # connection status
    cdp(action="list_browsers") # which providers (firefox/chrome/safari) are connected
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Annotated, Literal, Optional, Union

from pydantic import Field
from mcp.server import FastMCP

from hanzo_tools.core import BaseTool

logger = logging.getLogger(__name__)


CdpAction = Annotated[
    Literal["send", "tabs", "status", "list_browsers", "claim_browser", "release_browser"],
    Field(description="CDP action"),
]


async def _dispatch_raw(
    method: str,
    params: Optional[dict] = None,
    *,
    browser: Optional[str] = None,
    tab_id: Optional[Union[str, int]] = None,
    client_id: Optional[str] = None,
    timeout: float = 30.0,
) -> dict:
    """Dispatch a raw CDP method to the connected browser provider.

    Path order — same as BrowserTool:
      1. In-process ZAP server (microsecond round-trip; preferred).
      2. Legacy HTTP bridge on :9224 (kept as fallback for non-ZAP clients).

    Pin transport via ``BROWSER_TRANSPORT=zap|http|auto`` (default ``auto``).
    """
    params = dict(params or {})

    # Normalize tab id (accept "tab-123" or 123 or "123")
    if tab_id is not None:
        t = tab_id
        if isinstance(t, str) and t.startswith("tab-"):
            t = t[4:]
        try:
            t = int(t)
        except (TypeError, ValueError):
            pass
        params.setdefault("tabId", t)

    transport = os.environ.get("BROWSER_TRANSPORT", "auto").strip().lower()
    if transport not in {"zap", "http", "auto"}:
        transport = "auto"

    # 1) ZAP path
    if transport in {"zap", "auto"}:
        try:
            from hanzo_tools.browser.zap_server import get_server

            srv = get_server()
            if srv is not None and srv.has_client(browser=browser):
                try:
                    raw = await srv.send(
                        method, params, browser=browser, client_id=client_id
                    )
                    return {"success": True, "transport": "zap", "method": method, "result": raw}
                except Exception as e:
                    if transport == "zap":
                        return {"error": str(e), "transport": "zap", "method": method}
                    logger.debug("zap dispatch failed, falling back to http: %s", e)
        except ImportError:
            pass

        if transport == "zap":
            return {
                "error": "ZAP transport selected but no extension client matched",
                "transport": "zap",
                "method": method,
            }

    # 2) HTTP fallback — legacy CDP bridge speaks raw CDP via a `cdp` action
    try:
        import aiohttp

        payload: dict[str, Any] = {"action": "cdp", "method": method, "params": params}
        if browser:
            payload["browser"] = browser
        if client_id:
            payload["clientId"] = client_id

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:9224",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                body = await resp.text()
                try:
                    import json

                    parsed = json.loads(body)
                except Exception:
                    parsed = {"raw": body}
                parsed.setdefault("transport", "http")
                parsed.setdefault("method", method)
                if resp.status == 200:
                    parsed.setdefault("success", True)
                else:
                    parsed.setdefault("status", resp.status)
                    parsed.setdefault("error", parsed.get("error") or body[:200])
                return parsed
    except Exception as e:
        logger.debug("CDP dispatch HTTP fallback failed: %s", e)
        return {"error": str(e), "transport": "http", "method": method}


class CdpTool(BaseTool):
    """Raw Chrome DevTools Protocol method dispatch.

    Peer of ``browser`` (action-oriented) and ``playwright`` (Playwright API).
    Sends any CDP method directly to a connected browser via the ZAP server
    (extension) or legacy CDP HTTP bridge. Does NOT fall back to Playwright.
    """

    name = "cdp"

    @property
    def description(self) -> str:
        return """Raw Chrome DevTools Protocol dispatch — peer of `browser`.

ACTIONS:
- send       : send a CDP method (method=, params=, tab_id=, target_browser=)
- tabs       : Target.getTargets — list connected tabs
- status     : Browser.getVersion — connection + version
- list_browsers : list extension providers (firefox/chrome/safari/edge) connected
- claim_browser / release_browser : exclusive-lease management

EXAMPLES:
- cdp(action="send", method="Page.navigate", params={"url": "https://example.com"})
- cdp(action="send", method="Runtime.evaluate", params={"expression": "document.title"})
- cdp(action="tabs")
- cdp(action="status")

Use `browser` for high-level verbs (navigate, click, screenshot).
Use `playwright` for headless Playwright automation.
"""

    async def call(self, ctx, action: str = "send", **kwargs) -> dict[str, Any]:
        return await self.execute(action=action, **kwargs)

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
        ) -> str:
            result = await tool_instance.execute(
                action=action,
                method=method,
                params=params,
                tab_id=tab_id,
                target_browser=target_browser,
                client_id=client_id,
                timeout=timeout,
            )
            return json.dumps(result, indent=2, default=str)

    async def execute(
        self,
        action: str = "send",
        # Raw CDP
        method: Optional[str] = None,
        params: Optional[dict] = None,
        # Routing
        tab_id: Optional[Union[str, int]] = None,
        target_browser: Optional[str] = None,
        client_id: Optional[str] = None,
        # Timeout
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        t = float(timeout) if timeout else 30.0

        # === Local actions (handled in-process) =====================
        if action == "list_browsers":
            try:
                from hanzo_tools.browser.zap_server import get_server

                srv = get_server()
                if srv is None:
                    return {"error": "zap server not running"}
                clients = []
                for c in srv.clients:
                    clients.append(
                        {
                            "client_id": c.client_id,
                            "browser": getattr(c, "browser", None),
                            "label": getattr(c, "label", None),
                        }
                    )
                return {"success": True, "browsers": clients, "count": len(clients)}
            except Exception as e:
                return {"error": str(e)}

        if action == "claim_browser":
            try:
                from hanzo_tools.browser.zap_server import DEFAULT_LEASE_TTL, get_server

                srv = get_server()
                if srv is None:
                    return {"error": "zap server not running"}
                client = srv.resolve_client(client_id=client_id, browser=target_browser)
                if client is None:
                    return {"error": "no matching extension client"}
                lease = srv.claim(client.client_id, ttl=t)
                return {
                    "success": True,
                    "client_id": lease.client_id,
                    "holder": lease.holder,
                    "expires_at": lease.expires_at,
                }
            except Exception as e:
                return {"error": str(e)}

        if action == "release_browser":
            try:
                from hanzo_tools.browser.zap_server import get_server

                srv = get_server()
                if srv is None:
                    return {"error": "zap server not running"}
                if client_id:
                    return {"success": srv.release(client_id), "client_id": client_id}
                released = [c.client_id for c in list(srv.clients) if srv.release(c.client_id)]
                return {"success": True, "released": released}
            except Exception as e:
                return {"error": str(e)}

        # === Sugared CDP methods ==================================
        sugared = {
            "tabs": ("Target.getTargets", {}),
            "status": ("Browser.getVersion", {}),
        }
        if action in sugared:
            m, p = sugared[action]
            return await _dispatch_raw(
                m,
                p,
                browser=target_browser,
                tab_id=tab_id,
                client_id=client_id,
                timeout=t,
            )

        # === Raw send ==============================================
        if action == "send":
            if not method:
                return {
                    "error": "method required for action=send (e.g. 'Page.navigate')",
                    "action": "send",
                }
            return await _dispatch_raw(
                method,
                params,
                browser=target_browser,
                tab_id=tab_id,
                client_id=client_id,
                timeout=t,
            )

        return {
            "error": f"unknown action '{action}'. Try: send, tabs, status, list_browsers, claim_browser, release_browser",
        }
