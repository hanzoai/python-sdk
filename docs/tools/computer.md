# hanzo-tools-computer

Computer control via pyautogui for comprehensive Mac automation. Mouse, keyboard, screenshots, window management.

## Installation

```bash
pip install hanzo-tools-computer
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-computer` provides desktop automation:

- **Mouse** - click, drag, scroll, move
- **Keyboard** - type, press, hotkey
- **Screen** - screenshots, display info
- **Windows** - focus, list, get active
- **Image Location** - find UI elements
- **Regions** - named areas for targeting

## Quick Start

```python
# Click at coordinates
computer(action="click", x=100, y=200)

# Type text
computer(action="type", text="Hello, World!")

# Press keys
computer(action="press", key="enter")
computer(action="hotkey", keys=["command", "c"])

# Screenshot
computer(action="screenshot")

# Get screen info
computer(action="info")
```

## Actions Reference

### Mouse Actions

```python
# Click
computer(action="click", x=100, y=200)
computer(action="double_click", x=100, y=200)
computer(action="right_click", x=100, y=200)
computer(action="middle_click", x=100, y=200)

# Move
computer(action="move", x=100, y=200, duration=0.5)
computer(action="move_relative", dx=50, dy=-30)

# Drag
computer(action="drag", x=300, y=400, duration=0.5)
computer(action="drag_relative", dx=100, dy=0)

# Scroll
computer(action="scroll", amount=5)  # Scroll up
computer(action="scroll", amount=-5)  # Scroll down
computer(action="scroll", amount=3, x=500, y=300)  # At position
```

### Keyboard Actions

```python
# Type text (character by character)
computer(action="type", text="Hello!", interval=0.05)

# Write text (instant, can clear first)
computer(action="write", text="Instant text", clear=True)

# Press single key
computer(action="press", key="enter")
computer(action="press", key="tab")
computer(action="press", key="escape")

# Key combinations
computer(action="hotkey", keys=["command", "c"])  # Copy
computer(action="hotkey", keys=["command", "v"])  # Paste
computer(action="hotkey", keys=["command", "shift", "s"])  # Save as

# Hold/release keys
computer(action="key_down", key="shift")
computer(action="key_up", key="shift")
```

### Screen Actions

```python
# Full screenshot (returns base64)
computer(action="screenshot")

# Region screenshot
computer(action="screenshot_region", region=[100, 100, 500, 300])

# Get all displays
computer(action="get_screens")

# Get screen size
computer(action="screen_size")

# Current mouse position
computer(action="position")

# Full info
computer(action="info")
```

### Image Location

Find UI elements by image matching:

```python
# Find image on screen (returns center point)
computer(action="locate", image_path="button.png")

# Find all matches
computer(action="locate_all", image_path="icon.png")

# Get center point
computer(action="locate_center", image_path="submit.png")

# Wait for image to appear
computer(action="wait_for_image", image_path="loading.png", timeout=10)

# Wait while image is visible
computer(action="wait_while_image", image_path="spinner.png", timeout=30)
```

### Pixel Operations

```python
# Get pixel color at point
computer(action="pixel", x=100, y=200)

# Check if pixel matches color
computer(action="pixel_matches", x=100, y=200, color=[255, 0, 0], tolerance=10)
```

### Window Management

```python
# Get active window info
computer(action="get_active_window")

# List all windows
computer(action="list_windows")

# Focus window by title
computer(action="focus_window", title="Terminal")
computer(action="focus_window", title=".*Code.*", use_regex=True)
```

### Named Regions

Define reusable screen regions:

```python
# Define a region
computer(action="define_region", name="toolbar", x=0, y=0, width=1920, height=60)

# Screenshot region
computer(action="region_screenshot", name="toolbar")

# Locate image within region
computer(action="region_locate", name="toolbar", image_path="save_button.png")
```

### Timing & Flow

```python
# Sleep
computer(action="sleep", value=2.0)

# Countdown with output
computer(action="countdown", value=5)

# Set global pause between actions
computer(action="set_pause", value=0.2)

# Enable/disable fail-safe (corner abort)
computer(action="set_failsafe", value=True)
```

### Batch Operations

Execute multiple actions in sequence:

```python
computer(action="batch", actions=[
    {"action": "click", "x": 100, "y": 200},
    {"action": "type", "text": "Hello"},
    {"action": "press", "key": "enter"}
])
```

## Examples

### UI Automation

```python
# Click button and fill form
computer(action="click", x=500, y=300)  # Click form field
computer(action="write", text="user@example.com", clear=True)
computer(action="press", key="tab")
computer(action="write", text="password123")
computer(action="press", key="enter")
```

### Screenshot Workflow

```python
# Take screenshot, find element, click it
computer(action="screenshot")
result = computer(action="locate", image_path="login_button.png")
if result["found"]:
    computer(action="click", x=result["x"], y=result["y"])
```

### Window Management

```python
# Focus app and interact
computer(action="focus_window", title="Safari")
computer(action="hotkey", keys=["command", "l"])  # Focus URL bar
computer(action="write", text="https://example.com", clear=True)
computer(action="press", key="enter")
```

### Wait for UI State

```python
# Wait for loading to finish
computer(action="wait_while_image", image_path="spinner.png", timeout=30)

# Then continue
computer(action="click", x=500, y=400)
```

## Performance Features

- **Lazy loading** - pyautogui loads on first use (150ms+ startup savings)
- **Cached screen info** - Display info cached for 5 seconds
- **Thread pool executor** - All blocking operations run in threads
- **Batch operations** - Multiple actions in single call

## Fail-Safe

By default, moving the mouse to any corner of the screen will raise an exception, allowing you to abort automation. Disable with:

```python
computer(action="set_failsafe", value=False)
```

## Best Practices

1. **Use image location over coordinates** - More robust across resolutions
2. **Add waits for UI transitions** - Use `wait_for_image` after actions
3. **Define named regions** - Improves code readability
4. **Enable fail-safe** - Keep the corner abort enabled during development
5. **Use batch for sequences** - More efficient than individual calls
