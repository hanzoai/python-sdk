"""Playwright-pinned browser tool.

Same action surface as ``BrowserTool`` but with ``backend="playwright"``
forced — never dispatches through the extension or CDP bridge. Use this
when you want deterministic headless automation regardless of whether a
browser extension is connected to this MCP.

The high-level ``browser`` tool auto-detects transport. Calling
``playwright`` is the explicit "I want Playwright, period" path.
"""

from __future__ import annotations

import logging
from typing import Optional

from hanzo_tools.browser.browser_tool import BrowserTool

logger = logging.getLogger(__name__)


class PlaywrightTool(BrowserTool):
    """Browser automation pinned to the Playwright backend.

    Skips the in-process ZAP server (extension dispatch) and the legacy
    CDP HTTP bridge entirely — every action goes through Playwright's
    Chromium driver. Suitable for headless test runs, CI pipelines, and
    any context where attaching to a user-controlled browser is wrong.

    The action surface (navigate, click, fill, screenshot, expect_*, ...)
    is identical to ``BrowserTool`` — only the transport pin differs.
    """

    name = "playwright"

    def __init__(
        self,
        headless: bool = True,
        cdp_endpoint: Optional[str] = None,
    ):
        # Force backend="playwright" — overrides BROWSER_BACKEND env, ignores
        # extension config, skips ZAP/CDP-bridge lifecycle bootstrap.
        super().__init__(
            headless=headless,
            cdp_endpoint=cdp_endpoint,
            backend="playwright",
        )

    @property
    def description(self) -> str:
        return """Playwright-pinned browser automation — peer of `browser` and `cdp`.

Same action surface as `browser` but forces backend="playwright":
- No extension dispatch (does not talk to Hanzo browser extension).
- No legacy CDP HTTP bridge.
- Pure async-playwright, headless by default.

Use `browser` for auto-routing (extension > CDP-bridge > Playwright).
Use `cdp` for raw Chrome DevTools Protocol method dispatch.
Use `playwright` for deterministic headless automation.
""" + BrowserTool.description.fget(self).split("CATEGORIES:", 1)[-1].rstrip()
