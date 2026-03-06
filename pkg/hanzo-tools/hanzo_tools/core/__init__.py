"""Core infrastructure for Hanzo tool packages.

Exports both:
- HIP-0300 unified tool surface (`BaseTool`, `ToolError`, `Paging`, etc.)
- Low-level base abstractions (`BaseToolABC`, `ToolRegistry`, `FileSystemTool`)
"""

from hanzo_tools.core.base import (
    BaseTool as BaseToolABC,
    ToolRegistry,
    FileSystemTool,
    with_error_logging,
    handle_connection_errors,
)
from hanzo_tools.core.types import MCPResourceDocument
from hanzo_tools.core.context import ToolContext, create_tool_context
from hanzo_tools.core.decorators import auto_timeout
from hanzo_tools.core.validation import ValidationResult, validate_path_parameter
from hanzo_tools.core.permissions import PermissionManager
from hanzo_tools.core.unified import (
    BaseTool,  # Unified HIP-0300 base class
    ActionHandler,
    ErrorCode,
    ToolError,
    ConflictError,
    NotFoundError,
    InvalidParamsError,
    Paging,
    Range,
    content_hash,
    file_uri,
)

__all__ = [
    # Base classes
    "BaseTool",
    "BaseToolABC",
    "FileSystemTool",
    "ToolRegistry",
    # HIP-0300 unified helpers
    "ActionHandler",
    "ErrorCode",
    "ToolError",
    "ConflictError",
    "NotFoundError",
    "InvalidParamsError",
    "Paging",
    "Range",
    "content_hash",
    "file_uri",
    # Context
    "ToolContext",
    "create_tool_context",
    # Permissions
    "PermissionManager",
    # Decorators
    "auto_timeout",
    "with_error_logging",
    "handle_connection_errors",
    # Validation
    "ValidationResult",
    "validate_path_parameter",
    # Types
    "MCPResourceDocument",
]
