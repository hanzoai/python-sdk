"""WebDriver BiDi client for Firefox 129+ and Chrome 124+.

This is the v1.10.0 "trusted input" backend that complements the
WebExtension scripting backend (the cdp_bridge_server's WebSocket
to the browser extension). Where the extension produces synthetic
events with isTrusted=false (which strict frameworks like Drupal
AJAX, certain React libraries, and security-aware sites reject),
BiDi produces real browser input events with isTrusted=true.

Architecture (decomplected, three orthogonal layers):

  Layer 3 — ergonomic alias: hanzo.click(selector)
    └─ auto-routes to BiDi when available, extension otherwise

  Layer 2 — canonical primitives:
    Input.dispatchMouseEvent({x, y, type})
      ├─ synthetic path (extension backend)
      └─ trusted path (this module, BiDi backend)

  Layer 1 — wire transport:
    JSON-RPC over WebSocket to ws://localhost:9222/session

Per WebDriver BiDi spec:
  https://w3c.github.io/webdriver-bidi/

To enable: launch Firefox with `--remote-debugging-port=9222` (Firefox
129+) or Chrome with the same flag (Chrome 124+). The bridge will
auto-detect on startup and advertise BiDi.* methods in its capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:  # pragma: no cover
    websockets = None
    WebSocketClientProtocol = Any  # type: ignore

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class BiDiSession:
    """One BiDi session against one browser.

    Holds the WebSocket connection, the session_id, the open browsing
    contexts (one per tab), and the request-id → future map used to
    correlate JSON-RPC responses with their callers.
    """

    ws: WebSocketClientProtocol
    session_id: str | None = None
    next_id: int = 1
    pending: dict[int, asyncio.Future] = field(default_factory=dict)
    contexts: dict[str, dict] = field(default_factory=dict)  # context_id → info
    reader_task: asyncio.Task | None = None

    def _next_id(self) -> int:
        i = self.next_id
        self.next_id += 1
        return i


class BiDiClient:
    """High-level WebDriver BiDi client.

    Methods that the bridge can call:
      - connect()              — open WebSocket, create session
      - close()                — clean shutdown
      - list_contexts()        — list browsing contexts (one per tab)
      - find_context_by_url()  — locate the tab matching a URL substring
      - input_mouse_click(context_id, x, y, *, button=0) — TRUSTED click
      - input_key_down/up(context_id, key)               — TRUSTED keyboard
      - input_insert_text(context_id, text)              — TRUSTED typing
      - browsing_context_navigate(context_id, url)       — TRUSTED nav
      - browsing_context_capture_screenshot(context_id)  — native screenshot
      - script_evaluate(context_id, expression)          — page-context eval
      - subscribe(events)                                — event streams
    """

    def __init__(self, host: str = "localhost", port: int = 9222) -> None:
        self.host = host
        self.port = port
        self.session: BiDiSession | None = None

    @property
    def connected(self) -> bool:
        return self.session is not None and self.session.ws is not None and not self.session.ws.closed

    # ─────────────────────────────────────────────────────────────────
    # Discovery: probe whether the browser exposes a BiDi endpoint
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    async def probe(cls, host: str = "localhost", port: int = 9222, timeout: float = 1.5) -> str | None:
        """Return the BiDi WebSocket URL if available, else None.

        Firefox 129+ exposes the BiDi endpoint at GET /json/version which
        returns JSON containing 'webSocketDebuggerUrl'. Chrome 124+ exposes
        a similar endpoint with both 'webSocketDebuggerUrl' (legacy CDP)
        and (optionally) BiDi support via the same socket.
        """
        if websockets is None:
            return None
        url = f"http://{host}:{port}/json/version"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as sess:
                async with sess.get(url) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    # Firefox: "webSocketDebuggerUrl": "ws://host:port/session"
                    # Chrome: "webSocketDebuggerUrl": "ws://host:port/devtools/browser/<id>"
                    return data.get("webSocketDebuggerUrl")
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────
    # Connection lifecycle
    # ─────────────────────────────────────────────────────────────────
    async def connect(self) -> None:
        """Open the WebSocket and create a BiDi session."""
        if self.connected:
            return
        if websockets is None:
            raise RuntimeError("websockets package not installed")

        ws_url = await self.probe(self.host, self.port)
        if not ws_url:
            raise RuntimeError(
                f"No BiDi endpoint at http://{self.host}:{self.port}/json/version. "
                f"Launch Firefox with --remote-debugging-port={self.port} "
                f"or Chrome with --remote-debugging-port={self.port}."
            )

        logger.info("BiDi connecting to %s", ws_url)
        ws = await websockets.connect(ws_url, max_size=None)
        self.session = BiDiSession(ws=ws)
        self.session.reader_task = asyncio.create_task(self._reader_loop())

        # Create a BiDi session
        result = await self._send("session.new", {"capabilities": {}})
        self.session.session_id = result.get("sessionId")
        logger.info("BiDi session created: %s", self.session.session_id)

    async def close(self) -> None:
        if not self.session:
            return
        if self.session.reader_task and not self.session.reader_task.done():
            self.session.reader_task.cancel()
        try:
            if self.session.ws and not self.session.ws.closed:
                await self.session.ws.close()
        except Exception:
            pass
        self.session = None

    # ─────────────────────────────────────────────────────────────────
    # Wire protocol
    # ─────────────────────────────────────────────────────────────────
    async def _reader_loop(self) -> None:
        """Receive messages and dispatch to pending futures or event handlers."""
        assert self.session is not None
        try:
            async for raw in self.session.ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                msg_id = msg.get("id")
                if msg_id is not None and msg_id in self.session.pending:
                    fut = self.session.pending.pop(msg_id)
                    if msg.get("type") == "error" or "error" in msg:
                        err = msg.get("error") or msg.get("message", "unknown")
                        fut.set_exception(RuntimeError(f"BiDi error: {err}"))
                    else:
                        fut.set_result(msg.get("result", {}))
                # else: event — could route to subscribers (future work)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("BiDi reader loop exited: %s", e)

    async def _send(self, method: str, params: dict | None = None, timeout: float = 30.0) -> dict:
        """Send a method call, await the response."""
        if not self.connected:
            await self.connect()
        assert self.session is not None
        rid = self.session._next_id()
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self.session.pending[rid] = fut
        msg = {"id": rid, "method": method, "params": params or {}}
        await self.session.ws.send(json.dumps(msg))
        return await asyncio.wait_for(fut, timeout=timeout)

    # ─────────────────────────────────────────────────────────────────
    # Browsing contexts (one per tab)
    # ─────────────────────────────────────────────────────────────────
    async def list_contexts(self) -> list[dict]:
        """Return the list of top-level browsing contexts (tabs)."""
        result = await self._send("browsingContext.getTree", {})
        contexts = result.get("contexts", [])
        # Flatten so the caller has [{context, url, ...}, ...]
        return contexts

    async def find_context_by_url(self, url_substring: str) -> str | None:
        contexts = await self.list_contexts()
        for c in contexts:
            if url_substring in (c.get("url") or ""):
                return c.get("context")
        return None

    async def navigate(self, context_id: str, url: str, wait: str = "complete") -> dict:
        """Navigate a browsing context to a URL. wait ∈ {none, interactive, complete}."""
        return await self._send("browsingContext.navigate", {
            "context": context_id, "url": url, "wait": wait,
        })

    async def capture_screenshot(self, context_id: str) -> str:
        """Returns a base64-encoded PNG of the entire viewport."""
        result = await self._send("browsingContext.captureScreenshot", {"context": context_id})
        return result.get("data", "")

    # ─────────────────────────────────────────────────────────────────
    # Trusted input — THE WHOLE POINT of this backend
    # ─────────────────────────────────────────────────────────────────
    async def input_mouse_click(self, context_id: str, x: float, y: float, *,
                                 button: int = 0, click_count: int = 1) -> dict:
        """Dispatch a TRUSTED click at (x, y) in the given context's viewport.

        Generates pointerMove → pointerDown → pointerUp → pointerMove(0,0).
        Events have isTrusted=true at the page level — Drupal AJAX, React
        with isTrusted checks, and any other framework will honor them
        because they ARE real browser input events.
        """
        return await self._send("input.performActions", {
            "context": context_id,
            "actions": [{
                "type": "pointer",
                "id": "default-mouse",
                "parameters": {"pointerType": "mouse"},
                "actions": [
                    {"type": "pointerMove", "x": int(x), "y": int(y), "duration": 0},
                    {"type": "pointerDown", "button": button},
                    {"type": "pause", "duration": 30},
                    {"type": "pointerUp", "button": button},
                ],
            }],
        })

    async def input_double_click(self, context_id: str, x: float, y: float, *, button: int = 0) -> dict:
        return await self._send("input.performActions", {
            "context": context_id,
            "actions": [{
                "type": "pointer", "id": "default-mouse",
                "parameters": {"pointerType": "mouse"},
                "actions": [
                    {"type": "pointerMove", "x": int(x), "y": int(y), "duration": 0},
                    {"type": "pointerDown", "button": button},
                    {"type": "pointerUp", "button": button},
                    {"type": "pause", "duration": 30},
                    {"type": "pointerDown", "button": button},
                    {"type": "pointerUp", "button": button},
                ],
            }],
        })

    async def input_key_press(self, context_id: str, key: str) -> dict:
        """Press a single key. `key` follows the W3C WebDriver Key spec
        (e.g., 'Enter', 'Tab', 'Escape', or a literal character)."""
        return await self._send("input.performActions", {
            "context": context_id,
            "actions": [{
                "type": "key", "id": "default-keyboard",
                "actions": [
                    {"type": "keyDown", "value": key},
                    {"type": "keyUp", "value": key},
                ],
            }],
        })

    async def input_insert_text(self, context_id: str, text: str) -> dict:
        """Type a string with trusted keyboard events."""
        actions: list[dict] = []
        for ch in text:
            actions.append({"type": "keyDown", "value": ch})
            actions.append({"type": "keyUp", "value": ch})
        return await self._send("input.performActions", {
            "context": context_id,
            "actions": [{"type": "key", "id": "default-keyboard", "actions": actions}],
        })

    # ─────────────────────────────────────────────────────────────────
    # Script evaluation (similar to extension scripting, but BiDi-native)
    # ─────────────────────────────────────────────────────────────────
    async def script_evaluate(self, context_id: str, expression: str, *,
                              await_promise: bool = True) -> dict:
        """Evaluate JS in the page context. Result has 'result' field
        with serialized value."""
        return await self._send("script.evaluate", {
            "expression": expression,
            "target": {"context": context_id},
            "awaitPromise": await_promise,
            "userActivation": True,  # so popup blockers etc. don't fire
        })

    # ─────────────────────────────────────────────────────────────────
    # Convenience: get viewport coords of an element by CSS selector,
    # then click. This is the equivalent of hanzo.click but with the
    # actual click being TRUSTED via input.performActions.
    # ─────────────────────────────────────────────────────────────────
    async def click_selector(self, context_id: str, selector: str) -> dict:
        """Composite: scrollIntoView + getBoundingClientRect + trusted click."""
        # 1) Resolve the element's center coordinates via script.evaluate
        # (the eval itself runs in page context — that's fine; only the
        # CLICK needs to be trusted, and that's what input.performActions does)
        js = f"""
        (function() {{
          const el = document.querySelector({json.dumps(selector)});
          if (!el) return null;
          el.scrollIntoView({{block: 'center', behavior: 'instant'}});
          const r = el.getBoundingClientRect();
          return {{x: r.left + r.width/2, y: r.top + r.height/2}};
        }})()
        """
        ev = await self.script_evaluate(context_id, js, await_promise=False)
        result = ev.get("result", {})
        # BiDi script result shape: {type, value} or {type: 'object', value: {x: ..., y: ...}}
        if result.get("type") == "null":
            return {"clicked": False, "reason": "element not found"}
        val = result.get("value", {})
        x = val.get("x") if isinstance(val, dict) else None
        y = val.get("y") if isinstance(val, dict) else None
        if x is None or y is None:
            return {"clicked": False, "reason": "no coords returned", "raw": result}
        await self.input_mouse_click(context_id, x, y)
        return {"clicked": True, "isTrusted": True, "x": x, "y": y}


# Convenience: a singleton-ish auto-detected client for the bridge.
_default_client: BiDiClient | None = None


async def get_or_connect(host: str = "localhost", port: int = 9222) -> BiDiClient | None:
    """Return a connected BiDi client, or None if the browser isn't
    launched with --remote-debugging-port. Cached after first success."""
    global _default_client
    if _default_client is not None and _default_client.connected:
        return _default_client
    client = BiDiClient(host=host, port=port)
    try:
        await client.connect()
    except Exception as e:
        logger.info("BiDi unavailable: %s", e)
        return None
    _default_client = client
    return client
