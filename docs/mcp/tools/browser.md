# Browser Tool

Complete Playwright automation with 70+ actions.

→ **Full documentation: [../../tools/browser.md](../../tools/browser.md)**

## Quick Reference

```python
# Navigate
browser(action="navigate", url="https://example.com")

# Click element
browser(action="click", selector="button.submit")

# Fill form
browser(action="fill", selector="input[name=email]", text="user@example.com")

# Screenshot
browser(action="screenshot", full_page=True)

# Device emulation
browser(action="emulate", device="mobile")
```

Supports: navigation, forms, mouse, touch, assertions, storage, network, and more.
