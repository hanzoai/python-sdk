"""Hanzo AI MCP (Model Context Protocol) module.

This module provides access to the hanzo-mcp SDK for building
MCP servers and clients with extensive tool support.

Includes JSON-RPC 2.0 stdio and HTTP transport clients for
communicating with MCP servers.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

try:
    # Try to import hanzo-mcp if installed
    from hanzo_mcp import (
        # Base classes
        BaseTool,
        ToolRegistry,
        # Server creation
        HanzoMCPServer,
        # Permissions
        PermissionManager,
        # Version
        __version__ as mcp_version,
        create_server,
        get_git_tools,
        get_agent_tools,
        get_shell_tools,
        get_memory_tools,
        get_search_tools,
        get_jupyter_tools,
        # Tool registration
        register_all_tools,
        # Tool categories
        get_filesystem_tools,
        register_all_prompts,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    # Provide a helpful error message
    def _mcp_not_installed(*args, **kwargs):
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    # Create placeholder classes/functions
    HanzoMCPServer = create_server = _mcp_not_installed
    register_all_tools = register_all_prompts = _mcp_not_installed
    get_filesystem_tools = get_shell_tools = get_agent_tools = _mcp_not_installed
    get_search_tools = get_jupyter_tools = get_git_tools = _mcp_not_installed
    get_memory_tools = _mcp_not_installed
    BaseTool = ToolRegistry = _mcp_not_installed
    PermissionManager = _mcp_not_installed
    mcp_version = "not installed"


def create_mcp_server(name: str = "hanzo-mcp", allowed_paths: list = None, **kwargs):
    """Create a new MCP server.

    Args:
        name: Name of the server
        allowed_paths: List of allowed file paths
        **kwargs: Additional server options

    Returns:
        HanzoMCPServer instance
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    return create_server(name=name, allowed_paths=allowed_paths, **kwargs)


def run_mcp_server(name: str = "hanzo-mcp", transport: str = "stdio", **kwargs):
    """Run an MCP server.

    Args:
        name: Name of the server
        transport: Transport protocol ("stdio" or "sse")
        **kwargs: Additional server options
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    server = create_server(name=name, **kwargs)
    server.run(transport=transport)


# ---------------------------------------------------------------------------
# MCP tool name normalization
# ---------------------------------------------------------------------------

_NORM_RE = re.compile(r"[^a-zA-Z0-9_\-]")


def _collapse_underscores(value: str) -> str:
    """Collapse consecutive underscores into a single underscore."""
    out: list[str] = []
    last_was_underscore = False
    for ch in value:
        if ch == "_":
            if not last_was_underscore:
                out.append(ch)
            last_was_underscore = True
        else:
            out.append(ch)
            last_was_underscore = False
    return "".join(out)


def normalize_mcp_name(name: str) -> str:
    """Normalize an MCP server/tool name for the mcp__ prefix convention.

    Exact port of claw-code's ``normalize_name_for_mcp`` (mcp.rs):
    - Replace any char that is not alphanumeric, underscore, or hyphen with ``_``.
    - If *name* starts with ``"claude.ai "``, also collapse consecutive
      underscores and strip leading/trailing underscores.
    - Non-claude.ai names keep hyphens and trailing underscores as-is.
    """
    normalized = _NORM_RE.sub("_", name)
    if name.startswith("claude.ai "):
        normalized = _collapse_underscores(normalized).strip("_")
    return normalized


def mcp_tool_name(server_name: str, tool_name: str) -> str:
    """Build the canonical mcp__server__tool name."""
    return f"mcp__{normalize_mcp_name(server_name)}__{normalize_mcp_name(tool_name)}"


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 protocol types
# ---------------------------------------------------------------------------


class MCPClientError(Exception):
    """Raised on MCP client transport or protocol errors."""


@dataclass
class JsonRpcError:
    code: int
    message: str
    data: Any = None

    @classmethod
    def from_dict(cls, d: dict) -> JsonRpcError:
        return cls(code=d["code"], message=d["message"], data=d.get("data"))


@dataclass
class JsonRpcRequest:
    method: str
    params: dict[str, Any] = field(default_factory=dict)
    id: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "method": self.method, "params": self.params, "id": self.id}

    def to_line(self) -> bytes:
        return json.dumps(self.to_dict(), separators=(",", ":")).encode() + b"\n"


@dataclass
class JsonRpcResponse:
    id: int
    result: Any = None
    error: JsonRpcError | None = None

    @classmethod
    def from_dict(cls, d: dict) -> JsonRpcResponse:
        err = None
        if "error" in d and d["error"] is not None:
            err = JsonRpcError.from_dict(d["error"])
        return cls(id=d.get("id", 0), result=d.get("result"), error=err)


# ---------------------------------------------------------------------------
# Stdio transport MCP client
# ---------------------------------------------------------------------------

_MCP_PROTOCOL_VERSION = "2024-11-05"

_INIT_PARAMS: dict[str, Any] = {
    "protocolVersion": _MCP_PROTOCOL_VERSION,
    "capabilities": {},
    "clientInfo": {"name": "hanzoai-python", "version": "1.0.0"},
}


class MCPClient:
    """MCP client that communicates with a server subprocess over stdio JSON-RPC."""

    def __init__(
        self,
        server_command: list[str],
        env: dict[str, str] | None = None,
    ) -> None:
        self.server_command = server_command
        self.env = env
        self._process: asyncio.subprocess.Process | None = None
        self._next_id: int = 1
        self.server_info: dict[str, Any] | None = None
        self.capabilities: dict[str, Any] | None = None

    def _require_connected(self) -> None:
        if self._process is None or self._process.stdin is None:
            raise MCPClientError("not connected - call connect() first")

    async def _send(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._require_connected()
        req = JsonRpcRequest(method=method, params=params or {}, id=self._next_id)
        self._next_id += 1

        stdin = self._process.stdin
        stdout = self._process.stdout
        assert stdin is not None and stdout is not None

        stdin.write(req.to_line())
        await stdin.drain()

        try:
            raw = await asyncio.wait_for(stdout.readline(), timeout=30.0)
        except asyncio.TimeoutError:
            raise MCPClientError("server did not respond within 30 seconds") from None
        if not raw:
            raise MCPClientError("server closed stdout unexpectedly")
        if len(raw) > 10_485_760:  # 10 MB guard
            raise MCPClientError("server response exceeded 10 MB limit")

        resp = JsonRpcResponse.from_dict(json.loads(raw))
        if resp.error is not None:
            raise MCPClientError(f"JSON-RPC error {resp.error.code}: {resp.error.message}")
        return resp.result

    async def connect(self) -> None:
        """Spawn the server process and perform the MCP initialize handshake."""
        try:
            self._process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env,
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raise MCPClientError(f"failed to start server process: {exc}") from exc

        result = await self._send("initialize", _INIT_PARAMS)
        self.server_info = result.get("serverInfo")
        self.capabilities = result.get("capabilities")

    async def disconnect(self) -> None:
        """Terminate the server process."""
        proc = self._process
        if proc is None:
            return
        self._process = None
        if proc.stdin is not None:
            proc.stdin.close()
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except (ProcessLookupError, asyncio.TimeoutError):
            proc.kill()
            await proc.wait()

    async def list_tools(self) -> list[dict[str, Any]]:
        """Fetch all tools, following pagination cursors."""
        self._require_connected()
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {}
            if cursor is not None:
                params["cursor"] = cursor
            result = await self._send("tools/list", params)
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a tool on the server."""
        self._require_connected()
        params: dict[str, Any] = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send("tools/call", params)

    async def list_resources(self) -> list[dict[str, Any]]:
        """Fetch all resources."""
        self._require_connected()
        result = await self._send("resources/list")
        return result.get("resources", [])

    async def __aenter__(self) -> MCPClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.disconnect()


# ---------------------------------------------------------------------------
# HTTP transport MCP client
# ---------------------------------------------------------------------------


class MCPHttpClient:
    """MCP client that communicates with a server over HTTP POST (JSON-RPC)."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = url
        self._client = httpx.AsyncClient(
            headers=headers or {},
            timeout=httpx.Timeout(timeout),
        )
        self._next_id: int = 1
        self.server_info: dict[str, Any] | None = None
        self.capabilities: dict[str, Any] | None = None

    async def _send(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req = JsonRpcRequest(method=method, params=params or {}, id=self._next_id)
        self._next_id += 1

        resp = await self._client.post(self.url, json=req.to_dict())
        resp.raise_for_status()
        body = resp.json()

        rpc_resp = JsonRpcResponse.from_dict(body)
        if rpc_resp.error is not None:
            raise MCPClientError(f"JSON-RPC error {rpc_resp.error.code}: {rpc_resp.error.message}")
        return rpc_resp.result

    async def connect(self) -> None:
        """Perform the MCP initialize handshake over HTTP."""
        result = await self._send("initialize", _INIT_PARAMS)
        self.server_info = result.get("serverInfo")
        self.capabilities = result.get("capabilities")

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {}
            if cursor is not None:
                params["cursor"] = cursor
            result = await self._send("tools/list", params)
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send("tools/call", params)

    async def list_resources(self) -> list[dict[str, Any]]:
        result = await self._send("resources/list")
        return result.get("resources", [])

    async def __aenter__(self) -> MCPHttpClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.disconnect()


__all__ = [
    # Server
    "HanzoMCPServer",
    "create_server",
    "create_mcp_server",
    "run_mcp_server",
    # Tools
    "register_all_tools",
    "register_all_prompts",
    "get_filesystem_tools",
    "get_shell_tools",
    "get_agent_tools",
    "get_search_tools",
    "get_jupyter_tools",
    "get_git_tools",
    "get_memory_tools",
    # Base classes
    "BaseTool",
    "ToolRegistry",
    # Permissions
    "PermissionManager",
    # Protocol types
    "JsonRpcRequest",
    "JsonRpcResponse",
    "JsonRpcError",
    "MCPClientError",
    # Clients
    "MCPClient",
    "MCPHttpClient",
    # Name helpers
    "normalize_mcp_name",
    "mcp_tool_name",
    # Status
    "MCP_AVAILABLE",
    "mcp_version",
]
