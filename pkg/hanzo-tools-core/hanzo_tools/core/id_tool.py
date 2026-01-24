"""Identity tool for HIP-0300 architecture.

This module provides the 'id' tool for identity and addressing primitives:
- hash: Content → Digest
- uri: Path → file:// URI
- ref: Location → Reference
- verify: (Content, Digest) → Bool

Identity is fundamental to composability:
- Cache keys
- base_hash preconditions
- Deduplication
- Content-addressable storage

Effect lattice position: PURE
All operations are deterministic and side-effect free.
"""

import os
import json
import hashlib
import aiofiles
from typing import Any, ClassVar
from pathlib import Path
from urllib.parse import quote

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.unified import BaseTool
from hanzo_tools.core.unified import (
    ToolError,
    NotFoundError,
    InvalidParamsError,
)


# Supported hash algorithms
HASH_ALGORITHMS = ["sha256", "sha512", "sha1", "md5", "blake2b", "blake2s"]


class IdTool(BaseTool):
    """Identity and addressing tool (HIP-0300).

    Handles identity primitives:
    - hash: Content → Digest
    - uri: Path → file:// URI
    - ref: Location → Reference
    - verify: Check content integrity

    All operations are PURE (no side effects).
    """

    name: ClassVar[str] = "id"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._register_id_actions()

    @property
    def description(self) -> str:
        return """Identity and addressing tool (HIP-0300).

Actions:
- hash: Compute content hash (Content → Digest)
- uri: Convert path to file:// URI
- ref: Create location reference (path + optional line/col)
- verify: Check content matches expected hash

Identity is fundamental to composability:
- Cache keys for memoization
- base_hash preconditions for safe edits
- Content-addressable storage
- Deduplication

All operations are PURE.
"""

    def _compute_hash(self, content: bytes, algo: str = "sha256") -> str:
        """Compute hash of content."""
        if algo not in HASH_ALGORITHMS:
            raise InvalidParamsError(
                f"Unknown algorithm: {algo}",
                param="algo",
                expected=", ".join(HASH_ALGORITHMS),
            )

        h = hashlib.new(algo)
        h.update(content)
        return f"{algo}:{h.hexdigest()}"

    def _path_to_uri(self, path: str) -> str:
        """Convert path to file:// URI."""
        abs_path = Path(path).resolve()
        # Properly encode the path for URI
        encoded = quote(str(abs_path), safe="/:")
        return f"file://{encoded}"

    def _register_id_actions(self):
        """Register all identity actions."""

        @self.action("hash", "Compute content hash")
        async def hash_content(
            ctx: MCPContext,
            path: str | None = None,
            text: str | None = None,
            algo: str = "sha256",
        ) -> dict:
            """Compute hash of file or text content.

            Args:
                path: File path to hash
                text: Inline text to hash (alternative to path)
                algo: Hash algorithm (sha256, sha512, sha1, md5, blake2b, blake2s)

            Returns:
                {digest, algo, size}

            Effect: PURE
            """
            if path:
                full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                if not full_path.exists():
                    raise NotFoundError(f"File not found: {path}", uri=str(full_path))
                async with aiofiles.open(full_path, "rb") as f:
                    content = await f.read()
            elif text is not None:
                content = text.encode("utf-8")
            else:
                raise InvalidParamsError("Either path or text required")

            digest = self._compute_hash(content, algo)

            return {
                "digest": digest,
                "algo": algo,
                "size": len(content),
            }

        @self.action("uri", "Convert path to file:// URI")
        async def to_uri(
            ctx: MCPContext,
            path: str,
        ) -> dict:
            """Convert filesystem path to file:// URI.

            Args:
                path: Filesystem path

            Returns:
                {uri, path}

            Effect: PURE
            """
            full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
            uri = self._path_to_uri(str(full_path))

            return {
                "uri": uri,
                "path": str(full_path),
                "exists": full_path.exists(),
            }

        @self.action("ref", "Create location reference")
        async def create_ref(
            ctx: MCPContext,
            path: str,
            line: int | None = None,
            col: int | None = None,
            end_line: int | None = None,
            end_col: int | None = None,
        ) -> dict:
            """Create a location reference (URI + optional range).

            Args:
                path: File path
                line: Start line (0-based)
                col: Start column (0-based)
                end_line: End line (optional)
                end_col: End column (optional)

            Returns:
                {uri, range?, hash?}

            Effect: PURE
            """
            full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
            uri = self._path_to_uri(str(full_path))

            result = {
                "uri": uri,
                "path": str(full_path),
            }

            # Add range if line specified
            if line is not None:
                result["range"] = {
                    "start": {"line": line, "col": col or 0},
                }
                if end_line is not None:
                    result["range"]["end"] = {
                        "line": end_line,
                        "col": end_col or 0,
                    }

            # Add hash if file exists
            if full_path.exists():
                async with aiofiles.open(full_path, "rb") as f:
                    content = await f.read()
                result["hash"] = self._compute_hash(content)

            return result

        @self.action("verify", "Verify content matches expected hash")
        async def verify_hash(
            ctx: MCPContext,
            path: str | None = None,
            text: str | None = None,
            expected: str = "",
        ) -> dict:
            """Verify content matches expected hash.

            Args:
                path: File path to verify
                text: Inline text to verify (alternative)
                expected: Expected hash (format: "algo:hexdigest")

            Returns:
                {match, actual, expected}

            Effect: PURE
            """
            if not expected:
                raise InvalidParamsError("expected hash required")

            # Parse expected hash format
            if ":" in expected:
                algo, _ = expected.split(":", 1)
            else:
                algo = "sha256"
                expected = f"sha256:{expected}"

            # Get content
            if path:
                full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                if not full_path.exists():
                    raise NotFoundError(f"File not found: {path}")
                async with aiofiles.open(full_path, "rb") as f:
                    content = await f.read()
            elif text is not None:
                content = text.encode("utf-8")
            else:
                raise InvalidParamsError("Either path or text required")

            actual = self._compute_hash(content, algo)

            return {
                "match": actual == expected,
                "actual": actual,
                "expected": expected,
            }

        @self.action("algorithms", "List supported hash algorithms")
        async def list_algorithms(ctx: MCPContext) -> dict:
            """List supported hash algorithms.

            Returns:
                {algorithms, default}

            Effect: PURE
            """
            return {
                "algorithms": HASH_ALGORITHMS,
                "default": "sha256",
            }

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'id' tool with MCP server."""
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


# Singleton
id_tool = IdTool
