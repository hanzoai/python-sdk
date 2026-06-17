"""Unified GIMP automation tool for the HIP-0300 architecture.

This module provides a single unified ``gimp`` tool that drives GIMP 3.0
through the Hanzo GIMP bridge -- a clean-room, BSD-3 GIMP plug-in that exposes
GIMP's Procedural Database (PDB) over a line-oriented JSON TCP socket.

Actions (matching the TypeScript ``gimp`` tool):
- version:          bridge + GIMP version
- open:             load an image file
- export:           export/save an image to a path
- pdb_call:         invoke any PDB procedure (the core power)
- new_image:        create a blank RGB image
- image_info:       inspect an image
- list_procedures:  enumerate PDB procedures (optional prefix filter)
- flatten:          flatten an image

Following Unix philosophy: one tool for the GIMP-automation axis. No GPL
lineage -- the bridge and this client speak GIMP's documented public API.
"""

import asyncio
import json
import os
from typing import Any, ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    InvalidParamsError,
    ToolError,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


class GimpTool(BaseTool):
    """Unified GIMP automation tool (HIP-0300).

    Connects to the Hanzo GIMP bridge over TCP and drives GIMP through its
    PDB. The bridge default endpoint is ``127.0.0.1:9876``; every action
    accepts ``host`` / ``port`` overrides.

    Actions: version, open, export, pdb_call, new_image, image_info,
    list_procedures, flatten.
    """

    name: ClassVar[str] = "gimp"
    VERSION: ClassVar[str] = "1.0.0"

    def __init__(self, host: str | None = None, port: int | None = None):
        super().__init__()
        self.host = host or os.environ.get("HANZO_GIMP_HOST", DEFAULT_HOST)
        env_port = os.environ.get("HANZO_GIMP_PORT")
        self.port = port or (int(env_port) if env_port else DEFAULT_PORT)
        self._register_gimp_actions()

    @property
    def description(self) -> str:
        return """Unified GIMP automation tool (HIP-0300).

Drives GIMP 3.0 via the clean-room BSD-3 bridge (JSON-over-TCP to the GIMP PDB).

Actions:
- version: Bridge and GIMP version
- open: Load an image file (returns image_id, width, height)
- export: Export/save an image to a path
- pdb_call: Invoke any PDB procedure -- the generic core power
- new_image: Create a blank RGB image
- image_info: Inspect an image (size, layers, precision, file, dirty)
- list_procedures: Enumerate PDB procedures (optional prefix filter)
- flatten: Flatten an image

Requires the Hanzo GIMP bridge plug-in running inside GIMP
(default 127.0.0.1:9876).
"""

    async def _bridge_request(
        self,
        method: str,
        params: dict[str, Any],
        host: str | None = None,
        port: int | None = None,
        timeout: float = 60.0,
    ) -> Any:
        """Send one JSON request to the GIMP bridge and return its result.

        Opens a short-lived connection, writes one newline-terminated JSON
        request, reads one newline-terminated JSON reply.

        Raises:
            ToolError: on connection failure, timeout, malformed reply, or an
                error response from the bridge.
        """
        host = host or self.host
        port = port or self.port
        request = json.dumps({"id": 1, "method": method, "params": params}) + "\n"

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
        except (OSError, asyncio.TimeoutError) as exc:
            raise ToolError(
                code="NOT_FOUND",
                message=f"GIMP bridge connection failed ({host}:{port}): {exc}",
                details={"host": host, "port": port},
            )

        try:
            writer.write(request.encode("utf-8"))
            await writer.drain()
            line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        except asyncio.TimeoutError:
            raise ToolError(code="TIMEOUT", message="GIMP bridge timed out")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        if not line:
            raise ToolError(
                code="INTERNAL_ERROR", message="GIMP bridge closed without replying"
            )

        try:
            msg = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ToolError(
                code="INTERNAL_ERROR",
                message=f"Invalid response from GIMP bridge: {exc}",
            )

        if isinstance(msg, dict) and msg.get("error"):
            err = msg["error"]
            raise ToolError(
                code="INTERNAL_ERROR",
                message=err.get("message", "GIMP bridge error"),
                details={"type": err.get("type")},
            )

        return msg.get("result") if isinstance(msg, dict) else msg

    def _register_gimp_actions(self):
        """Register all GIMP actions."""

        @self.action("version", "Get bridge and GIMP version")
        async def version(
            ctx: MCPContext,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Return the bridge version, GIMP version, and protocol id."""
            return await self._bridge_request("version", {}, host, port)

        @self.action("open", "Open (load) an image file")
        async def open_image(
            ctx: MCPContext,
            path: str,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Load an image from disk.

            Args:
                path: Filesystem path to the image.

            Returns:
                ``{image_id, width, height}``.
            """
            if not path:
                raise InvalidParamsError("path required", param="path")
            return await self._bridge_request("open_image", {"path": path}, host, port)

        @self.action("export", "Export/save an image to a path")
        async def export(
            ctx: MCPContext,
            image_id: int,
            path: str,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Export an image; the format is chosen by the file extension.

            Args:
                image_id: GIMP image id.
                path: Destination path (e.g. ``out.png``, ``out.xcf``).
            """
            if image_id is None:
                raise InvalidParamsError("image_id required", param="image_id")
            if not path:
                raise InvalidParamsError("path required", param="path")
            return await self._bridge_request(
                "export", {"image_id": image_id, "path": path}, host, port
            )

        @self.action("pdb_call", "Invoke any PDB procedure (generic core power)")
        async def pdb_call(
            ctx: MCPContext,
            procedure: str,
            args: list | None = None,
            host: str | None = None,
            port: int | None = None,
        ) -> Any:
            """Invoke an arbitrary GIMP PDB procedure.

            Anything GIMP can do is reachable here. Integer ids may be passed
            where a procedure expects a GIMP object (image/drawable/layer/...).

            Args:
                procedure: PDB procedure name, e.g. ``gimp-image-flatten``.
                args: Positional arguments in PDB order.
            """
            if not procedure:
                raise InvalidParamsError("procedure required", param="procedure")
            return await self._bridge_request(
                "pdb_call", {"procedure": procedure, "args": args or []}, host, port
            )

        @self.action("new_image", "Create a blank RGB image")
        async def new_image(
            ctx: MCPContext,
            width: int,
            height: int,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Create a new blank RGB image.

            Args:
                width: Image width in pixels.
                height: Image height in pixels.

            Returns:
                ``{image_id, width, height}``.
            """
            if width is None or height is None:
                raise InvalidParamsError(
                    "width and height required", param="width"
                )
            return await self._bridge_request(
                "new_image", {"width": width, "height": height}, host, port
            )

        @self.action("image_info", "Inspect an image")
        async def image_info(
            ctx: MCPContext,
            image_id: int,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Return image size, layers, precision, source file, and dirty flag."""
            if image_id is None:
                raise InvalidParamsError("image_id required", param="image_id")
            return await self._bridge_request(
                "image_info", {"image_id": image_id}, host, port
            )

        @self.action("list_procedures", "Enumerate PDB procedures")
        async def list_procedures(
            ctx: MCPContext,
            prefix: str | None = None,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """List PDB procedure names, optionally filtered by ``prefix``.

            Returns:
                ``{count, procedures: [...]}``.
            """
            params = {"prefix": prefix} if prefix else {}
            return await self._bridge_request(
                "list_procedures", params, host, port
            )

        @self.action("flatten", "Flatten an image")
        async def flatten(
            ctx: MCPContext,
            image_id: int,
            host: str | None = None,
            port: int | None = None,
        ) -> dict:
            """Flatten all layers of an image into one.

            Returns:
                ``{image_id, layer_id}``.
            """
            if image_id is None:
                raise InvalidParamsError("image_id required", param="image_id")
            return await self._bridge_request(
                "flatten", {"image_id": image_id}, host, port
            )


# Backward compatibility / convenience handle.
gimp_tool = GimpTool
