"""Computer control tools for Hanzo AI.

Tools:
- computer: Control local computer via pyautogui (mouse, keyboard, screenshots)
- fast_computer: Ultra-fast native macOS control via Quartz/CoreGraphics
- video: Screen recording and video capture
- media: Image/video processing with configurable limits (100 images, 32MB max)

Install:
    pip install hanzo-tools-computer

Usage:
    from hanzo_tools.computer import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server, permission_manager)

    # Or access individual tools
    from hanzo_tools.computer import ComputerTool, FastComputerTool, VideoTool, MediaTool

Media Limits (configurable via env vars):
    HANZO_MEDIA_MAX_IMAGES=100       # Max images per batch
    HANZO_MEDIA_MAX_PAYLOAD_MB=32    # Max total payload in MB
    HANZO_MEDIA_MAX_RESOLUTION=1568  # Max image dimension
    HANZO_MEDIA_OPTIMAL_SIZE=768     # Target size for optimization
    HANZO_MEDIA_JPEG_QUALITY=85      # JPEG quality (1-100)
"""

from hanzo_tools.core import BaseTool, ToolRegistry, PermissionManager

from .computer_tool import ComputerTool
from .fast_computer import FastComputerTool
from .video_tool import VideoTool
from .media_tool import MediaTool, MediaLimits, MediaResult, ActivitySegment, media_tool
from .screen_tool import ScreenTool, ScreenConfig, screen_tool

# Export list for tool discovery
TOOLS = [ComputerTool, FastComputerTool, VideoTool, MediaTool, ScreenTool]

__all__ = [
    "ComputerTool",
    "FastComputerTool",
    "VideoTool",
    "MediaTool",
    "MediaLimits",
    "MediaResult",
    "ActivitySegment",
    "media_tool",
    "ScreenTool",
    "ScreenConfig",
    "screen_tool",
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
