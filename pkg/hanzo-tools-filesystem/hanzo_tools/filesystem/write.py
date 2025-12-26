"""Write tool - write/create files."""

from typing import Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import FileSystemTool, PermissionManager, auto_timeout


class WriteTool(FileSystemTool):
    """Write content to a file."""
    
    name = "write"
    
    @property
    def description(self) -> str:
        return """Write content to a file (creates or overwrites).

Args:
    file_path: Absolute path to the file
    content: Content to write

Returns:
    Success message or error
"""
    
    def __init__(self, permission_manager: PermissionManager):
        super().__init__(permission_manager)
    
    @auto_timeout("write")
    async def call(
        self,
        ctx: MCPContext,
        file_path: str,
        content: str,
        **kwargs,
    ) -> str:
        """Write content to file."""
        validation = self.validate_path(file_path)
        if not validation:
            return validation.error_message
        
        if not self.is_path_allowed(file_path):
            return f"Error: Access denied to path: {file_path}"
        
        path = Path(file_path)
        
        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} bytes to {file_path}"
            
        except Exception as e:
            return f"Error writing file: {e}"
    
    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self
        
        @mcp_server.tool()
        async def write(
            file_path: Annotated[str, Field(description="Absolute path to the file")],
            content: Annotated[str, Field(description="Content to write")],
            ctx: MCPContext = None,
        ) -> str:
            """Write content to a file."""
            return await tool_instance.call(ctx, file_path=file_path, content=content)
