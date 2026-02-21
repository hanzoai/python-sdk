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
    BaseTool as BaseToolABC,  # Low-level ABC
    ToolRegistry,
    FileSystemTool,
)
from hanzo_tools.core.types import MCPResourceDocument
from hanzo_tools.core.context import ToolContext, create_tool_context
from hanzo_tools.core.id_tool import IdTool, id_tool
from hanzo_tools.core.unified import (
    Range,
    Paging,
    BaseTool,  # HIP-0300 unified tool - use this
    ErrorCode,
    ToolError,
    ActionHandler,
    ConflictError,
    NotFoundError,
    InvalidParamsError,
    file_uri,
    content_hash,
)
from hanzo_tools.core.decorators import auto_timeout
from hanzo_tools.core.permissions import PermissionManager

__all__ = [
    # HIP-0300 Base class - use this for new tools
    "BaseTool",
    # Low-level ABC (for FileSystemTool etc)
    "BaseToolABC",
    "FileSystemTool",
    "ToolRegistry",
    # HIP-0300 helpers
    "ActionHandler",
    "ToolError",
    "ConflictError",
    "NotFoundError",
    "InvalidParamsError",
    "Paging",
    "Range",
    "ErrorCode",
    "content_hash",
    "file_uri",
    # Identity tool
    "IdTool",
    "id_tool",
    # Types
    "MCPResourceDocument",
    # Context
    "PermissionManager",
    "ToolContext",
    "create_tool_context",
    "auto_timeout",
]
