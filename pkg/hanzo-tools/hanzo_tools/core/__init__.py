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
from hanzo_tools.core.unified import (
    Range,
    Paging,
    BaseTool,  # Unified HIP-0300 base class
    ErrorCode,
    ToolError,
    ToolImage,
    ActionHandler,
    ConflictError,
    NotFoundError,
    InvalidParamsError,
    capture,
    file_uri,
    content_hash,
)
from hanzo_tools.core.id_tool import IdTool, id_tool
from hanzo_tools.core.cloud import (
    NO_KEY,
    HanzoCloud,
    CloudError,
    cloud_api_key,
    cloud_api_base,
)
from hanzo_tools.core.decorators import auto_timeout
from hanzo_tools.core.validation import ValidationResult, validate_path_parameter
from hanzo_tools.core.permissions import PermissionManager

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
    "ToolImage",
    "ConflictError",
    "NotFoundError",
    "InvalidParamsError",
    "Paging",
    "Range",
    "capture",
    "content_hash",
    "file_uri",
    # Identity tool
    "IdTool",
    "id_tool",
    # Cloud client (api.hanzo.ai)
    "NO_KEY",
    "HanzoCloud",
    "CloudError",
    "cloud_api_key",
    "cloud_api_base",
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
