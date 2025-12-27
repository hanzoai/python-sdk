"""Tree tool - directory tree view."""

from typing import Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout


class TreeTool(BaseTool):
    """Display directory tree structure."""

    name = "tree"

    @property
    def description(self) -> str:
        return """Display directory tree structure.

Args:
    path: Directory path to display
    depth: Maximum depth to traverse (default 3)
    include_filtered: Include normally filtered dirs like .git

Returns:
    Tree structure as text
"""

    # Directories to skip by default
    FILTERED_DIRS = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".idea",
        ".vscode",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "egg-info",
        ".tox",
        ".nox",
    }

    @auto_timeout("tree")
    async def call(
        self,
        ctx: MCPContext,
        path: str,
        depth: int = 3,
        include_filtered: bool = False,
        **kwargs,
    ) -> str:
        """Generate directory tree."""
        root = Path(path)

        if not root.exists():
            return f"Error: Path does not exist: {path}"

        if not root.is_dir():
            return f"Error: Not a directory: {path}"

        lines = []
        self._build_tree(root, lines, "", depth, include_filtered)

        return "\n".join(lines)

    def _build_tree(
        self,
        path: Path,
        lines: list[str],
        prefix: str,
        depth: int,
        include_filtered: bool,
    ) -> None:
        """Recursively build tree lines."""
        if depth < 0:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}[permission denied]")
            return

        # Filter entries
        if not include_filtered:
            entries = [e for e in entries if e.name not in self.FILTERED_DIRS]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                if depth > 0:
                    extension = "    " if is_last else "│   "
                    self._build_tree(entry, lines, prefix + extension, depth - 1, include_filtered)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def tree(
            path: Annotated[str, Field(description="Directory path")],
            depth: Annotated[int, Field(description="Max depth")] = 3,
            include_filtered: Annotated[bool, Field(description="Include filtered dirs")] = False,
            ctx: MCPContext = None,
        ) -> str:
            """Display directory tree structure."""
            return await tool_instance.call(ctx, path=path, depth=depth, include_filtered=include_filtered)
