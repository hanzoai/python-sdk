"""Unified filesystem tool for HIP-0300 architecture.

This module provides a single unified 'fs' tool that handles all filesystem operations:
- read: Read file contents (returns hash for composability)
- write: Create new files only
- stat: File metadata including hash
- list: Directory listing with depth/pattern
- apply_patch: Edit files with base_hash precondition (the ONLY mutation for existing files)
- search_text: Ripgrep-style text search
- diff: Content diff between hashes

Following Unix philosophy: one tool for the Bytes + Paths axis.
"""

import os
import json
import fnmatch
import hashlib
import aiofiles
from typing import Any, Optional, ClassVar
from pathlib import Path
from datetime import datetime

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    PermissionManager,
    ConflictError,
    NotFoundError,
    InvalidParamsError,
    Paging,
    content_hash,
    file_uri,
)


class FsTool(BaseTool):
    """Unified filesystem tool (HIP-0300).

    Handles all filesystem operations on a single axis:
    - read: Read file contents
    - write: Create new files
    - stat: File metadata
    - list: Directory listing
    - apply_patch: Edit with precondition
    - search_text: Text search
    - mkdir: Create directory
    - rm: Remove (guarded)

    CRITICAL: apply_patch is the ONLY way to edit existing files.
    It requires base_hash to prevent stale edits.
    """

    name: ClassVar[str] = "fs"
    VERSION: ClassVar[str] = "0.12.0"

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        super().__init__()
        if permission_manager is None:
            permission_manager = PermissionManager()
        self.permission_manager = permission_manager
        self._register_fs_actions()

    @property
    def description(self) -> str:
        return """Unified filesystem tool (HIP-0300).

Actions:
- read: Read file contents (returns hash)
- write: Create new files only
- stat: File metadata including hash
- list: Directory listing
- apply_patch: Edit with base_hash precondition
- search_text: Text search
- mkdir: Create directory
- rm: Remove (requires confirm=true)

IMPORTANT: apply_patch is the ONLY way to edit existing files.
"""

    def _validate_path(self, path: str) -> Path:
        """Validate and return Path object."""
        if not path:
            raise InvalidParamsError("Path is required", param="uri")
        if not os.path.isabs(path):
            raise InvalidParamsError("Path must be absolute", param="uri", expected="absolute path")
        return Path(path)

    def _check_permission(self, path: str) -> None:
        """Check if path is allowed."""
        if not self.permission_manager.is_path_allowed(path):
            raise InvalidParamsError(f"Access denied: {path}", param="uri")

    def _compute_hash(self, content: str | bytes) -> str:
        """Compute content hash."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        h = hashlib.sha256(content)
        return f"sha256:{h.hexdigest()}"

    def _register_fs_actions(self):
        """Register all filesystem actions."""

        @self.action("read", "Read file contents")
        async def read(
            ctx: MCPContext,
            uri: str,
            offset: int = 0,
            limit: int = 2000,
            encoding: str = "utf-8",
        ) -> dict:
            """Read file contents.

            Returns text content and hash for composability.
            """
            # Handle file:// URIs
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if not path.exists():
                raise NotFoundError(f"File not found: {path}", uri=uri)

            if not path.is_file():
                raise InvalidParamsError(f"Not a file: {path}", param="uri")

            try:
                async with aiofiles.open(path, "r", encoding=encoding, errors="replace") as f:
                    content = await f.read()

                # Compute hash of full content
                file_hash = self._compute_hash(content)

                # Apply offset/limit by lines
                lines = content.splitlines(keepends=True)
                total_lines = len(lines)
                selected = lines[offset:offset + limit]

                # Format with line numbers
                output_lines = []
                for i, line in enumerate(selected, start=offset + 1):
                    line = line.rstrip("\n\r")
                    if len(line) > 2000:
                        line = line[:2000] + "..."
                    output_lines.append(f"{i:6}│{line}")

                text = "\n".join(output_lines)

                return {
                    "uri": file_uri(str(path)),
                    "text": text,
                    "hash": file_hash,
                    "total_lines": total_lines,
                    "offset": offset,
                    "limit": limit,
                }

            except UnicodeDecodeError as e:
                raise InvalidParamsError(f"Encoding error: {e}", param="encoding")

        @self.action("write", "Create new file")
        async def write(
            ctx: MCPContext,
            uri: str,
            content: str,
            encoding: str = "utf-8",
        ) -> dict:
            """Create a new file. Fails if file already exists.

            For editing existing files, use apply_patch instead.
            """
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if path.exists():
                raise ConflictError(
                    f"File already exists: {path}. Use apply_patch to edit.",
                    expected="non-existent",
                    actual="exists",
                )

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            try:
                async with aiofiles.open(path, "w", encoding=encoding) as f:
                    await f.write(content)

                file_hash = self._compute_hash(content)

                return {
                    "uri": file_uri(str(path)),
                    "hash": file_hash,
                    "size": len(content.encode(encoding)),
                }

            except Exception as e:
                raise InvalidParamsError(f"Write failed: {e}")

        @self.action("stat", "Get file metadata")
        async def stat(ctx: MCPContext, uri: str) -> dict:
            """Get file metadata including hash."""
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if not path.exists():
                raise NotFoundError(f"File not found: {path}", uri=uri)

            stat_info = path.stat()

            # Compute hash for files
            file_hash = None
            if path.is_file():
                async with aiofiles.open(path, "rb") as f:
                    file_hash = self._compute_hash(await f.read())

            return {
                "uri": file_uri(str(path)),
                "size": stat_info.st_size,
                "hash": file_hash,
                "mtime": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
            }

        @self.action("list", "List directory contents")
        async def list_dir(
            ctx: MCPContext,
            uri: str,
            depth: int = 1,
            pattern: str | None = None,
            cursor: str | None = None,
            limit: int = 100,
        ) -> dict:
            """List directory contents with optional depth and pattern."""
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if not path.exists():
                raise NotFoundError(f"Directory not found: {path}", uri=uri)

            if not path.is_dir():
                raise InvalidParamsError(f"Not a directory: {path}", param="uri")

            entries = []
            start_index = int(cursor) if cursor else 0
            count = 0
            total = 0

            def should_include(p: Path) -> bool:
                if pattern:
                    return fnmatch.fnmatch(p.name, pattern)
                return True

            def walk(dir_path: Path, current_depth: int):
                nonlocal count, total
                if current_depth > depth:
                    return

                try:
                    for entry in sorted(dir_path.iterdir()):
                        if not should_include(entry):
                            continue

                        total += 1

                        if total <= start_index:
                            continue

                        if count >= limit:
                            continue

                        rel_path = entry.relative_to(path)
                        entries.append({
                            "name": str(rel_path),
                            "uri": file_uri(str(entry)),
                            "is_dir": entry.is_dir(),
                            "size": entry.stat().st_size if entry.is_file() else None,
                        })
                        count += 1

                        if entry.is_dir() and current_depth < depth:
                            walk(entry, current_depth + 1)

                except PermissionError:
                    pass

            walk(path, 1)

            has_more = total > start_index + count
            next_cursor = str(start_index + count) if has_more else None

            return {
                "uri": file_uri(str(path)),
                "entries": entries,
                "paging": {
                    "cursor": next_cursor,
                    "more": has_more,
                    "total": total,
                }
            }

        @self.action("apply_patch", "Edit file with precondition")
        async def apply_patch(
            ctx: MCPContext,
            uri: str,
            old_text: str,
            new_text: str,
            base_hash: str,
        ) -> dict:
            """Edit existing file with base_hash precondition.

            This is the ONLY way to edit existing files.
            The base_hash must match the current file hash to prevent stale edits.

            Args:
                uri: File path
                old_text: Text to find and replace
                new_text: Replacement text
                base_hash: Expected hash from previous read (prevents race conditions)

            Returns:
                New file URI and hash

            Raises:
                ConflictError: If base_hash doesn't match current file
            """
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if not path.exists():
                raise NotFoundError(f"File not found: {path}", uri=uri)

            if not path.is_file():
                raise InvalidParamsError(f"Not a file: {path}", param="uri")

            # Read current content and verify hash
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            current_hash = self._compute_hash(content)

            if current_hash != base_hash:
                raise ConflictError(
                    "File has changed since last read (base_hash mismatch)",
                    expected=base_hash,
                    actual=current_hash,
                )

            # Check old_text exists and is unique
            count = content.count(old_text)

            if count == 0:
                raise NotFoundError(
                    f"old_text not found in file",
                    uri=uri,
                )

            if count > 1:
                raise InvalidParamsError(
                    f"old_text found {count} times. Make it more specific.",
                    param="old_text",
                    expected="unique match",
                )

            # Apply the patch
            new_content = content.replace(old_text, new_text, 1)

            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(new_content)

            new_hash = self._compute_hash(new_content)

            return {
                "uri": file_uri(str(path)),
                "hash": new_hash,
                "previous_hash": current_hash,
            }

        @self.action("search_text", "Search file contents")
        async def search_text(
            ctx: MCPContext,
            pattern: str,
            uri: str | None = None,
            glob: str | None = None,
            limit: int = 50,
            cursor: str | None = None,
        ) -> dict:
            """Search for text pattern in files.

            Uses ripgrep-style matching with regex support.
            """
            import re
            import subprocess

            # Default to current directory
            search_path = "."
            if uri:
                path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
                path = self._validate_path(path_str)
                self._check_permission(str(path))
                search_path = str(path)

            matches = []
            start_index = int(cursor) if cursor else 0

            # Try ripgrep first (fastest)
            try:
                cmd = ["rg", "--json", "-n", "--max-count", str(limit * 2)]
                if glob:
                    cmd.extend(["--glob", glob])
                cmd.extend([pattern, search_path])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                for line in result.stdout.splitlines():
                    if len(matches) >= limit:
                        break

                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            match_data = data["data"]
                            matches.append({
                                "uri": file_uri(match_data["path"]["text"]),
                                "line": match_data["line_number"],
                                "text": match_data["lines"]["text"].strip(),
                            })
                    except json.JSONDecodeError:
                        continue

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Fallback to Python regex search
                try:
                    regex = re.compile(pattern)
                except re.error as e:
                    raise InvalidParamsError(f"Invalid regex: {e}", param="pattern")

                async def search_file(file_path: Path):
                    try:
                        async with aiofiles.open(file_path, "r", encoding="utf-8", errors="replace") as f:
                            line_num = 0
                            async for line in f:
                                line_num += 1
                                if regex.search(line):
                                    matches.append({
                                        "uri": file_uri(str(file_path)),
                                        "line": line_num,
                                        "text": line.strip()[:200],
                                    })
                                    if len(matches) >= limit:
                                        return
                    except (PermissionError, IsADirectoryError):
                        pass

                search_dir = Path(search_path)
                if search_dir.is_file():
                    await search_file(search_dir)
                else:
                    for file_path in search_dir.rglob(glob or "*"):
                        if file_path.is_file():
                            await search_file(file_path)
                            if len(matches) >= limit:
                                break

            has_more = len(matches) >= limit
            next_cursor = str(start_index + len(matches)) if has_more else None

            return {
                "pattern": pattern,
                "matches": matches,
                "paging": {
                    "cursor": next_cursor,
                    "more": has_more,
                }
            }

        @self.action("mkdir", "Create directory")
        async def mkdir(ctx: MCPContext, uri: str) -> dict:
            """Create directory and parent directories."""
            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if path.exists():
                if path.is_dir():
                    return {"uri": file_uri(str(path)), "created": False}
                raise ConflictError(f"Path exists and is not a directory: {path}")

            path.mkdir(parents=True, exist_ok=True)

            return {"uri": file_uri(str(path)), "created": True}

        @self.action("rm", "Remove file or directory")
        async def rm(ctx: MCPContext, uri: str, confirm: bool = False) -> dict:
            """Remove file or directory.

            REQUIRES confirm=true as safety measure.
            """
            if not confirm:
                raise InvalidParamsError(
                    "rm requires confirm=true for safety",
                    param="confirm",
                    expected="true",
                )

            path_str = uri.replace("file://", "") if uri.startswith("file://") else uri
            path = self._validate_path(path_str)
            self._check_permission(str(path))

            if not path.exists():
                raise NotFoundError(f"Path not found: {path}", uri=uri)

            if path.is_file():
                path.unlink()
            else:
                import shutil
                shutil.rmtree(path)

            return {"uri": file_uri(str(path)), "removed": True}

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'fs' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Backward compatibility
fs_tool = FsTool
