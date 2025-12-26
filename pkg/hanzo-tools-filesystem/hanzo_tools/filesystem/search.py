"""Search tool - search file contents."""

import re
import subprocess
from typing import Optional, Annotated
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout


class SearchTool(BaseTool):
    """Search file contents using regex."""

    name = "search"

    @property
    def description(self) -> str:
        return """Search for patterns in file contents.

Uses ripgrep (rg) if available, falls back to Python regex.

Args:
    pattern: Regex pattern to search for
    path: Directory or file to search (default: current dir)
    include: Glob pattern to filter files (e.g., "*.py")
    context_lines: Lines of context around matches
    max_results: Maximum results (default 50)

Returns:
    Matching lines with file paths and line numbers
"""

    @auto_timeout("search")
    async def call(
        self,
        ctx: MCPContext,
        pattern: str,
        path: str = ".",
        include: Optional[str] = None,
        context_lines: int = 2,
        max_results: int = 50,
        **kwargs,
    ) -> str:
        """Search for pattern in files."""
        root = Path(path).resolve()

        if not root.exists():
            return f"Error: Path does not exist: {path}"

        # Try ripgrep first (much faster)
        try:
            result = await self._search_with_rg(pattern, root, include, context_lines, max_results)
            if result is not None:
                return result
        except Exception:
            pass

        # Fallback to Python
        return await self._search_with_python(pattern, root, include, context_lines, max_results)

    async def _search_with_rg(
        self,
        pattern: str,
        root: Path,
        include: Optional[str],
        context_lines: int,
        max_results: int,
    ) -> Optional[str]:
        """Search using ripgrep."""
        cmd = [
            "rg",
            "--line-number",
            "--color=never",
            f"--max-count={max_results}",
        ]

        if context_lines > 0:
            cmd.append(f"-C{context_lines}")

        if include:
            cmd.extend(["--glob", include])

        cmd.extend([pattern, str(root)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return result.stdout or "No matches found"
            elif result.returncode == 1:
                return "No matches found"
            else:
                return None  # Fall back to Python
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    async def _search_with_python(
        self,
        pattern: str,
        root: Path,
        include: Optional[str],
        context_lines: int,
        max_results: int,
    ) -> str:
        """Search using Python regex."""
        import fnmatch

        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Invalid regex pattern: {e}"

        matches = []

        # Find files to search
        if root.is_file():
            files = [root]
        else:
            files = list(root.rglob("*"))

        for file_path in files:
            if not file_path.is_file():
                continue

            if include and not fnmatch.fnmatch(file_path.name, include):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        rel_path = file_path.relative_to(root)
                        matches.append(f"{rel_path}:{i}:{line.rstrip()}")

                        if len(matches) >= max_results:
                            break

                if len(matches) >= max_results:
                    break

            except Exception:
                continue

        if not matches:
            return "No matches found"

        result = f"Found {len(matches)} matches:\n\n"
        result += "\n".join(matches)

        if len(matches) >= max_results:
            result += f"\n\n[Truncated at {max_results} results]"

        return result

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def search(
            pattern: Annotated[str, Field(description="Regex pattern")],
            path: Annotated[str, Field(description="Path to search")] = ".",
            include: Annotated[Optional[str], Field(description="File pattern")] = None,
            context_lines: Annotated[int, Field(description="Context lines")] = 2,
            max_results: Annotated[int, Field(description="Max results")] = 50,
            ctx: MCPContext = None,
        ) -> str:
            """Search for patterns in file contents."""
            return await tool_instance.call(
                ctx,
                pattern=pattern,
                path=path,
                include=include,
                context_lines=context_lines,
                max_results=max_results,
            )
