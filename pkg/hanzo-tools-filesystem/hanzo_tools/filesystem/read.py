"""Read tool - read file contents."""

from typing import Any, Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import FileSystemTool, PermissionManager, auto_timeout


class ReadTool(FileSystemTool):
    """Read file contents with line numbers."""

    name = "read"

    @property
    def description(self) -> str:
        return """Read file contents with line numbers.

Args:
    file_path: Absolute path to the file
    offset: Starting line (0-based, optional)
    limit: Max lines to read (optional, default 2000)

Returns:
    File contents with line numbers
"""

    def __init__(self, permission_manager: PermissionManager):
        super().__init__(permission_manager)

    @auto_timeout("read")
    async def call(
        self,
        ctx: MCPContext,
        file_path: str,
        offset: int = 0,
        limit: int = 2000,
        **kwargs,
    ) -> str:
        """Read file contents."""
        # Validate path
        validation = self.validate_path(file_path)
        if not validation:
            return validation.error_message

        if not self.is_path_allowed(file_path):
            return f"Error: Access denied to path: {file_path}"

        path = Path(file_path)

        if not path.exists():
            return f"Error: File does not exist: {file_path}"

        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Apply offset and limit
            total_lines = len(lines)
            selected = lines[offset : offset + limit]

            # Format with line numbers
            output_lines = []
            for i, line in enumerate(selected, start=offset + 1):
                line = line.rstrip("\n\r")
                # Truncate long lines
                if len(line) > 2000:
                    line = line[:2000] + "..."
                output_lines.append(f"{i:6}→{line}")

            result = "\n".join(output_lines)

            # Add info if truncated
            if offset > 0 or offset + limit < total_lines:
                result += f"\n\n[Showing lines {offset + 1}-{min(offset + limit, total_lines)} of {total_lines}]"

            return result

        except Exception as e:
            return f"Error reading file: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def read(
            file_path: Annotated[str, Field(description="Absolute path to the file")],
            offset: Annotated[int, Field(description="Starting line (0-based)")] = 0,
            limit: Annotated[int, Field(description="Max lines to read")] = 2000,
            ctx: MCPContext = None,
        ) -> str:
            """Read file contents with line numbers."""
            return await tool_instance.call(ctx, file_path=file_path, offset=offset, limit=limit)
