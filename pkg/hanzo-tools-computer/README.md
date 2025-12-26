# hanzo-tools-computer

Computer control tools for Hanzo AI - pyautogui-based Mac automation.

## Installation

```bash
pip install hanzo-tools-computer
```

## Usage

```python
from hanzo_tools.computer import ComputerTool, register_tools

# Register with MCP server
register_tools(mcp_server, permission_manager)
```

## Actions

### Mouse
- `click` - Click at (x, y)
- `double_click` - Double click at (x, y)
- `right_click` - Right click at (x, y)
- `move` - Move mouse to (x, y)
- `drag` - Drag to (x, y)
- `scroll` - Scroll by amount

### Keyboard
- `type` - Type text string
- `press` - Press single key
- `hotkey` - Press key combination

### Screen
- `screenshot` - Capture screen
- `locate` - Find image on screen
- `info` - Get screen/mouse info

## Examples

```python
# Click at coordinates
computer(action="click", x=100, y=200)

# Type text
computer(action="type", text="Hello world")

# Keyboard shortcut (Cmd+C on Mac)
computer(action="hotkey", keys=["command", "c"])

# Take screenshot
computer(action="screenshot")

# Get screen info
computer(action="info")
```

## Safety

- FAILSAFE enabled: Move mouse to corner to abort
- macOS only (checks platform)
- All actions run in executor threads (non-blocking)

## License

MIT
