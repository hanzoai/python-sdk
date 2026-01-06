# hanzo-tools-browser

Complete browser automation with full Playwright API. Provides 70+ actions for navigation, forms, mouse control, assertions, and more.

## Installation

```bash
pip install hanzo-tools-browser
playwright install chromium
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
playwright install chromium
```

## Overview

`hanzo-tools-browser` provides comprehensive browser automation:

- **Navigation**: navigate, reload, go_back, go_forward
- **Input**: click, type, fill, press, select_option
- **Mouse**: hover, drag, scroll, mouse_move
- **Touch**: tap, swipe, pinch (mobile emulation)
- **Assertions**: expect_visible, expect_text, expect_url
- **Content**: get_text, get_attribute, screenshot
- **Storage**: cookies, localStorage, sessionStorage
- **Network**: route (mock/block requests)

## Quick Start

```python
# Navigate to page
browser(action="navigate", url="https://example.com")

# Click a button
browser(action="click", selector="button.submit")

# Fill a form
browser(action="fill", selector="input[name='email']", text="user@example.com")

# Take screenshot
browser(action="screenshot", full_page=True)
```

## Device Emulation

Built-in device presets for responsive testing:

```python
# User-friendly aliases
browser(action="emulate", device="mobile")   # iPhone-like (390x844)
browser(action="emulate", device="tablet")   # iPad-like (1024x1366)
browser(action="emulate", device="laptop")   # MacBook-like (1440x900)
browser(action="emulate", device="desktop")  # Full HD (1920x1080)

# Specific devices
browser(action="emulate", device="iphone_14")
browser(action="emulate", device="pixel_7")
browser(action="emulate", device="ipad_pro")
```

## Navigation

```python
# Basic navigation
browser(action="navigate", url="https://example.com")
browser(action="reload")
browser(action="go_back")
browser(action="go_forward")

# Get page info
browser(action="url")    # Current URL
browser(action="title")  # Page title
browser(action="content")  # HTML content
```

## Input Actions

```python
# Click variants
browser(action="click", selector="button")
browser(action="dblclick", selector=".item")
browser(action="right_click", selector=".context-menu")

# Text input
browser(action="type", selector="input", text="Hello", interval=0.1)
browser(action="fill", selector="input", text="Instant fill")
browser(action="clear", selector="input")

# Keyboard
browser(action="press", key="Enter")
browser(action="press", key="Control+c")
```

## Form Handling

```python
# Select dropdowns
browser(action="select_option", selector="select", value="option1")

# Checkboxes
browser(action="check", selector="input[type='checkbox']")
browser(action="uncheck", selector="input[type='checkbox']")

# File uploads
browser(action="upload", selector="input[type='file']", files=["./doc.pdf"])
```

## Mouse Control

```python
# Hover
browser(action="hover", selector=".menu-item")

# Drag and drop
browser(action="drag", selector=".draggable", target_selector=".dropzone")

# Scroll
browser(action="scroll", delta_y=500)
browser(action="scroll", selector=".container", delta_y=300)

# Mouse coordinates
browser(action="mouse_move", x=100, y=200)
browser(action="mouse_down")
browser(action="mouse_up")
```

## Touch & Mobile

```python
# Touch actions
browser(action="tap", selector="button")
browser(action="swipe", direction="up", distance=300)
browser(action="pinch", scale=0.5)  # Zoom out
browser(action="pinch", scale=2.0)  # Zoom in
```

## Locators

```python
# CSS/XPath
browser(action="locator", selector="div.class")
browser(action="locator", selector="//button[@id='submit']")

# Semantic locators
browser(action="get_by_role", role="button", name="Submit")
browser(action="get_by_text", text="Click me")
browser(action="get_by_label", text="Email")
browser(action="get_by_placeholder", text="Enter email")
browser(action="get_by_test_id", text="submit-btn")

# Composition
browser(action="first", selector=".items")
browser(action="last", selector=".items")
browser(action="nth", selector=".items", index=2)
browser(action="filter", selector=".items", has_text="Important")
```

## Assertions

```python
# Element assertions
browser(action="expect_visible", selector=".modal")
browser(action="expect_hidden", selector=".loading")
browser(action="expect_enabled", selector="button")
browser(action="expect_text", selector="h1", expected="Welcome")
browser(action="expect_count", selector=".items", index=5)

# Page assertions
browser(action="expect_url", expected="*/dashboard*")
browser(action="expect_title", expected="Dashboard")

# Negative assertions
browser(action="expect_visible", selector=".loading", not_=True)
```

## Content Extraction

```python
# Get text content
browser(action="get_text", selector="h1")
browser(action="get_inner_text", selector=".content")

# Get attributes
browser(action="get_attribute", selector="a", attribute="href")
browser(action="get_value", selector="input")

# Get HTML
browser(action="get_html", selector=".container")

# Get bounding box
browser(action="get_bounding_box", selector=".element")
```

## State Checking

```python
browser(action="is_visible", selector=".modal")
browser(action="is_hidden", selector=".loading")
browser(action="is_enabled", selector="button")
browser(action="is_editable", selector="input")
browser(action="is_checked", selector="input[type='checkbox']")
```

## Screenshots & PDFs

```python
# Screenshots
browser(action="screenshot")
browser(action="screenshot", full_page=True)
browser(action="screenshot", selector=".chart")

# PDF export
browser(action="pdf")
```

## Wait Operations

```python
# Wait for load states
browser(action="wait_for_load", state="networkidle")
browser(action="wait_for_url", url="*/success*")

# Wait for elements
browser(action="wait", selector=".loaded", state="visible")
browser(action="wait", timeout=5000)

# Wait for events
browser(action="wait_for_event", event="download")
browser(action="wait_for_response", pattern="*/api/*")
```

## Network Interception

```python
# Mock API responses
browser(
    action="route",
    pattern="*/api/users*",
    response={"users": [{"name": "Mock User"}]},
    status_code=200
)

# Block requests
browser(action="route", pattern="*.png", block=True)

# Remove route
browser(action="unroute", pattern="*/api/users*")
```

## Storage

```python
# Cookies
browser(action="cookies")
browser(action="cookies", cookies=[{"name": "token", "value": "abc"}])
browser(action="clear_cookies")

# Local/Session storage
browser(action="storage", storage_type="local")
browser(action="storage", storage_type="session", storage_data={"key": "value"})

# Save/restore auth state
browser(action="storage_state", auth_file="./auth.json")
```

## Tab Management

```python
# Multiple tabs
browser(action="new_tab", url="https://example.com")
browser(action="tabs")  # List all tabs
browser(action="close_tab", tab_index=1)
```

## Parallel Agents

For parallel execution, create isolated contexts:

```python
# Create new context (isolated cookies/storage)
browser(action="new_context")

# Each agent uses separate context
# One Chrome process, many parallel sessions
```

## Configuration

### Headless Mode

```python
# Toggle headless mode
browser(action="set_headless", headless=True)
browser(action="set_headless", headless=False)  # Show browser
```

### CDP Connection

Share browser instance across MCPs:

```bash
BROWSER_CDP_ENDPOINT=http://localhost:9222 hanzo-mcp
```

## Examples

### Login Flow

```python
# Navigate to login
browser(action="navigate", url="https://app.example.com/login")

# Fill credentials
browser(action="fill", selector="input[name='email']", text="user@example.com")
browser(action="fill", selector="input[name='password']", text="password123")

# Submit
browser(action="click", selector="button[type='submit']")

# Wait for redirect
browser(action="wait_for_url", url="*/dashboard*")

# Verify login
browser(action="expect_visible", selector=".user-menu")
```

### E2E Test

```python
# Test shopping cart
browser(action="navigate", url="https://shop.example.com")
browser(action="click", selector=".product-card:first-child button")
browser(action="expect_text", selector=".cart-count", expected="1")
browser(action="click", selector=".cart-icon")
browser(action="expect_visible", selector=".cart-modal")
browser(action="expect_text", selector=".total", expected="$99.00")
```

### Screenshot Comparison

```python
# Capture baseline
browser(action="navigate", url="https://example.com")
browser(action="screenshot", full_page=True)
# Returns base64 image for comparison
```
