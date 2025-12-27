"""Base classes for Hanzo tool packages.

Provides the foundation for all tool implementations:
- BaseTool: Abstract base class defining the tool interface
- FileSystemTool: Base class for filesystem operations
- ToolRegistry: Central registry for tool management
"""

import inspect
import logging
import functools
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, final
from pathlib import Path
from collections.abc import Awaitable

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

logger = logging.getLogger(__name__)


def with_error_logging(tool_name: str) -> Callable:
    """Decorator to add comprehensive error logging to tool functions.

    Args:
        tool_name: Name of the tool for logging purposes

    Returns:
        Decorator function
    """
    log_dir = Path.home() / ".hanzo" / "mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    def decorator(func: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> str:
            try:
                return await func(*args, **kwargs)
            except TypeError as e:
                error_msg = str(e)
                if "takes" in error_msg and "positional argument" in error_msg:
                    sig = inspect.signature(func)
                    logger.error(
                        f"Tool {tool_name} call signature mismatch: "
                        f"expected {func.__name__}{sig}, got args={args}, kwargs={kwargs}"
                    )
                logger.exception(f"Tool {tool_name} TypeError: {e}")
                return (
                    f"Error executing tool '{tool_name}': {error_msg}\n\nCheck logs at ~/.hanzo/mcp/logs/ for details."
                )
            except Exception as e:
                logger.exception(f"Tool {tool_name} error: {e}")
                return f"Error executing tool '{tool_name}': {str(e)}\n\nCheck logs at ~/.hanzo/mcp/logs/ for details."

        return wrapper

    return decorator


def handle_connection_errors(
    func: Callable[..., Awaitable[str]],
) -> Callable[..., Awaitable[str]]:
    """Decorator to handle connection errors gracefully."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_name = type(e).__name__
            if any(name in error_name for name in ["ClosedResourceError", "ConnectionError", "BrokenPipeError"]):
                return f"Client disconnected during operation: {error_name}"
            raise

    return wrapper


class BaseTool(ABC):
    """Abstract base class for all Hanzo tools.

    All tool packages must implement this interface to be compatible
    with the hanzo-mcp server and tool registry.

    Example:
        class MyTool(BaseTool):
            @property
            def name(self) -> str:
                return "my_tool"

            @property
            def description(self) -> str:
                return "Does something useful"

            async def call(self, ctx, **params) -> str:
                return "Result"

            def register(self, mcp_server):
                @mcp_server.tool()
                async def my_tool(...):
                    return await self.call(...)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the tool name as it appears in the MCP server."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get detailed description of the tool's purpose and usage."""
        pass

    @abstractmethod
    async def call(self, ctx: MCPContext, **params: Any) -> Any:
        """Execute the tool with the given parameters.

        Args:
            ctx: MCP context for the tool call
            **params: Tool parameters provided by the caller

        Returns:
            Tool execution result
        """
        pass

    @abstractmethod
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server.

        Must create a wrapper function with explicit parameters
        that calls this tool's call method.

        Args:
            mcp_server: The FastMCP server instance
        """
        pass


class FileSystemTool(BaseTool, ABC):
    """Base class for filesystem-related tools.

    Provides common functionality for working with files and directories,
    including permission checking and path validation.
    """

    def __init__(self, permission_manager: "PermissionManager | None" = None) -> None:
        """Initialize filesystem tool.

        Args:
            permission_manager: Permission manager for access control (auto-created if None)
        """
        if permission_manager is None:
            from hanzo_tools.core.permissions import PermissionManager

            permission_manager = PermissionManager()
        self.permission_manager = permission_manager

    def validate_path(self, path: str, param_name: str = "path") -> "ValidationResult":
        """Validate a path parameter."""
        from hanzo_tools.core.validation import validate_path_parameter

        return validate_path_parameter(path, param_name)

    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed according to permission settings."""
        return self.permission_manager.is_path_allowed(path)


@final
class ToolRegistry:
    """Registry for Hanzo tools.

    Provides functionality for registering tool implementations
    with an MCP server, with support for enable/disable states.
    """

    # Class-level storage for tool states
    _enabled_tools: ClassVar[dict[str, bool]] = {}
    _config_loaded: ClassVar[bool] = False

    @classmethod
    def _load_config(cls) -> None:
        """Load tool enable/disable states from config."""
        if cls._config_loaded:
            return

        import json

        config_file = Path.home() / ".hanzo" / "mcp" / "tool_states.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    cls._enabled_tools = json.load(f)
            except Exception:
                pass
        cls._config_loaded = True

    @classmethod
    def is_tool_enabled(cls, tool_name: str) -> bool:
        """Check if a tool is enabled."""
        cls._load_config()
        return cls._enabled_tools.get(tool_name, True)  # Enabled by default

    @classmethod
    def set_tool_enabled(cls, tool_name: str, enabled: bool, persist: bool = True) -> None:
        """Enable or disable a tool."""
        import json

        cls._load_config()
        cls._enabled_tools[tool_name] = enabled

        if persist:
            config_file = Path.home() / ".hanzo" / "mcp" / "tool_states.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(cls._enabled_tools, f, indent=2)

    @staticmethod
    def register_tool(mcp_server: FastMCP, tool: BaseTool) -> None:
        """Register a tool with the MCP server.

        Args:
            mcp_server: The FastMCP server instance
            tool: The tool to register
        """
        if ToolRegistry.is_tool_enabled(tool.name):
            tool.register(mcp_server)
            logger.debug(f"Registered tool: {tool.name}")
        else:
            logger.debug(f"Skipped disabled tool: {tool.name}")

    @staticmethod
    def register_tools(mcp_server: FastMCP, tools: list[BaseTool]) -> None:
        """Register multiple tools with the MCP server."""
        for tool in tools:
            ToolRegistry.register_tool(mcp_server, tool)


# Import PermissionManager type for type hints
from hanzo_tools.core.validation import ValidationResult
from hanzo_tools.core.permissions import PermissionManager
