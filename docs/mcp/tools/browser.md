# Browser Tool

Drive the user's browser through the Hanzo extension (headless Playwright when
none is connected): snapshot, act on refs, snapshot again.

→ **Full documentation: [../../tools/browser.md](../../tools/browser.md)**

## Quick Reference

```python
browser(action="navigate", url="https://example.com")
browser(action="snapshot", interactive=True)      # - button "Sign in" [ref=e2]
browser(action="click", selector="@e2")
browser(action="fill", selector="@e3", text="user@example.com")
browser(action="read", filter="pricing")           # the page as markdown
browser(action="screenshot", annotate=True)        # labels [N] = @eN
browser(action="help")                             # every other action
```
