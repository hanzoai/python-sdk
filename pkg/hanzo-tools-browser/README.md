# hanzo-tools-browser

Browser automation tools for Hanzo MCP using Playwright.

## Installation

```bash
pip install hanzo-tools-browser
```

## Tools

### browser - Complete Playwright API
70+ browser actions for full automation.

**Navigation:**
```python
browser(action="navigate", url="https://example.com")
browser(action="go_back")
browser(action="reload")
```

**Input:**
```python
browser(action="click", selector="button.submit")
browser(action="fill", selector="input[name=email]", text="user@example.com")
browser(action="type", selector="textarea", text="Hello")
```

**Touch/Mobile:**
```python
browser(action="tap", selector=".button")
browser(action="swipe", selector=".carousel", direction="left")
browser(action="emulate", device="mobile")  # or tablet, laptop
```

**Assertions:**
```python
browser(action="expect_visible", selector=".modal")
browser(action="expect_text", selector="h1", expected="Welcome")
browser(action="expect_url", expected="*/dashboard*")
```

**Content:**
```python
browser(action="get_text", selector=".content")
browser(action="screenshot", full_page=True)
browser(action="pdf")
```

**Parallel Agents:**
```python
# Each agent gets isolated session
browser(action="new_context")  # Separate cookies/storage
```

**Device Presets:**
- `mobile` - iPhone-like (390x844, touch)
- `tablet` - iPad-like (1024x1366, touch)
- `laptop` - MacBook-like (1440x900)
- `iphone_14`, `pixel_7`, `ipad_pro`, etc.

## License

MIT
