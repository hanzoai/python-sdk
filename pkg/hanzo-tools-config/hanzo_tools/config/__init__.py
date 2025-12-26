"""Configuration tools for Hanzo AI.

Tools:
- config: Configuration management
- mode: Development mode switching

Install:
    pip install hanzo-tools-config
"""

import logging

logger = logging.getLogger(__name__)

_tools = []

try:
    from .config_tool import ConfigTool

    _tools.append(ConfigTool)
except ImportError as e:
    logger.debug(f"ConfigTool not available: {e}")
    ConfigTool = None

try:
    from .mode_tool import ModeTool

    _tools.append(ModeTool)
except ImportError as e:
    logger.debug(f"ModeTool not available: {e}")
    ModeTool = None

TOOLS = _tools

__all__ = [
    "TOOLS",
    "ConfigTool",
    "ModeTool",
    "register_tools",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register config tools with MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        if tool_class is None:
            continue
        tool_name = getattr(tool_class, "name", tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")

    return registered
