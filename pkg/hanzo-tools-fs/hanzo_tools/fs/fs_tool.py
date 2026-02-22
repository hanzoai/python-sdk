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
import re
import json
import fnmatch
import hashlib
from enum import Enum
from typing import Any, ClassVar, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass

import aiofiles
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    Paging,
    BaseTool,
    ConflictError,
    NotFoundError,
    PermissionManager,
    InvalidParamsError,
    file_uri,
    content_hash,
)


class PatchOp(str, Enum):
    """Patch operation type (Rust parity)."""

    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class PatchHunk:
    """A single hunk in a patch (Rust parity)."""

    context: str = ""  # @@ header context
    old_lines: list[str] = field(default_factory=list)
    new_lines: list[str] = field(default_factory=list)


@dataclass
class PatchFile:
    """A single file operation in a patch (Rust parity)."""

    op: PatchOp
    path: str
    hunks: list[PatchHunk] = field(default_factory=list)
    content: str = ""  # For ADD operations


def parse_patch_format(patch_text: str) -> list[PatchFile]:
    """Parse Rust-style patch format.

    Format:
        *** Begin Patch
        *** Add File: path
        +content lines
        *** Update File: path
        @@ context header
        -old line
        +new line
        *** Delete File: path
        *** End Patch
    """
    files = []
    current_file: PatchFile | None = None
    current_hunk: PatchHunk | None = None

    lines = patch_text.strip().splitlines()

    for line in lines:
        # Skip begin/end markers
        if line.strip() in ("*** Begin Patch", "*** End Patch"):
            continue

        # File operations
        if line.startswith("*** Add File:"):
            if current_file:
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                files.append(current_file)
            path = line.replace("*** Add File:", "").strip()
            current_file = PatchFile(op=PatchOp.ADD, path=path)
            current_hunk = None

        elif line.startswith("*** Update File:"):
            if current_file:
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                files.append(current_file)
            path = line.replace("*** Update File:", "").strip()
            current_file = PatchFile(op=PatchOp.UPDATE, path=path)
            current_hunk = None

        elif line.startswith("*** Delete File:"):
            if current_file:
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                files.append(current_file)
            path = line.replace("*** Delete File:", "").strip()
            current_file = PatchFile(op=PatchOp.DELETE, path=path)
            current_hunk = None
            files.append(current_file)
            current_file = None

        # Hunk header
        elif line.startswith("@@"):
            if current_file and current_hunk:
                current_file.hunks.append(current_hunk)
            context = line.strip()
            current_hunk = PatchHunk(context=context)

        # Content lines
        elif current_file:
            if current_file.op == PatchOp.ADD:
                # For ADD, lines starting with + are content
                if line.startswith("+"):
                    current_file.content += line[1:] + "\n"
                else:
                    current_file.content += line + "\n"
            elif current_hunk:
                if line.startswith("-"):
                    current_hunk.old_lines.append(line[1:])
                elif line.startswith("+"):
                    current_hunk.new_lines.append(line[1:])
                elif line.startswith(" "):
                    # Context line - appears in both old and new
                    current_hunk.old_lines.append(line[1:])
                    current_hunk.new_lines.append(line[1:])

    # Don't forget the last file
    if current_file:
        if current_hunk:
            current_file.hunks.append(current_hunk)
        files.append(current_file)

    return files


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
- patch: Apply Rust-style patch format (Rust parity)
- search_text: Text search
- mkdir: Create directory
- rm: Remove (requires confirm=true)

IMPORTANT: apply_patch is the ONLY way to edit existing files.
patch supports Rust grammar format: *** Begin Patch / *** Update File: / @@ / -old +new
"""

    def _validate_path(self, path: str) -> Path:
        """Validate and return Path object."""
        if not path:
            raise InvalidParamsError("Path is required", param="uri")
        if not os.path.isabs(path):
            raise InvalidParamsError(
                "Path must be absolute", param="uri", expected="absolute path"
            )
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
                async with aiofiles.open(
                    path, "r", encoding=encoding, errors="replace"
                ) as f:
                    content = await f.read()

                # Compute hash of full content
                file_hash = self._compute_hash(content)

                # Apply offset/limit by lines
                lines = content.splitlines(keepends=True)
                total_lines = len(lines)
                selected = lines[offset : offset + limit]

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
                        entries.append(
                            {
                                "name": str(rel_path),
                                "uri": file_uri(str(entry)),
                                "is_dir": entry.is_dir(),
                                "size": (
                                    entry.stat().st_size if entry.is_file() else None
                                ),
                            }
                        )
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
                },
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

        @self.action("patch", "Apply Rust-style patch format (Rust parity)")
        async def patch(
            ctx: MCPContext,
            input: str,
        ) -> dict:
            """Apply a patch in Rust grammar format.

            This provides parity with the Rust apply_patch tool.

            Format:
                *** Begin Patch
                *** Add File: path/to/new/file.py
                +new file content
                +line 2
                *** Update File: path/to/existing/file.py
                @@ context header
                -old line to remove
                +new line to add
                *** Delete File: path/to/delete.py
                *** End Patch

            Args:
                input: The patch text in Rust grammar format

            Returns:
                Results for each file operation
            """
            if not input or not input.strip():
                raise InvalidParamsError("Patch input is required", param="input")

            # Parse the patch
            try:
                patch_files = parse_patch_format(input)
            except Exception as e:
                raise InvalidParamsError(f"Invalid patch format: {e}", param="input")

            if not patch_files:
                raise InvalidParamsError(
                    "No file operations found in patch", param="input"
                )

            results = []

            for pf in patch_files:
                path = Path(pf.path)

                # Make path absolute if relative
                if not path.is_absolute():
                    # Use current working directory
                    path = Path.cwd() / path

                self._check_permission(str(path))

                try:
                    if pf.op == PatchOp.ADD:
                        # Create new file
                        if path.exists():
                            raise ConflictError(f"File already exists: {path}")

                        path.parent.mkdir(parents=True, exist_ok=True)

                        async with aiofiles.open(path, "w", encoding="utf-8") as f:
                            await f.write(pf.content)

                        results.append(
                            {
                                "op": "add",
                                "path": str(path),
                                "hash": self._compute_hash(pf.content),
                                "success": True,
                            }
                        )

                    elif pf.op == PatchOp.UPDATE:
                        # Update existing file
                        if not path.exists():
                            raise NotFoundError(f"File not found: {path}")

                        async with aiofiles.open(path, "r", encoding="utf-8") as f:
                            content = await f.read()

                        # Apply each hunk
                        for hunk in pf.hunks:
                            old_text = "\n".join(hunk.old_lines)
                            new_text = "\n".join(hunk.new_lines)

                            if old_text and old_text in content:
                                content = content.replace(old_text, new_text, 1)
                            elif not old_text and new_text:
                                # Pure addition - append to end
                                content += "\n" + new_text

                        async with aiofiles.open(path, "w", encoding="utf-8") as f:
                            await f.write(content)

                        results.append(
                            {
                                "op": "update",
                                "path": str(path),
                                "hash": self._compute_hash(content),
                                "hunks_applied": len(pf.hunks),
                                "success": True,
                            }
                        )

                    elif pf.op == PatchOp.DELETE:
                        # Delete file
                        if not path.exists():
                            results.append(
                                {
                                    "op": "delete",
                                    "path": str(path),
                                    "success": True,
                                    "message": "File already deleted",
                                }
                            )
                        else:
                            path.unlink()
                            results.append(
                                {
                                    "op": "delete",
                                    "path": str(path),
                                    "success": True,
                                }
                            )

                except Exception as e:
                    results.append(
                        {
                            "op": pf.op.value,
                            "path": str(path),
                            "success": False,
                            "error": str(e),
                        }
                    )

            return {
                "results": results,
                "total": len(results),
                "success": all(r.get("success") for r in results),
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
                path_str = (
                    uri.replace("file://", "") if uri.startswith("file://") else uri
                )
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
                            matches.append(
                                {
                                    "uri": file_uri(match_data["path"]["text"]),
                                    "line": match_data["line_number"],
                                    "text": match_data["lines"]["text"].strip(),
                                }
                            )
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
                        async with aiofiles.open(
                            file_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            line_num = 0
                            async for line in f:
                                line_num += 1
                                if regex.search(line):
                                    matches.append(
                                        {
                                            "uri": file_uri(str(file_path)),
                                            "line": line_num,
                                            "text": line.strip()[:200],
                                        }
                                    )
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
                },
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
