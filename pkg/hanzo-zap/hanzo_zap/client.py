"""
ZAP Client implementation.
"""

from __future__ import annotations

import asyncio
import json
import ssl
import struct
from typing import Any
from urllib.parse import urlparse

from .types import (
    ClientInfo,
    MessageType,
    Resource,
    ServerInfo,
    Tool,
    ToolCall,
    ToolResult,
)

MAX_MESSAGE_SIZE = 16 * 1024 * 1024  # 16MB


class ZapClient:
    """
    ZAP Client for connecting to ZAP servers.

    Example:
        >>> async with ZapClient.connect("zap://localhost:9999") as client:
        ...     tools = await client.list_tools()
        ...     result = await client.call_tool("read_file", {"path": "README.md"})
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._server_info: ServerInfo | None = None
        self._request_id = 0

    @classmethod
    async def connect(cls, url: str) -> ZapClient:
        """
        Connect to a ZAP server.

        Args:
            url: Server URL (zap:// or zaps:// for TLS)

        Returns:
            Connected ZapClient instance
        """
        parsed = urlparse(url)
        use_tls = parsed.scheme == "zaps"
        host = parsed.hostname or "localhost"
        port = parsed.port or 9999

        ssl_ctx = ssl.create_default_context() if use_tls else None

        reader, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx)
        client = cls(reader, writer)
        await client._handshake()
        return client

    async def _handshake(self) -> None:
        """Perform protocol handshake."""
        client_info = ClientInfo(name="hanzo-zap", version="0.6.1")
        await self._send(MessageType.INIT, client_info.__dict__)
        msg_type, payload = await self._recv()

        if msg_type != MessageType.INIT_ACK:
            raise ConnectionError(f"Expected INIT_ACK, got {msg_type}")

        self._server_info = ServerInfo(**payload)

    @property
    def server_info(self) -> ServerInfo | None:
        """Get server info from handshake."""
        return self._server_info

    async def list_tools(self) -> list[Tool]:
        """List available tools."""
        await self._send(MessageType.LIST_TOOLS, {})
        _, payload = await self._recv()
        return [Tool(**t) for t in payload]

    async def call_tool(self, name: str, args: dict[str, Any]) -> ToolResult:
        """Call a tool by name."""
        self._request_id += 1
        call = ToolCall(id=f"req-{self._request_id}", name=name, args=args)
        await self._send(MessageType.CALL_TOOL, call.__dict__)
        _, payload = await self._recv()
        return ToolResult(**payload)

    async def batch(
        self, calls: list[dict[str, Any]]
    ) -> list[ToolResult]:
        """Call multiple tools in a batch."""
        return [await self.call_tool(c["name"], c["args"]) for c in calls]

    async def list_resources(self) -> list[Resource]:
        """List available resources."""
        await self._send(MessageType.LIST_RESOURCES, {})
        _, payload = await self._recv()
        return [Resource(**r) for r in payload]

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource by URI."""
        await self._send(MessageType.READ_RESOURCE, {"uri": uri})
        _, payload = await self._recv()
        return payload

    async def ping(self) -> None:
        """Send ping to check connection."""
        await self._send(MessageType.PING, {})
        msg_type, _ = await self._recv()
        if msg_type != MessageType.PONG:
            raise ConnectionError(f"Expected PONG, got {msg_type}")

    async def close(self) -> None:
        """Close the connection."""
        self._writer.close()
        await self._writer.wait_closed()

    async def __aenter__(self) -> ZapClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _send(self, msg_type: MessageType, payload: dict[str, Any]) -> None:
        """Send a message with ZAP wire format."""
        payload_bytes = json.dumps(payload).encode("utf-8") if payload else b""
        total_len = 1 + len(payload_bytes)

        # Header: 4-byte LE length + 1-byte message type
        header = struct.pack("<IB", total_len, msg_type)
        self._writer.write(header + payload_bytes)
        await self._writer.drain()

    async def _recv(self) -> tuple[MessageType, Any]:
        """Receive and parse a message."""
        # Read header
        header = await self._reader.readexactly(5)
        total_len, msg_type_byte = struct.unpack("<IB", header)

        if total_len > MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {total_len}")

        # Read payload
        payload_len = total_len - 1
        if payload_len > 0:
            payload_bytes = await self._reader.readexactly(payload_len)
            payload = json.loads(payload_bytes.decode("utf-8"))
        else:
            payload = {}

        msg_type = MessageType(msg_type_byte)

        if msg_type == MessageType.ERROR:
            raise RuntimeError(payload.get("message", "Server error"))

        return msg_type, payload
