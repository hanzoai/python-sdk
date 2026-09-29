# hanzo-tools-browser

Browser tools for Hanzo MCP: `browser` drives the user's own browser through
the Hanzo extension (headless Playwright when none is connected), `playwright`
is the same tool pinned to Playwright, and `cdp` sends a raw DevTools method.

## Installation

```bash
pip install hanzo-tools-browser
pip install 'hanzo-tools-browser[playwright]' && playwright install chromium   # headless fallback
```

## The loop

```python
browser(action="navigate", url="https://example.com")
browser(action="snapshot", interactive=True)       # - button "Sign in" [ref=e2]
browser(action="click", selector="@e2")
browser(action="fill", selector="@e3", text="user@example.com")
browser(action="press", key="Enter")
browser(action="read", outline=True)               # the page as markdown
browser(action="screenshot", annotate=True)        # labels [N] = @eN, with a legend
```

`selector` takes a ref from the last snapshot or a CSS selector. A stale ref,
or a click on an element covered by a banner or modal, is refused with what to
do next.

## Progressive surface

The schema carries the core actions: navigate, snapshot, click, fill, type,
press, read, screenshot, evaluate, wait, tabs, help. `browser(action="help")`
lists the rest by topic, and their parameters go in `args`:

```python
browser(action="select", selector="@e4", args={"value": "Weekly"})
```

## License

MIT
