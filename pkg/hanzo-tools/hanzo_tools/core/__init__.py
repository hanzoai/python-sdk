"""Core infrastructure for Hanzo tool packages.

Provides:
- BaseTool: Abstract base class for all tools
- ToolRegistry: Tool registration and discovery
- ToolContext: Execution context utilities
- Decorators for timeouts, error handling, etc.
"""

from hanzo_tools.core.base import (
    BaseTool,
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

__all__ = [
    # Base classes
    "BaseTool",
    "FileSystemTool",
    "ToolRegistry",
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
