"""DEPRECATED: Use hanzo-tools instead.

This package re-exports from hanzo_tools.core for backwards compatibility.
"""

import warnings

warnings.warn(
    "hanzo-tools-core is deprecated. Use hanzo-tools instead: pip install hanzo-tools",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from hanzo-tools
from hanzo_tools.core.base import (
    BaseTool,
    ToolRegistry,
    FileSystemTool,
)
from hanzo_tools.core.types import MCPResourceDocument
from hanzo_tools.core.context import ToolContext, create_tool_context
from hanzo_tools.core.decorators import auto_timeout
from hanzo_tools.core.permissions import PermissionManager

__all__ = [
    "BaseTool",
    "FileSystemTool",
    "ToolRegistry",
    "MCPResourceDocument",
    "PermissionManager",
    "ToolContext",
    "create_tool_context",
    "auto_timeout",
]
