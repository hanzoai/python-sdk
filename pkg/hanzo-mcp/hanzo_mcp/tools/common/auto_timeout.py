"""Universal auto-timeout and backgrounding for all MCP tools.

This module provides automatic timeout and backgrounding for any MCP tool operation
that takes longer than the configured threshold (default: 2 minutes).
"""

import os
import json
import time
import uuid
import asyncio
import functools
from typing import Any, Tuple, Callable, Optional
from pathlib import Path
from collections.abc import Awaitable

import aiofiles
from mcp.server.fastmcp import Context as MCPContext

from .timeout_parser import parse_timeout, format_timeout


class MCPToolTimeoutManager:
    """Manager for MCP tool timeouts and backgrounding."""

    # Default timeout before auto-backgrounding (2 minutes)
    DEFAULT_TIMEOUT = 120.0

    # Environment variable to configure timeout
    TIMEOUT_ENV_VAR = "HANZO_MCP_TOOL_TIMEOUT"

    def __init__(self, process_manager: Optional[Any] = None):
        """Initialize the timeout manager.

        Args:
            process_manager: Process manager for tracking background operations
        """
        if process_manager is None:
            # Lazy import to avoid circular imports
            try:
                from hanzo_tools.shell.base_process import ProcessManager

                self.process_manager = ProcessManager()
            except ImportError:
                # If ProcessManager is not available, disable backgrounding
                self.process_manager = None
        else:
            self.process_manager = process_manager

        # Get timeout from environment or use default
        env_timeout = os.getenv(self.TIMEOUT_ENV_VAR)
        if env_timeout:
            try:
                self.timeout = parse_timeout(env_timeout)
            except ValueError:
                self.timeout = self.DEFAULT_TIMEOUT
        else:
            self.timeout = self.DEFAULT_TIMEOUT

    def _get_timeout_for_tool(self, tool_name: str) -> float:
        """Get timeout setting for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Timeout in seconds
        """
        # Check for tool-specific timeout
        env_var = f"HANZO_MCP_{tool_name.upper()}_TIMEOUT"
        tool_timeout = os.getenv(env_var)
        if tool_timeout:
            try:
                return parse_timeout(tool_timeout)
            except ValueError:
                pass

        return self.timeout

    async def _background_tool_execution(
        self, tool_func: Callable, tool_name: str, ctx: MCPContext, process_id: str, log_file: Path, **params: Any
    ) -> None:
        """Execute tool in background and log results.

        Uses aiofiles for non-blocking file I/O.

        Args:
            tool_func: The tool function to execute
            tool_name: Name of the tool
            ctx: MCP context
            process_id: Process identifier
            log_file: Log file path
            **params: Tool parameters
        """
        try:
            # Log start (async)
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"=== Background execution started for {tool_name} ===\n")
                await f.write(f"Parameters: {json.dumps(params, indent=2, default=str)}\n")
                await f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Execute the tool
            result = await tool_func(ctx, **params)

            # Log completion (async)
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"\n\n=== Tool execution completed ===\n")
                await f.write(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                await f.write(f"Result length: {len(str(result))} characters\n")
                await f.write("\n=== RESULT ===\n")
                await f.write(str(result))
                await f.write("\n=== END RESULT ===\n")

            # Mark as completed
            self.process_manager.mark_completed(process_id, 0)

        except Exception as e:
            # Log error (async)
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"\n\n=== Tool execution failed ===\n")
                await f.write(f"Failed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                await f.write(f"Error: {str(e)}\n")
                await f.write(f"Error type: {type(e).__name__}\n")

            self.process_manager.mark_completed(process_id, 1)


def with_auto_timeout(tool_name: str, timeout_manager: Optional[MCPToolTimeoutManager] = None):
    """Decorator to add automatic timeout and backgrounding to MCP tools.

    Args:
        tool_name: Name of the tool (for logging and process tracking)
        timeout_manager: Optional timeout manager instance

    Returns:
        Decorator function
    """
    if timeout_manager is None:
        timeout_manager = MCPToolTimeoutManager()

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **params: Any) -> Any:
            # Handle both method calls (with self) and function calls
            # For methods: args = (self, ctx), For functions: args = (ctx,)
            if len(args) >= 2:
                # Method call: self, ctx, **params
                self_or_ctx = args[0]
                ctx = args[1]
                call_func = lambda: func(self_or_ctx, ctx, **params)
            elif len(args) == 1:
                # Function call: ctx, **params
                ctx = args[0]
                call_func = lambda: func(ctx, **params)
            else:
                raise TypeError(f"Expected at least 1 argument (ctx), got {len(args)}")

            # Fast path for tests - skip timeout logic
            if os.getenv("HANZO_MCP_FAST_TESTS") == "1":
                return await call_func()

            # Get tool-specific timeout
            tool_timeout = timeout_manager._get_timeout_for_tool(tool_name)

            # Create task for the tool execution
            tool_task = asyncio.create_task(call_func())

            try:
                # Wait for completion with timeout
                result = await asyncio.wait_for(tool_task, timeout=tool_timeout)
                return result

            except asyncio.TimeoutError:
                # Tool timed out - background it if process manager is available
                if timeout_manager.process_manager is None:
                    # No process manager - just report timeout
                    timeout_formatted = format_timeout(tool_timeout)
                    return f"Operation timed out after {timeout_formatted}. Backgrounding unavailable."

                process_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
                log_file = await timeout_manager.process_manager.create_log_file(process_id)

                # Start background execution (need to reconstruct the call)
                async def background_call():
                    if len(args) >= 2:
                        return await func(args[0], ctx, **params)
                    else:
                        return await func(ctx, **params)

                asyncio.create_task(
                    timeout_manager._background_tool_execution(
                        background_call, tool_name, ctx, process_id, log_file, **params
                    )
                )

                # Return backgrounding message
                timeout_formatted = format_timeout(tool_timeout)
                return (
                    f"Operation automatically backgrounded after {timeout_formatted}\n"
                    f"Process ID: {process_id}\n"
                    f"Log file: {log_file}\n\n"
                    f"Use 'process --action logs --id {process_id}' to view results\n"
                    f"Use 'process --action kill --id {process_id}' to cancel\n\n"
                    f"The {tool_name} operation is continuing in the background..."
                )

        return wrapper

    return decorator


# Global timeout manager instance
_global_timeout_manager = None


def get_global_timeout_manager() -> MCPToolTimeoutManager:
    """Get the global timeout manager instance.

    Returns:
        Global timeout manager
    """
    global _global_timeout_manager
    if _global_timeout_manager is None:
        _global_timeout_manager = MCPToolTimeoutManager()
    return _global_timeout_manager


def set_global_timeout(timeout_seconds: float) -> None:
    """Set the global timeout for all MCP tools.

    Args:
        timeout_seconds: Timeout in seconds
    """
    manager = get_global_timeout_manager()
    manager.timeout = timeout_seconds


def set_tool_timeout(tool_name: str, timeout_seconds: float) -> None:
    """Set timeout for a specific tool via environment variable.

    Args:
        tool_name: Name of the tool
        timeout_seconds: Timeout in seconds
    """
    env_var = f"HANZO_MCP_{tool_name.upper()}_TIMEOUT"
    os.environ[env_var] = str(timeout_seconds)


# Convenience decorator using global manager
def auto_timeout(tool_name: str):
    """Convenience decorator using the global timeout manager.

    Args:
        tool_name: Name of the tool

    Returns:
        Decorator function
    """
    return with_auto_timeout(tool_name, get_global_timeout_manager())
