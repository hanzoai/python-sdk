"""Common utilities for Hanzo MCP tools.

System tools (always available):
- tool_install: Install, update, reload tools dynamically
- tool_enable/tool_disable: Enable/disable tools at runtime
- tool_list: List available tools
- version: Get hanzo-mcp version info
- stats: Usage statistics

Base classes and utilities:
- BaseTool: Base class for all tools
- ToolRegistry: Tool registration utilities
- PermissionManager: File access control

Note: All actual tools (think, critic, dag, read, etc.) come from
hanzo-tools-* packages via entry points. See entrypoint_loader.py.
"""

from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.common.tool_install import ToolInstallTool, register_tool_install

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "ToolInstallTool",
    "register_tool_install",
]
