"""Computer control tool using pyautogui for Mac automation.

Provides unified control over mouse, keyboard, and screen capture.
All operations run in executor threads to avoid blocking the event loop.
"""

import asyncio
import base64
import io
import sys
from typing import Annotated, Literal, final, override
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, PermissionManager, auto_timeout


# Action types
Action = Literal[
    # Mouse actions
    "click",
    "double_click",
    "right_click",
    "move",
    "drag",
    "scroll",
    # Keyboard actions
    "type",
    "press",
    "hotkey",
    # Screen actions
    "screenshot",
    "locate",
    # Info
    "info",
]


@final
class ComputerTool(BaseTool):
    """Control local computer via pyautogui.

    Supports mouse control, keyboard input, and screen capture for
    automating local Mac workflows.
    """

    name = "computer"

    def __init__(self, permission_manager: PermissionManager):
        """Initialize the computer tool.

        Args:
            permission_manager: Permission manager for access control
        """
        self.permission_manager = permission_manager
        self._pyautogui = None
        self._pil = None

    def _ensure_pyautogui(self):
        """Lazy load pyautogui to avoid startup cost."""
        if self._pyautogui is None:
            import pyautogui

            # Safety settings
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            pyautogui.PAUSE = 0.1  # Small delay between actions
            self._pyautogui = pyautogui
        return self._pyautogui

    def _ensure_pil(self):
        """Lazy load PIL."""
        if self._pil is None:
            from PIL import Image

            self._pil = Image
        return self._pil

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Control local computer via pyautogui for Mac automation.

Actions:
- Mouse: click, double_click, right_click, move, drag, scroll
- Keyboard: type (text), press (key), hotkey (shortcuts)
- Screen: screenshot, locate (find image on screen), info

Examples:
    # Click at coordinates
    computer(action="click", x=100, y=200)
    
    # Type text
    computer(action="type", text="Hello world")
    
    # Press key
    computer(action="press", key="enter")
    
    # Keyboard shortcut
    computer(action="hotkey", keys=["command", "c"])
    
    # Take screenshot
    computer(action="screenshot")
    
    # Get screen info
    computer(action="info")

Args:
    action: The action to perform
    x, y: Coordinates for mouse actions
    text: Text for type action
    key: Key name for press action
    keys: List of keys for hotkey action
    amount: Scroll amount (positive=up, negative=down)
    duration: Duration for smooth mouse movements
    region: Screenshot region as [x, y, width, height]

Returns:
    Action result or error message
"""

    @override
    @auto_timeout("computer")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "info",
        x: int | None = None,
        y: int | None = None,
        text: str | None = None,
        key: str | None = None,
        keys: list[str] | None = None,
        amount: int | None = None,
        duration: float = 0.25,
        region: list[int] | None = None,
        **kwargs,
    ) -> str:
        """Execute computer control action."""
        # Check platform
        if sys.platform != "darwin":
            return f"Error: computer tool only supports macOS, got {sys.platform}"

        loop = asyncio.get_event_loop()

        try:
            if action == "info":
                return await loop.run_in_executor(None, self._get_info)

            elif action == "click":
                if x is None or y is None:
                    return "Error: click requires x and y coordinates"
                return await loop.run_in_executor(None, self._click, x, y)

            elif action == "double_click":
                if x is None or y is None:
                    return "Error: double_click requires x and y coordinates"
                return await loop.run_in_executor(None, self._double_click, x, y)

            elif action == "right_click":
                if x is None or y is None:
                    return "Error: right_click requires x and y coordinates"
                return await loop.run_in_executor(None, self._right_click, x, y)

            elif action == "move":
                if x is None or y is None:
                    return "Error: move requires x and y coordinates"
                return await loop.run_in_executor(None, self._move, x, y, duration)

            elif action == "drag":
                if x is None or y is None:
                    return "Error: drag requires x and y coordinates"
                return await loop.run_in_executor(None, self._drag, x, y, duration)

            elif action == "scroll":
                if amount is None:
                    return "Error: scroll requires amount"
                return await loop.run_in_executor(None, self._scroll, amount, x, y)

            elif action == "type":
                if not text:
                    return "Error: type requires text"
                return await loop.run_in_executor(None, self._type_text, text)

            elif action == "press":
                if not key:
                    return "Error: press requires key"
                return await loop.run_in_executor(None, self._press_key, key)

            elif action == "hotkey":
                if not keys:
                    return "Error: hotkey requires keys list"
                return await loop.run_in_executor(None, self._hotkey, keys)

            elif action == "screenshot":
                return await loop.run_in_executor(None, self._screenshot, region)

            elif action == "locate":
                if not text:  # text is used as image path for locate
                    return "Error: locate requires image path in text parameter"
                return await loop.run_in_executor(None, self._locate, text)

            else:
                return f"Error: Unknown action '{action}'. Valid: click, double_click, right_click, move, drag, scroll, type, press, hotkey, screenshot, locate, info"

        except Exception as e:
            return f"Error: {str(e)}"

    def _get_info(self) -> str:
        """Get screen and mouse info."""
        pg = self._ensure_pyautogui()
        size = pg.size()
        pos = pg.position()
        return f"Screen: {size.width}x{size.height}\nMouse: ({pos.x}, {pos.y})"

    def _click(self, x: int, y: int) -> str:
        """Click at coordinates."""
        pg = self._ensure_pyautogui()
        pg.click(x, y)
        return f"Clicked at ({x}, {y})"

    def _double_click(self, x: int, y: int) -> str:
        """Double click at coordinates."""
        pg = self._ensure_pyautogui()
        pg.doubleClick(x, y)
        return f"Double clicked at ({x}, {y})"

    def _right_click(self, x: int, y: int) -> str:
        """Right click at coordinates."""
        pg = self._ensure_pyautogui()
        pg.rightClick(x, y)
        return f"Right clicked at ({x}, {y})"

    def _move(self, x: int, y: int, duration: float) -> str:
        """Move mouse to coordinates."""
        pg = self._ensure_pyautogui()
        pg.moveTo(x, y, duration=duration)
        return f"Moved to ({x}, {y})"

    def _drag(self, x: int, y: int, duration: float) -> str:
        """Drag to coordinates."""
        pg = self._ensure_pyautogui()
        pg.dragTo(x, y, duration=duration)
        return f"Dragged to ({x}, {y})"

    def _scroll(self, amount: int, x: int | None, y: int | None) -> str:
        """Scroll at optional position."""
        pg = self._ensure_pyautogui()
        if x is not None and y is not None:
            pg.scroll(amount, x=x, y=y)
            return f"Scrolled {amount} at ({x}, {y})"
        else:
            pg.scroll(amount)
            return f"Scrolled {amount}"

    def _type_text(self, text: str) -> str:
        """Type text."""
        pg = self._ensure_pyautogui()
        pg.typewrite(text, interval=0.02)
        return f"Typed {len(text)} characters"

    def _press_key(self, key: str) -> str:
        """Press a key."""
        pg = self._ensure_pyautogui()
        pg.press(key)
        return f"Pressed '{key}'"

    def _hotkey(self, keys: list[str]) -> str:
        """Press hotkey combination."""
        pg = self._ensure_pyautogui()
        pg.hotkey(*keys)
        return f"Pressed hotkey: {'+'.join(keys)}"

    def _screenshot(self, region: list[int] | None) -> str:
        """Take screenshot, return as base64."""
        pg = self._ensure_pyautogui()
        Image = self._ensure_pil()

        if region and len(region) == 4:
            screenshot = pg.screenshot(region=tuple(region))
        else:
            screenshot = pg.screenshot()

        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"Screenshot captured ({screenshot.width}x{screenshot.height})\ndata:image/png;base64,{img_data[:100]}...[truncated]"

    def _locate(self, image_path: str) -> str:
        """Locate image on screen."""
        pg = self._ensure_pyautogui()

        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        try:
            location = pg.locateOnScreen(str(path))
            if location:
                center = pg.center(location)
                return f"Found at: ({center.x}, {center.y})\nBox: {location}"
            else:
                return "Image not found on screen"
        except Exception as e:
            return f"Error locating image: {str(e)}"

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def computer(
            action: Annotated[str, Field(description="Action to perform")] = "info",
            x: Annotated[int | None, Field(description="X coordinate")] = None,
            y: Annotated[int | None, Field(description="Y coordinate")] = None,
            text: Annotated[str | None, Field(description="Text for type action")] = None,
            key: Annotated[str | None, Field(description="Key for press action")] = None,
            keys: Annotated[list[str] | None, Field(description="Keys for hotkey")] = None,
            amount: Annotated[int | None, Field(description="Scroll amount")] = None,
            duration: Annotated[float, Field(description="Movement duration")] = 0.25,
            region: Annotated[list[int] | None, Field(description="Screenshot region")] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                x=x,
                y=y,
                text=text,
                key=key,
                keys=keys,
                amount=amount,
                duration=duration,
                region=region,
            )
