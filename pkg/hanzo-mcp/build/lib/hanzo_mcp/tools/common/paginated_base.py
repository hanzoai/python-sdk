"""Enhanced base class with automatic pagination support.

This module provides a base class that automatically handles pagination
for all tool responses that exceed MCP token limits.
"""

from abc import abstractmethod
from typing import Any, Dict, Union

from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool, handle_connection_errors
from hanzo_mcp.tools.common.pagination import CursorManager
from hanzo_mcp.tools.common.paginated_response import paginate_if_needed


class PaginatedBaseTool(BaseTool):
    """Base class for tools with automatic pagination support.

    This base class automatically handles pagination for responses that
    exceed MCP token limits, making all tools pagination-aware by default.
    """

    def __init__(self):
        """Initialize the paginated base tool."""
        super().__init__()
        self._supports_pagination = True

    @abstractmethod
    async def execute(self, ctx: MCPContext, **params: Any) -> Any:
        """Execute the tool logic and return raw results.

        This method should be implemented by subclasses to perform the
        actual tool logic. The base class will handle pagination of
        the returned results automatically.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Raw tool results (will be paginated if needed)
        """
        pass

    @handle_connection_errors
    async def call(self, ctx: MCPContext, **params: Any) -> Union[str, Dict[str, Any]]:
        """Execute the tool with automatic pagination support.

        This method wraps the execute() method and automatically handles
        pagination if the response exceeds token limits.

        Args:
            ctx: MCP context
            **params: Tool parameters including optional 'cursor'

        Returns:
            Tool result, potentially paginated
        """
        # Extract cursor if provided
        cursor = params.pop("cursor", None)

        # Validate cursor if provided
        if cursor and not CursorManager.parse_cursor(cursor):
            return {"error": "Invalid cursor provided", "code": -32602}

        # Check if this is a continuation request
        if cursor:
            # For continuation, check if we have cached results
            cursor_data = CursorManager.parse_cursor(cursor)
            if (
                cursor_data
                and "tool" in cursor_data
                and cursor_data["tool"] != self.name
            ):
                return {"error": "Cursor is for a different tool", "code": -32602}

        # Execute the tool
        try:
            result = await self.execute(ctx, **params)
        except Exception as e:
            # Format errors consistently
            return {"error": str(e), "type": type(e).__name__}

        # Handle pagination automatically
        if self._supports_pagination:
            paginated_result = paginate_if_needed(result, cursor)

            # If pagination occurred, add tool info to help with continuation
            if isinstance(paginated_result, dict) and "nextCursor" in paginated_result:
                # Enhance the cursor with tool information
                if "nextCursor" in paginated_result:
                    cursor_data = CursorManager.parse_cursor(
                        paginated_result["nextCursor"]
                    )
                    if cursor_data:
                        cursor_data["tool"] = self.name
                        cursor_data["params"] = params  # Store params for continuation
                        paginated_result["nextCursor"] = CursorManager.create_cursor(
                            cursor_data
                        )

            return paginated_result
        else:
            # Return raw result if pagination is disabled
            return result

    def disable_pagination(self):
        """Disable automatic pagination for this tool.

        Some tools may want to handle their own pagination logic.
        """
        self._supports_pagination = False

    def enable_pagination(self):
        """Re-enable automatic pagination for this tool."""
        self._supports_pagination = True


class PaginatedFileSystemTool(PaginatedBaseTool):
    """Base class for filesystem tools with pagination support."""

    def __init__(self, permission_manager):
        """Initialize filesystem tool with pagination.

        Args:
            permission_manager: Permission manager for access control
        """
        super().__init__()
        self.permission_manager = permission_manager

    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed according to permission settings.

        Args:
            path: Path to check

        Returns:
            True if the path is allowed, False otherwise
        """
        return self.permission_manager.is_path_allowed(path)


def migrate_tool_to_paginated(tool_class):
    """Decorator to migrate existing tools to use pagination.

    This decorator can be applied to existing tool classes to add
    automatic pagination support without modifying their code.

    Usage:
        @migrate_tool_to_paginated
        class MyTool(BaseTool):
            ...
    """

    class PaginatedWrapper(PaginatedBaseTool):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self._wrapped_tool = tool_class(*args, **kwargs)

        @property
        def name(self):
            return self._wrapped_tool.name

        @property
        def description(self):
            # Add pagination info to description
            desc = self._wrapped_tool.description
            if not "pagination" in desc.lower():
                desc += "\n\nThis tool supports automatic pagination. If the response is too large, it will be split across multiple requests. Use the returned cursor to continue."
            return desc

        async def execute(self, ctx: MCPContext, **params: Any) -> Any:
            # Call the wrapped tool's call method
            return await self._wrapped_tool.call(ctx, **params)

        def register(self, mcp_server):
            # Need to create a new registration that includes cursor parameter
            tool_self = self

            # Get the original registration function
            original_register = self._wrapped_tool.register

            # Create a new registration that adds cursor support
            def register_with_pagination(server):
                # First register the original tool
                original_register(server)

                # Then override with pagination support
                import inspect

                # Get the registered function
                tool_func = None
                for name, func in server._tools.items():
                    if name == self.name:
                        tool_func = func
                        break

                if tool_func:
                    # Get original signature
                    sig = inspect.signature(tool_func)
                    params = list(sig.parameters.values())

                    # Add cursor parameter if not present
                    has_cursor = any(p.name == "cursor" for p in params)
                    if not has_cursor:
                        import inspect
                        from typing import Optional

                        # Create new parameter with cursor
                        cursor_param = inspect.Parameter(
                            "cursor",
                            inspect.Parameter.KEYWORD_ONLY,
                            default=None,
                            annotation=Optional[str],
                        )

                        # Insert before ctx parameter
                        new_params = []
                        for p in params:
                            if p.name == "ctx":
                                new_params.append(cursor_param)
                            new_params.append(p)

                        # Create wrapper function
                        async def paginated_wrapper(**kwargs):
                            return await tool_self.call(kwargs.get("ctx"), **kwargs)

                        # Update registration
                        server._tools[self.name] = paginated_wrapper

            register_with_pagination(mcp_server)

    # Set the class name
    PaginatedWrapper.__name__ = f"Paginated{tool_class.__name__}"
    PaginatedWrapper.__qualname__ = f"Paginated{tool_class.__qualname__}"

    return PaginatedWrapper
