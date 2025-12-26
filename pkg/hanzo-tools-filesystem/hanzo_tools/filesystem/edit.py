"""Edit tool - find and replace in files."""

from typing import Optional,  Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import FileSystemTool, PermissionManager, auto_timeout


class EditTool(FileSystemTool):
    """Edit files with find and replace."""

    name = "edit"

    @property
    def description(self) -> str:
        return """Edit a file by replacing text.

Args:
    file_path: Absolute path to the file
    old_string: Text to find (must be unique)
    new_string: Text to replace with
    expected_replacements: Expected number of replacements (default 1)

Returns:
    Success message with diff or error
"""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__(permission_manager)

    @auto_timeout("edit")
    async def call(
        self,
        ctx: MCPContext,
        file_path: str,
        old_string: str,
        new_string: str,
        expected_replacements: int = 1,
        **kwargs,
    ) -> str:
        """Edit file with find/replace."""
        validation = self.validate_path(file_path)
        if not validation:
            return validation.error_message

        if not self.is_path_allowed(file_path):
            return f"Error: Access denied to path: {file_path}"

        path = Path(file_path)

        if not path.exists():
            return f"Error: File does not exist: {file_path}"

        if old_string == new_string:
            return "Error: old_string and new_string are identical"

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                return f"Error: old_string not found in file"

            if count != expected_replacements:
                return (
                    f"Error: Found {count} occurrences of old_string, "
                    f"expected {expected_replacements}. "
                    f"Use expected_replacements={count} or make old_string more specific."
                )

            # Perform replacement
            new_content = content.replace(old_string, new_string, expected_replacements)

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"Successfully edited {file_path}\nReplaced {count} occurrence(s)"

        except Exception as e:
            return f"Error editing file: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def edit(
            file_path: Annotated[str, Field(description="Absolute path to the file")],
            old_string: Annotated[str, Field(description="Text to find")],
            new_string: Annotated[str, Field(description="Text to replace with")],
            expected_replacements: Annotated[int, Field(description="Expected replacements")] = 1,
            ctx: MCPContext = None,
        ) -> str:
            """Edit a file by replacing text."""
            return await tool_instance.call(
                ctx,
                file_path=file_path,
                old_string=old_string,
                new_string=new_string,
                expected_replacements=expected_replacements,
            )
