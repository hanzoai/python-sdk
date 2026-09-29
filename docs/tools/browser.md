# hanzo-tools-browser

One `browser` tool that drives the user's own browser, signed in, through the
Hanzo extension, or a headless Playwright Chromium when no extension is
connected. `playwright` is the same tool pinned to Playwright; `cdp` sends a raw
DevTools method.

## Installation

```bash
pip install hanzo-tools-browser
pip install 'hanzo-tools-browser[playwright]' && playwright install chromium   # headless fallback
```

## The loop: snapshot, act on refs, snapshot again

```python
browser(action="navigate", url="https://example.com/login")
browser(action="snapshot", interactive=True)
# Login — https://example.com/login (4 refs)
# - textbox "Email" [ref=e3]
# - textbox "Password" [ref=e4]
# - checkbox "Remember me" [ref=e5]
# - button "Sign in" [ref=e6]
browser(action="fill", selector="@e3", text="me@example.com")
browser(action="fill", selector="@e4", text="…")
browser(action="click", selector="@e6")
browser(action="read")                      # the page as markdown
```

- `snapshot` prints the rendered accessibility tree. Every node an agent can act
  on carries `[ref=eN]`; `interactive=True` lists only those, flat. `compact`,
  `depth` and `selector` (a CSS selector or a ref) trim it.
- `selector` takes a ref (`@e3`, or `e3`) or a CSS selector, everywhere.
- A ref names one element while that element stays on the page, across
  snapshots. After a navigation, or once its element is removed, it is refused
  with "run snapshot again".
- A click on an element under a consent banner, modal or overlay is refused
  before any event fires, and the error names the cover. Act on the cover, then
  snapshot again.
- `read` returns the page as markdown; `outline=True` keeps the headings,
  `filter="pricing"` only the sections that mention it.
- `screenshot annotate=True` boxes every on-screen ref and labels it `[N]`,
  which is ref `@eN`, and returns the legend beside the image.

Refs, `annotate` and the markdown reader live in the extension's page engine;
on Playwright `snapshot` answers an aria tree without refs, so act with CSS
selectors there.

## Progressive surface

The schema carries the core actions only:

| Action | Parameters |
| --- | --- |
| `navigate` | `url` — returns once the page has loaded |
| `snapshot` | `interactive`, `compact`, `depth`, `selector` |
| `click`, `fill`, `type`, `press` | `selector`, `text`, `key` |
| `read` | `outline`, `filter` |
| `screenshot` | `annotate` |
| `evaluate` | `code` |
| `wait` | `selector` or `text`, `timeout` |
| `tabs` | — (`tab_id` targets a tab in any action) |
| `help` | `topic` |

`browser(action="help")` lists every other action by topic (interact,
navigation, tabs, page, assert, storage, network, emulation, debug) with a
one-line usage each. Their parameters travel in `args`:

```python
browser(action="help", topic="interact")
browser(action="select", selector="@e8", args={"value": "Weekly"})
browser(action="scroll", args={"delta_y": 600})
browser(action="screenshot", args={"full_page": True, "full_res": True})
browser(action="emulate", args={"device": "iphone_14"})     # Playwright
```

Actions marked `(Playwright)` in help run on headless Playwright only.

## Screenshots

A screenshot comes back as an image block, downscaled to 1280px JPEG; the
native capture is written to a file whose path is returned. `args.full_res`
inlines the native pixels.

## Parallel agents (Playwright)

`browser(action="new_context")` opens an isolated Playwright session with its
own cookies and storage: one Chromium, one context per agent.
