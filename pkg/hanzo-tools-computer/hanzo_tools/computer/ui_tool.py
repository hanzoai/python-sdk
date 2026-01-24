"""Unified UI tool for HIP-0300 architecture.

This module provides a single unified 'ui' tool that consolidates:
- Computer control (click, type, screenshot, etc.)
- Screen recording (session, record, stop, analyze)

Following Unix philosophy: one tool for the Interface axis.
"""

from typing import Any, ClassVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import PermissionManager

from .computer_tool import ComputerTool


class UiTool(ComputerTool):
    """Unified UI tool (HIP-0300).

    Consolidates computer + screen tools into single 'ui' tool.
    Inherits all functionality from ComputerTool.

    Actions:
    - Mouse: click, double_click, right_click, middle_click, move, drag, scroll
    - Touch: tap, swipe, pinch
    - Keyboard: type, write, press, key_down, key_up, hotkey
    - Screen capture: screenshot, screenshot_region, capture
    - Screen recording: session, record, stop, analyze
    - Image location: locate, locate_all, locate_center, wait_for_image
    - Window: get_active_window, list_windows, focus_window
    - Screen info: get_screens, screen_size, current_screen
    - Region: define_region, region_screenshot, region_locate
    - Batch: batch
    """

    # Override name to 'ui' for HIP-0300
    name: ClassVar[str] = "ui"

    @property
    def description(self) -> str:
        return """Unified interface control tool (HIP-0300).

Actions:
- click, double_click, right_click, middle_click, move, drag, scroll
- tap, swipe, pinch (touch/mobile)
- type, write, press, key_down, key_up, hotkey (keyboard)
- screenshot, screenshot_region, capture
- session, record, stop, analyze (screen recording)
- focus_window, list_windows, get_active_window
- get_screens, screen_size

Cross-platform: macOS (Quartz), Linux (xdotool), Windows (win32api).
"""

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'ui' tool with MCP server."""
        # Delegate to parent registration but with 'ui' name
        super().register(mcp_server)


# Backward compatibility aliases
ComputerToolAlias = UiTool

# For imports: from hanzo_tools.computer import ui_tool
ui_tool = UiTool
