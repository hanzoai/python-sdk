"""Computer control tools for Hanzo AI.

Tools:
- computer: Unified computer control with native API acceleration
  - macOS: Quartz/CoreGraphics (10-50x faster than pyautogui)
  - Linux: xdotool/scrot for X11
  - Windows: win32api via ctypes
  - Fallback: pyautogui when native unavailable

- screen: Screen recording, capture, and Claude-optimized processing
  - capture: Single screenshot
  - record: Background recording
  - session: ONE-SHOT record → analyze → compress → return for Claude
  - Claude limits: 100 frames max, 32MB payload, 2000px max dimension

Install:
    pip install hanzo-tools-computer

Usage:
    from hanzo_tools.computer import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server, permission_manager)

    # Or access individual tools
    from hanzo_tools.computer import ComputerTool, ScreenTool

Screen Limits (configurable via env vars):
    HANZO_SCREEN_DURATION=30         # Default session duration (seconds)
    HANZO_SCREEN_TARGET_FRAMES=30    # Target frames per session
    HANZO_SCREEN_MAX_SIZE=768        # Max frame dimension (capped at 1568)
    HANZO_SCREEN_QUALITY=60          # JPEG quality (1-100)
"""

from hanzo_tools.core import BaseTool, ToolRegistry, PermissionManager

from .computer_tool import ComputerTool
from .screen_tool import ScreenTool, ScreenConfig, screen_tool

# Internal utilities (used by screen_tool)
from .media_tool import MediaLimits, MediaResult, ActivitySegment, media_tool

# Export list for tool discovery - only 2 tools now
TOOLS = [ComputerTool, ScreenTool]

__all__ = [
    "ComputerTool",
    "ScreenTool",
    "ScreenConfig",
    "screen_tool",
    "MediaLimits",
    "MediaResult",
    "ActivitySegment",
    "media_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(
    mcp_server,
    permission_manager: PermissionManager,
    enabled_tools: dict[str, bool] | None = None,
) -> list[BaseTool]:
    """Register computer control tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tools
    """
    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        tool_name = tool_class.name if hasattr(tool_class, "name") else tool_class.__name__.lower()
        if enabled.get(tool_name, True):  # Enabled by default
            tool = tool_class(permission_manager)
            ToolRegistry.register_tool(mcp_server, tool)
            registered.append(tool)

    return registered
