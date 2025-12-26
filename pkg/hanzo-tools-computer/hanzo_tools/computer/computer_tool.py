"""Computer control tool using pyautogui for Mac automation.

Provides unified control over mouse, keyboard, screen capture, window management,
and image location. All operations run in executor threads to avoid blocking.

Performance optimizations:
- Lazy loading of pyautogui/PIL (150ms+ startup savings)
- Cached screen size and display info
- Thread pool executor for all blocking operations
- Batch operations for multiple actions
- Async-first design with no blocking in event loop
"""

import asyncio
import base64
import functools
import io
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core import BaseTool, PermissionManager, auto_timeout

# Shared thread pool for blocking operations (faster than run_in_executor default)
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="computer_")


# All supported actions
Action = Literal[
    # Mouse actions
    "click", "double_click", "right_click", "middle_click",
    "move", "move_relative", "drag", "drag_relative", "scroll",
    # Keyboard actions
    "type", "write", "press", "key_down", "key_up", "hotkey",
    # Screen actions
    "screenshot", "screenshot_region",
    # Image location
    "locate", "locate_all", "locate_center", "wait_for_image", "wait_while_image",
    # Pixel operations
    "pixel", "pixel_matches",
    # Window management
    "get_active_window", "list_windows", "focus_window",
    # Screen management
    "get_screens", "screen_size", "current_screen",
    # Region helpers
    "define_region", "region_screenshot", "region_locate",
    # Timing/flow
    "sleep", "countdown", "set_pause", "set_failsafe",
    # Batch operations
    "batch",
    # Info
    "info", "position",
]


@final
class ComputerTool(BaseTool):
    """Control local computer via pyautogui.

    Comprehensive Mac automation supporting mouse, keyboard, screen capture,
    window management, image location, and timing controls.
    """

    name = "computer"

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """Initialize the computer tool.

        Args:
            permission_manager: Permission manager for access control (auto-created if None)
        """
        if permission_manager is None:
            permission_manager = PermissionManager()
        self.permission_manager = permission_manager
        self._pyautogui = None
        self._pil = None
        self._defined_regions: dict[str, tuple[int, int, int, int]] = {}
        self._pause = 0.1
        self._failsafe = True
        # Caches
        self._screen_size_cache: tuple[int, int] | None = None
        self._screen_size_time: float = 0
        self._displays_cache: str | None = None
        self._displays_time: float = 0
        self._CACHE_TTL = 5.0  # Cache for 5 seconds

    def _ensure_pyautogui(self):
        """Lazy load pyautogui to avoid startup cost."""
        if self._pyautogui is None:
            import pyautogui

            pyautogui.FAILSAFE = self._failsafe
            pyautogui.PAUSE = self._pause
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
        return """Control local computer via pyautogui for comprehensive Mac automation.

Actions:

MOUSE:
- click(x, y) / double_click / right_click / middle_click
- move(x, y, duration) / move_relative(dx, dy)
- drag(x, y, duration) / drag_relative(dx, dy)
- scroll(amount, x, y)

KEYBOARD:
- type(text, interval): Type text character by character
- write(text, clear): Type text, optionally clear first
- press(key): Press and release a key
- key_down(key) / key_up(key): Hold/release modifier
- hotkey(keys): Press key combination like ["command", "c"]

SCREEN:
- screenshot() / screenshot_region(region)
- get_screens(): List all displays
- screen_size() / current_screen()

IMAGE LOCATION:
- locate(image_path): Find image on screen, return center
- locate_all(image_path): Find all matches
- locate_center(image_path): Return just center point
- wait_for_image(image_path, timeout): Wait until image appears
- wait_while_image(image_path, timeout): Wait while image visible

PIXEL:
- pixel(x, y): Get pixel color at point
- pixel_matches(x, y, color, tolerance): Check if pixel matches

WINDOWS:
- get_active_window(): Get frontmost window info
- list_windows(): List all windows with bounds
- focus_window(title, regex): Bring window to front

REGIONS:
- define_region(name, x, y, w, h): Name a region for reuse
- region_screenshot(name): Screenshot named region
- region_locate(name, image): Find image in named region

TIMING:
- sleep(seconds)
- countdown(seconds): Sleep with countdown output
- set_pause(seconds): Set global pause between actions
- set_failsafe(enabled): Enable/disable corner abort

INFO:
- info(): Screen size and mouse position
- position(): Current mouse position

Examples:
    computer(action="click", x=100, y=200)
    computer(action="write", text="Hello", clear=True)
    computer(action="hotkey", keys=["command", "v"])
    computer(action="wait_for_image", image_path="button.png", timeout=10)
    computer(action="focus_window", title="Terminal")
    computer(action="define_region", name="toolbar", x=0, y=0, width=1920, height=60)
    computer(action="set_pause", value=0.2)
"""

    @override
    @auto_timeout("computer")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "info",
        # Coordinates
        x: int | None = None,
        y: int | None = None,
        dx: int | None = None,
        dy: int | None = None,
        # Text/keys
        text: str | None = None,
        key: str | None = None,
        keys: list[str] | None = None,
        # Options
        amount: int | None = None,
        duration: float = 0.25,
        interval: float = 0.02,
        region: list[int] | None = None,
        clear: bool = False,
        # Image location
        image_path: str | None = None,
        confidence: float = 0.9,
        timeout: float = 10.0,
        # Pixel matching
        color: tuple[int, int, int] | list[int] | None = None,
        tolerance: int = 0,
        # Window
        title: str | None = None,
        use_regex: bool = False,
        # Regions
        name: str | None = None,
        width: int | None = None,
        height: int | None = None,
        # Settings
        value: float | bool | None = None,
        # Batch operations
        actions: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> str:
        """Execute computer control action."""
        # Check platform
        if sys.platform != "darwin":
            return f"Error: computer tool only supports macOS, got {sys.platform}"

        loop = asyncio.get_event_loop()

        # Helper for running in thread pool
        def run(fn, *args):
            return loop.run_in_executor(_EXECUTOR, fn, *args)

        try:
            # Mouse actions
            if action == "click":
                if x is None or y is None:
                    return "Error: click requires x and y coordinates"
                return await run(self._click, x, y, "left")

            elif action == "double_click":
                if x is None or y is None:
                    return "Error: double_click requires x and y coordinates"
                return await run(self._double_click, x, y)

            elif action == "right_click":
                if x is None or y is None:
                    return "Error: right_click requires x and y coordinates"
                return await run(self._click, x, y, "right")

            elif action == "middle_click":
                if x is None or y is None:
                    return "Error: middle_click requires x and y coordinates"
                return await run(self._click, x, y, "middle")

            elif action == "move":
                if x is None or y is None:
                    return "Error: move requires x and y coordinates"
                return await run(self._move, x, y, duration)

            elif action == "move_relative":
                if dx is None or dy is None:
                    return "Error: move_relative requires dx and dy"
                return await run(self._move_relative, dx, dy, duration)

            elif action == "drag":
                if x is None or y is None:
                    return "Error: drag requires x and y coordinates"
                return await run(self._drag, x, y, duration)

            elif action == "drag_relative":
                if dx is None or dy is None:
                    return "Error: drag_relative requires dx and dy"
                return await run(self._drag_relative, dx, dy, duration)

            elif action == "scroll":
                if amount is None:
                    return "Error: scroll requires amount"
                return await run(self._scroll, amount, x, y)

            # Keyboard actions
            elif action == "type":
                if not text:
                    return "Error: type requires text"
                return await run(self._type_text, text, interval)

            elif action == "write":
                if not text:
                    return "Error: write requires text"
                return await run(self._write_text, text, clear, interval)

            elif action == "press":
                if not key:
                    return "Error: press requires key"
                return await run(self._press_key, key)

            elif action == "key_down":
                if not key:
                    return "Error: key_down requires key"
                return await run(self._key_down, key)

            elif action == "key_up":
                if not key:
                    return "Error: key_up requires key"
                return await run(self._key_up, key)

            elif action == "hotkey":
                if not keys:
                    return "Error: hotkey requires keys list"
                return await run(self._hotkey, keys)

            # Screen actions
            elif action == "screenshot":
                return await run(self._screenshot, None)

            elif action == "screenshot_region":
                if region is None:
                    return "Error: screenshot_region requires region [x, y, width, height]"
                return await run(self._screenshot, region)

            # Image location
            elif action == "locate":
                if not image_path and not text:
                    return "Error: locate requires image_path"
                path = image_path or text
                return await run(self._locate, path, confidence, None)

            elif action == "locate_all":
                if not image_path and not text:
                    return "Error: locate_all requires image_path"
                path = image_path or text
                return await run(self._locate_all, path, confidence)

            elif action == "locate_center":
                if not image_path and not text:
                    return "Error: locate_center requires image_path"
                path = image_path or text
                return await run(self._locate_center, path, confidence)

            elif action == "wait_for_image":
                if not image_path and not text:
                    return "Error: wait_for_image requires image_path"
                path = image_path or text
                return await self._wait_for_image(path, timeout, confidence, run)

            elif action == "wait_while_image":
                if not image_path and not text:
                    return "Error: wait_while_image requires image_path"
                path = image_path or text
                return await self._wait_while_image(path, timeout, confidence, run)

            # Pixel operations
            elif action == "pixel":
                if x is None or y is None:
                    return "Error: pixel requires x and y coordinates"
                return await run(self._get_pixel, x, y)

            elif action == "pixel_matches":
                if x is None or y is None:
                    return "Error: pixel_matches requires x and y coordinates"
                if color is None:
                    return "Error: pixel_matches requires color (RGB tuple)"
                return await run(self._pixel_matches, x, y, tuple(color), tolerance)

            # Window management
            elif action == "get_active_window":
                return await run(self._get_active_window)

            elif action == "list_windows":
                return await run(self._list_windows)

            elif action == "focus_window":
                if not title and not text:
                    return "Error: focus_window requires title"
                win_title = title or text
                return await run(self._focus_window, win_title, use_regex)

            # Screen management
            elif action == "get_screens":
                return await run(self._get_screens_cached)

            elif action == "screen_size":
                return await run(self._screen_size_cached)

            elif action == "current_screen":
                return await run(self._current_screen)

            # Region helpers
            elif action == "define_region":
                if not name:
                    return "Error: define_region requires name"
                if x is None or y is None or width is None or height is None:
                    return "Error: define_region requires x, y, width, height"
                self._defined_regions[name] = (x, y, width, height)
                return f"Defined region '{name}': ({x}, {y}, {width}, {height})"

            elif action == "region_screenshot":
                if not name:
                    return "Error: region_screenshot requires region name"
                if name not in self._defined_regions:
                    return f"Error: Region '{name}' not defined"
                reg = list(self._defined_regions[name])
                return await run(self._screenshot, reg)

            elif action == "region_locate":
                if not name:
                    return "Error: region_locate requires region name"
                if not image_path and not text:
                    return "Error: region_locate requires image_path"
                if name not in self._defined_regions:
                    return f"Error: Region '{name}' not defined"
                path = image_path or text
                reg = self._defined_regions[name]
                return await run(self._locate, path, confidence, reg)

            # Timing/flow
            elif action == "sleep":
                if value is None:
                    return "Error: sleep requires value (seconds)"
                await asyncio.sleep(float(value))
                return f"Slept for {value} seconds"

            elif action == "countdown":
                if value is None:
                    return "Error: countdown requires value (seconds)"
                return await self._countdown(int(value))

            elif action == "set_pause":
                if value is None:
                    return "Error: set_pause requires value (seconds)"
                self._pause = float(value)
                if self._pyautogui:
                    self._pyautogui.PAUSE = self._pause
                return f"Set global pause to {self._pause}s"

            elif action == "set_failsafe":
                if value is None:
                    return "Error: set_failsafe requires value (true/false)"
                self._failsafe = bool(value)
                if self._pyautogui:
                    self._pyautogui.FAILSAFE = self._failsafe
                return f"Failsafe {'enabled' if self._failsafe else 'disabled'}"

            # Info
            elif action == "info":
                return await run(self._get_info)

            elif action == "position":
                return await run(self._get_position)

            # Batch operations - run multiple actions in one call
            elif action == "batch":
                if not actions:
                    return "Error: batch requires actions list"
                return await self._run_batch(actions, run)

            else:
                return f"Error: Unknown action '{action}'"

        except Exception as e:
            return f"Error: {str(e)}"

    # ========== Mouse Methods ==========

    def _click(self, x: int, y: int, button: str = "left") -> str:
        pg = self._ensure_pyautogui()
        pg.click(x, y, button=button)
        return f"Clicked {button} at ({x}, {y})"

    def _double_click(self, x: int, y: int) -> str:
        pg = self._ensure_pyautogui()
        pg.doubleClick(x, y)
        return f"Double clicked at ({x}, {y})"

    def _move(self, x: int, y: int, duration: float) -> str:
        pg = self._ensure_pyautogui()
        pg.moveTo(x, y, duration=duration)
        return f"Moved to ({x}, {y})"

    def _move_relative(self, dx: int, dy: int, duration: float) -> str:
        pg = self._ensure_pyautogui()
        pg.moveRel(dx, dy, duration=duration)
        pos = pg.position()
        return f"Moved by ({dx}, {dy}) to ({pos.x}, {pos.y})"

    def _drag(self, x: int, y: int, duration: float) -> str:
        pg = self._ensure_pyautogui()
        pg.dragTo(x, y, duration=duration)
        return f"Dragged to ({x}, {y})"

    def _drag_relative(self, dx: int, dy: int, duration: float) -> str:
        pg = self._ensure_pyautogui()
        pg.dragRel(dx, dy, duration=duration)
        pos = pg.position()
        return f"Dragged by ({dx}, {dy}) to ({pos.x}, {pos.y})"

    def _scroll(self, amount: int, x: int | None, y: int | None) -> str:
        pg = self._ensure_pyautogui()
        if x is not None and y is not None:
            pg.scroll(amount, x=x, y=y)
            return f"Scrolled {amount} at ({x}, {y})"
        else:
            pg.scroll(amount)
            return f"Scrolled {amount}"

    # ========== Keyboard Methods ==========

    def _type_text(self, text: str, interval: float) -> str:
        pg = self._ensure_pyautogui()
        pg.typewrite(text, interval=interval)
        return f"Typed {len(text)} characters"

    def _write_text(self, text: str, clear: bool, interval: float) -> str:
        pg = self._ensure_pyautogui()
        if clear:
            pg.hotkey("command", "a")
            time.sleep(0.05)
        pg.write(text, interval=interval)
        return f"Wrote {len(text)} characters" + (" (cleared first)" if clear else "")

    def _press_key(self, key: str) -> str:
        pg = self._ensure_pyautogui()
        pg.press(key)
        return f"Pressed '{key}'"

    def _key_down(self, key: str) -> str:
        pg = self._ensure_pyautogui()
        pg.keyDown(key)
        return f"Key down: '{key}'"

    def _key_up(self, key: str) -> str:
        pg = self._ensure_pyautogui()
        pg.keyUp(key)
        return f"Key up: '{key}'"

    def _hotkey(self, keys: list[str]) -> str:
        pg = self._ensure_pyautogui()
        pg.hotkey(*keys)
        return f"Pressed hotkey: {'+'.join(keys)}"

    # ========== Screen Methods ==========

    def _screenshot(self, region: list[int] | None) -> str:
        pg = self._ensure_pyautogui()
        self._ensure_pil()

        if region and len(region) == 4:
            screenshot = pg.screenshot(region=tuple(region))
        else:
            screenshot = pg.screenshot()

        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"Screenshot captured ({screenshot.width}x{screenshot.height})\ndata:image/png;base64,{img_data[:100]}...[truncated]"

    def _get_screens(self) -> str:
        """Get all display info using AppKit."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                displays = []
                for gpu in data.get("SPDisplaysDataType", []):
                    for disp in gpu.get("spdisplays_ndrvs", []):
                        displays.append({
                            "name": disp.get("_name", "Unknown"),
                            "resolution": disp.get("_spdisplays_resolution", "Unknown"),
                            "main": disp.get("spdisplays_main") == "spdisplays_yes",
                        })
                return json.dumps(displays, indent=2)
        except Exception as e:
            pass

        pg = self._ensure_pyautogui()
        size = pg.size()
        return json.dumps([{"name": "Primary", "resolution": f"{size.width}x{size.height}", "main": True}])

    def _screen_size(self) -> str:
        pg = self._ensure_pyautogui()
        size = pg.size()
        return f"{size.width}x{size.height}"

    def _screen_size_cached(self) -> str:
        """Cached screen size (5 second TTL)."""
        now = time.time()
        if self._screen_size_cache and (now - self._screen_size_time) < self._CACHE_TTL:
            return f"{self._screen_size_cache[0]}x{self._screen_size_cache[1]}"
        pg = self._ensure_pyautogui()
        size = pg.size()
        self._screen_size_cache = (size.width, size.height)
        self._screen_size_time = now
        return f"{size.width}x{size.height}"

    def _get_screens_cached(self) -> str:
        """Cached screen list (5 second TTL)."""
        now = time.time()
        if self._displays_cache and (now - self._displays_time) < self._CACHE_TTL:
            return self._displays_cache
        result = self._get_screens()
        self._displays_cache = result
        self._displays_time = now
        return result

    def _current_screen(self) -> str:
        pg = self._ensure_pyautogui()
        pos = pg.position()
        size = pg.size()
        return json.dumps({
            "size": {"width": size.width, "height": size.height},
            "mouse": {"x": pos.x, "y": pos.y},
        })

    # ========== Image Location Methods ==========

    def _locate(
        self, image_path: str, confidence: float, region: tuple | None
    ) -> str:
        pg = self._ensure_pyautogui()
        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        try:
            kwargs: dict[str, Any] = {}
            if confidence < 1.0:
                kwargs["confidence"] = confidence
            if region:
                kwargs["region"] = region

            location = pg.locateOnScreen(str(path), **kwargs)
            if location:
                center = pg.center(location)
                return json.dumps({
                    "found": True,
                    "center": {"x": center.x, "y": center.y},
                    "box": {"left": location.left, "top": location.top,
                           "width": location.width, "height": location.height},
                })
            else:
                return json.dumps({"found": False, "message": "Image not found on screen"})
        except Exception as e:
            return f"Error locating image: {str(e)}"

    def _locate_all(self, image_path: str, confidence: float) -> str:
        pg = self._ensure_pyautogui()
        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        try:
            kwargs: dict[str, Any] = {}
            if confidence < 1.0:
                kwargs["confidence"] = confidence

            locations = list(pg.locateAllOnScreen(str(path), **kwargs))
            results = []
            for loc in locations:
                center = pg.center(loc)
                results.append({
                    "center": {"x": center.x, "y": center.y},
                    "box": {"left": loc.left, "top": loc.top,
                           "width": loc.width, "height": loc.height},
                })
            return json.dumps({"found": len(results), "locations": results})
        except Exception as e:
            return f"Error locating images: {str(e)}"

    def _locate_center(self, image_path: str, confidence: float) -> str:
        pg = self._ensure_pyautogui()
        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        try:
            kwargs: dict[str, Any] = {}
            if confidence < 1.0:
                kwargs["confidence"] = confidence

            center = pg.locateCenterOnScreen(str(path), **kwargs)
            if center:
                return json.dumps({"found": True, "x": center.x, "y": center.y})
            else:
                return json.dumps({"found": False})
        except Exception as e:
            return f"Error: {str(e)}"

    async def _wait_for_image(
        self, image_path: str, timeout: float, confidence: float, run
    ) -> str:
        """Wait until image appears on screen."""
        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        start = time.time()
        while time.time() - start < timeout:
            result = await run(self._locate_center, str(path), confidence)
            data = json.loads(result) if result.startswith("{") else {}
            if data.get("found"):
                elapsed = time.time() - start
                return json.dumps({
                    "found": True,
                    "x": data["x"],
                    "y": data["y"],
                    "elapsed": round(elapsed, 2),
                })
            await asyncio.sleep(0.1)  # Faster polling

        return json.dumps({"found": False, "timeout": timeout})

    async def _wait_while_image(
        self, image_path: str, timeout: float, confidence: float, run
    ) -> str:
        """Wait while image is visible on screen."""
        path = Path(image_path)
        if not path.exists():
            return f"Error: Image not found: {image_path}"

        start = time.time()
        while time.time() - start < timeout:
            result = await run(self._locate_center, str(path), confidence)
            data = json.loads(result) if result.startswith("{") else {}
            if not data.get("found"):
                elapsed = time.time() - start
                return json.dumps({"disappeared": True, "elapsed": round(elapsed, 2)})
            await asyncio.sleep(0.1)  # Faster polling

        return json.dumps({"disappeared": False, "timeout": timeout, "still_visible": True})

    # ========== Pixel Methods ==========

    def _get_pixel(self, x: int, y: int) -> str:
        pg = self._ensure_pyautogui()
        try:
            screenshot = pg.screenshot(region=(x, y, 1, 1))
            pixel = screenshot.getpixel((0, 0))
            return json.dumps({"x": x, "y": y, "color": {"r": pixel[0], "g": pixel[1], "b": pixel[2]}})
        except Exception as e:
            return f"Error: {str(e)}"

    def _pixel_matches(
        self, x: int, y: int, color: tuple[int, int, int], tolerance: int
    ) -> str:
        pg = self._ensure_pyautogui()
        try:
            screenshot = pg.screenshot(region=(x, y, 1, 1))
            pixel = screenshot.getpixel((0, 0))
            matches = all(
                abs(pixel[i] - color[i]) <= tolerance for i in range(3)
            )
            return json.dumps({
                "matches": matches,
                "expected": {"r": color[0], "g": color[1], "b": color[2]},
                "actual": {"r": pixel[0], "g": pixel[1], "b": pixel[2]},
                "tolerance": tolerance,
            })
        except Exception as e:
            return f"Error: {str(e)}"

    # ========== Window Management Methods ==========

    def _get_active_window(self) -> str:
        """Get frontmost window info using AppleScript."""
        try:
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                try
                    set frontWindow to front window of frontApp
                    set winName to name of frontWindow
                    set winPos to position of frontWindow
                    set winSize to size of frontWindow
                    return appName & "|||" & winName & "|||" & (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "|||" & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
                on error
                    return appName & "|||" & "" & "|||0,0|||0,0"
                end try
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split("|||")
                if len(parts) >= 4:
                    pos = parts[2].split(",")
                    size = parts[3].split(",")
                    return json.dumps({
                        "app": parts[0],
                        "title": parts[1],
                        "position": {"x": int(pos[0]), "y": int(pos[1])},
                        "size": {"width": int(size[0]), "height": int(size[1])},
                    })
            return json.dumps({"error": "Could not get active window"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _list_windows(self) -> str:
        """List all windows using AppleScript."""
        try:
            script = '''
            set windowList to ""
            tell application "System Events"
                set allProcesses to application processes whose visible is true
                repeat with proc in allProcesses
                    set procName to name of proc
                    try
                        set procWindows to windows of proc
                        repeat with win in procWindows
                            set winName to name of win
                            set winPos to position of win
                            set winSize to size of win
                            set windowList to windowList & procName & "|||" & winName & "|||" & (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "|||" & (item 1 of winSize as string) & "," & (item 2 of winSize as string) & "\\n"
                        end repeat
                    end try
                end repeat
            end tell
            return windowList
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                windows = []
                for line in result.stdout.strip().split("\n"):
                    if "|||" in line:
                        parts = line.split("|||")
                        if len(parts) >= 4:
                            pos = parts[2].split(",")
                            size = parts[3].split(",")
                            windows.append({
                                "app": parts[0],
                                "title": parts[1],
                                "position": {"x": int(pos[0]), "y": int(pos[1])},
                                "size": {"width": int(size[0]), "height": int(size[1])},
                            })
                return json.dumps({"windows": windows, "count": len(windows)})
            return json.dumps({"error": "Could not list windows", "windows": []})
        except Exception as e:
            return json.dumps({"error": str(e), "windows": []})

    def _focus_window(self, title: str, use_regex: bool) -> str:
        """Focus a window by title."""
        try:
            if use_regex:
                # First list windows and find match
                windows_json = self._list_windows()
                windows_data = json.loads(windows_json)
                pattern = re.compile(title)
                for win in windows_data.get("windows", []):
                    if pattern.search(win.get("title", "")) or pattern.search(win.get("app", "")):
                        title = win.get("app")
                        break

            script = f'''
            tell application "{title}"
                activate
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return json.dumps({"focused": True, "title": title})
            return json.dumps({"focused": False, "error": result.stderr})
        except Exception as e:
            return json.dumps({"focused": False, "error": str(e)})

    # ========== Timing Methods ==========

    async def _countdown(self, seconds: int) -> str:
        """Countdown with output."""
        for i in range(seconds, 0, -1):
            await asyncio.sleep(1)
        return f"Countdown complete ({seconds}s)"

    async def _run_batch(self, actions: list[dict[str, Any]], run) -> str:
        """Run multiple actions in sequence, returning all results.

        Example:
            computer(action="batch", actions=[
                {"action": "move", "x": 100, "y": 200},
                {"action": "click", "x": 100, "y": 200},
                {"action": "type", "text": "hello"},
            ])
        """
        results = []
        for i, action_spec in enumerate(actions):
            if not isinstance(action_spec, dict):
                results.append({"index": i, "error": "Invalid action spec"})
                continue

            action = action_spec.get("action", "")
            if not action:
                results.append({"index": i, "error": "Missing action"})
                continue

            # Build kwargs from action spec
            kwargs = {k: v for k, v in action_spec.items() if k != "action"}

            # Execute action using the appropriate method
            try:
                result = await self._execute_single_action(action, kwargs, run)
                results.append({"index": i, "action": action, "result": result})
            except Exception as e:
                results.append({"index": i, "action": action, "error": str(e)})

        return json.dumps({"batch_results": results, "count": len(results)})

    async def _execute_single_action(self, action: str, params: dict, run) -> str:
        """Execute a single action with params (for batch operations)."""
        x = params.get("x")
        y = params.get("y")
        dx = params.get("dx")
        dy = params.get("dy")
        duration = params.get("duration", 0.25)

        # Mouse
        if action == "click":
            return await run(self._click, x, y, params.get("button", "left"))
        elif action == "double_click":
            return await run(self._double_click, x, y)
        elif action == "right_click":
            return await run(self._click, x, y, "right")
        elif action == "move":
            return await run(self._move, x, y, duration)
        elif action == "move_relative":
            return await run(self._move_relative, dx, dy, duration)
        elif action == "drag":
            return await run(self._drag, x, y, duration)
        elif action == "scroll":
            return await run(self._scroll, params.get("amount", 0), x, y)

        # Keyboard
        elif action == "type":
            return await run(self._type_text, params.get("text", ""), params.get("interval", 0.02))
        elif action == "write":
            return await run(self._write_text, params.get("text", ""), params.get("clear", False), params.get("interval", 0.02))
        elif action == "press":
            return await run(self._press_key, params.get("key", ""))
        elif action == "key_down":
            return await run(self._key_down, params.get("key", ""))
        elif action == "key_up":
            return await run(self._key_up, params.get("key", ""))
        elif action == "hotkey":
            return await run(self._hotkey, params.get("keys", []))

        # Screen
        elif action == "screenshot":
            return await run(self._screenshot, params.get("region"))

        # Timing
        elif action == "sleep":
            await asyncio.sleep(float(params.get("value", 0)))
            return f"Slept {params.get('value', 0)}s"

        else:
            return f"Unsupported batch action: {action}"

    # ========== Info Methods ==========

    def _get_info(self) -> str:
        pg = self._ensure_pyautogui()
        size = pg.size()
        pos = pg.position()
        return json.dumps({
            "screen": {"width": size.width, "height": size.height},
            "mouse": {"x": pos.x, "y": pos.y},
            "pause": self._pause,
            "failsafe": self._failsafe,
            "regions": list(self._defined_regions.keys()),
        })

    def _get_position(self) -> str:
        pg = self._ensure_pyautogui()
        pos = pg.position()
        return json.dumps({"x": pos.x, "y": pos.y})

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def computer(
            action: Annotated[str, Field(description="Action to perform")] = "info",
            x: Annotated[int | None, Field(description="X coordinate")] = None,
            y: Annotated[int | None, Field(description="Y coordinate")] = None,
            dx: Annotated[int | None, Field(description="Delta X for relative movement")] = None,
            dy: Annotated[int | None, Field(description="Delta Y for relative movement")] = None,
            text: Annotated[str | None, Field(description="Text for type/write actions")] = None,
            key: Annotated[str | None, Field(description="Key for press/key_down/key_up")] = None,
            keys: Annotated[list[str] | None, Field(description="Keys for hotkey")] = None,
            amount: Annotated[int | None, Field(description="Scroll amount")] = None,
            duration: Annotated[float, Field(description="Movement duration")] = 0.25,
            interval: Annotated[float, Field(description="Typing interval")] = 0.02,
            region: Annotated[list[int] | None, Field(description="Region [x, y, w, h]")] = None,
            clear: Annotated[bool, Field(description="Clear before write")] = False,
            image_path: Annotated[str | None, Field(description="Image path for locate")] = None,
            confidence: Annotated[float, Field(description="Image match confidence")] = 0.9,
            timeout: Annotated[float, Field(description="Wait timeout in seconds")] = 10.0,
            color: Annotated[list[int] | None, Field(description="RGB color for pixel_matches")] = None,
            tolerance: Annotated[int, Field(description="Color tolerance")] = 0,
            title: Annotated[str | None, Field(description="Window title")] = None,
            use_regex: Annotated[bool, Field(description="Use regex for title match")] = False,
            name: Annotated[str | None, Field(description="Region name")] = None,
            width: Annotated[int | None, Field(description="Width for region")] = None,
            height: Annotated[int | None, Field(description="Height for region")] = None,
            value: Annotated[float | None, Field(description="Value for settings")] = None,
            actions: Annotated[list[dict] | None, Field(description="Batch actions list")] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                x=x, y=y, dx=dx, dy=dy,
                text=text, key=key, keys=keys,
                amount=amount, duration=duration, interval=interval,
                region=region, clear=clear,
                image_path=image_path, confidence=confidence, timeout=timeout,
                color=tuple(color) if color else None, tolerance=tolerance,
                title=title, use_regex=use_regex,
                name=name, width=width, height=height,
                value=value,
                actions=actions,
            )
