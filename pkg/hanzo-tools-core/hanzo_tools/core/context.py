"""Tool execution context utilities."""

import logging
from typing import Any, Optional
from dataclasses import field, dataclass

from mcp.server.fastmcp import Context as MCPContext

logger = logging.getLogger(__name__)


@dataclass
class ToolContext:
    """Extended context for tool execution.

    Provides utilities for logging, progress reporting,
    and accessing the MCP context.
    """

    mcp_ctx: MCPContext
    tool_name: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    async def set_tool_info(self, tool_name: str) -> None:
        """Set the current tool name for logging."""
        self.tool_name = tool_name

    async def info(self, message: str) -> None:
        """Log an info message."""
        logger.info(f"[{self.tool_name or 'tool'}] {message}")

    async def warning(self, message: str) -> None:
        """Log a warning message."""
        logger.warning(f"[{self.tool_name or 'tool'}] {message}")

    async def error(self, message: str) -> None:
        """Log an error message."""
        logger.error(f"[{self.tool_name or 'tool'}] {message}")

    async def debug(self, message: str) -> None:
        """Log a debug message."""
        logger.debug(f"[{self.tool_name or 'tool'}] {message}")

    async def progress(self, current: int, total: int, message: str = "") -> None:
        """Report progress."""
        pct = (current / total * 100) if total > 0 else 0
        await self.info(f"Progress: {current}/{total} ({pct:.1f}%) {message}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value


def create_tool_context(mcp_ctx: MCPContext) -> ToolContext:
    """Create a ToolContext from an MCP context.

    Args:
        mcp_ctx: The MCP context from the tool call

    Returns:
        Extended ToolContext for tool execution
    """
    return ToolContext(mcp_ctx=mcp_ctx)
