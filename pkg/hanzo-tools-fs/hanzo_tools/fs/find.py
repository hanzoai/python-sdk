"""Find tool - find files by pattern."""

import fnmatch
from typing import Optional, Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout


class FindTool(BaseTool):
    """Find files by name pattern."""

    name = "find"

    @property
    def description(self) -> str:
        return """Find files and directories by name pattern.

Args:
    pattern: Glob pattern (e.g., "*.py", "test_*")
    path: Directory to search in (default: current dir)
    type: "file", "dir", or None for both
    max_results: Maximum results to return (default 100)

Returns:
    List of matching paths
"""

    IGNORED_DIRS = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".idea",
        ".vscode",
        ".mypy_cache",
        ".pytest_cache",
    }

    @auto_timeout("find")
    async def call(
        self,
        ctx: MCPContext,
        pattern: str,
        path: str = ".",
        type: Optional[str] = None,
        max_results: int = 100,
        **kwargs,
    ) -> str:
        """Find files matching pattern."""
        root = Path(path).resolve()

        if not root.exists():
            return f"Error: Path does not exist: {path}"

        matches = []

        def should_skip(p: Path) -> bool:
            return any(part in self.IGNORED_DIRS for part in p.parts)

        for item in root.rglob("*"):
            if len(matches) >= max_results:
                break

            if should_skip(item):
                continue

            # Check type filter
            if type == "file" and not item.is_file():
                continue
            if type == "dir" and not item.is_dir():
                continue

            # Check pattern match
            if fnmatch.fnmatch(item.name, pattern):
                try:
                    rel_path = item.relative_to(root)
                    suffix = "/" if item.is_dir() else ""
                    matches.append(f"{rel_path}{suffix}")
                except ValueError:
                    matches.append(str(item))

        if not matches:
            return f"No matches found for pattern: {pattern}"

        result = f"Found {len(matches)} matches:\n\n"
        result += "\n".join(matches)

        if len(matches) >= max_results:
            result += f"\n\n[Truncated at {max_results} results]"

        return result

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def find(
            pattern: Annotated[str, Field(description="Glob pattern")],
            path: Annotated[str, Field(description="Directory to search")] = ".",
            type: Annotated[Optional[str], Field(description="file, dir, or None")] = None,
            max_results: Annotated[int, Field(description="Max results")] = 100,
            ctx: MCPContext = None,
        ) -> str:
            """Find files and directories by pattern."""
            return await tool_instance.call(ctx, pattern=pattern, path=path, type=type, max_results=max_results)
