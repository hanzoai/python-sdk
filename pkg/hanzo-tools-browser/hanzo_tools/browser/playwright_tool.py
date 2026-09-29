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
        return """Headless Playwright Chromium, never the user's browser: the `browser`
tool's actions, pinned to Playwright for deterministic runs. It has no snapshot
refs (those come from the Hanzo extension through `browser`), so act with CSS
selectors: snapshot answers an aria tree to read them from.

Core: navigate, snapshot, click, fill, type, press, read, screenshot, evaluate,
wait, tabs. action="help" lists the rest; their parameters go in args."""
