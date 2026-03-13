"""
ZAP Server implementation.
"""

from __future__ import annotations

import asyncio
import json
import struct
from collections.abc import Awaitable, Callable
from typing import Any

from .types import (
    MessageType,
    ServerInfo,
    Tool,
    ToolResult,
)

ToolHandler = Callable[[str, dict[str, Any]], Awaitable[Any] | Any]


class ZapServer:
    """
    ZAP Server for hosting tools.

    Example:
        >>> server = ZapServer(name="my-tools", version="1.0.0")
        >>> @server.tool("greet", "Greet someone")
        ... async def greet(name: str) -> str:
        ...     return f"Hello, {name}!"
        >>> await server.serve(9999)
    """

    def __init__(self, name: str, version: str) -> None:
        self._info = ServerInfo(
            name=name,
            version=version,
            capabilities={"tools": True, "resources": False, "prompts": False},
        )
        self._tools: dict[str, tuple[Tool, ToolHandler]] = {}
        self._server: asyncio.Server | None = None

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a tool."""
        tool = Tool(name=name, description=description, input_schema=input_schema)
        self._tools[name] = (tool, handler)

    def tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any] | None = None,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """Decorator to register a tool."""

        def decorator(handler: ToolHandler) -> ToolHandler:
            self.register_tool(
                name=name,
                description=description,
                input_schema=input_schema or {},
                handler=handler,
            )
            return handler

        return decorator

    async def serve(self, port: int, host: str = "0.0.0.0") -> None:
        """Start serving and block."""
        self._server = await asyncio.start_server(
            self._handle_connection, host, port
        )
        async with self._server:
            await self._server.serve_forever()

    async def start(self, port: int, host: str = "0.0.0.0") -> None:
        """Start serving in background."""
        self._server = await asyncio.start_server(
            self._handle_connection, host, port
        )
        await self._server.start_serving()

    async def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a client connection."""
        try:
            while True:
                # Read header
                header = await reader.readexactly(5)
                total_len, msg_type_byte = struct.unpack("<IB", header)

                # Read payload
                payload_len = total_len - 1
                if payload_len > 0:
                    payload_bytes = await reader.readexactly(payload_len)
                    payload = json.loads(payload_bytes.decode("utf-8"))
                else:
                    payload = {}

                msg_type = MessageType(msg_type_byte)
                await self._handle_message(writer, msg_type, payload)

        except asyncio.IncompleteReadError:
            pass  # Connection closed
        except Exception:
            pass  # Connection error
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_message(
        self,
        writer: asyncio.StreamWriter,
        msg_type: MessageType,
        payload: dict[str, Any],
    ) -> None:
        """Handle a message from client."""
        try:
            if msg_type == MessageType.INIT:
                await self._send(writer, MessageType.INIT_ACK, self._info.__dict__)

            elif msg_type == MessageType.LIST_TOOLS:
                tools = [t.__dict__ for t, _ in self._tools.values()]
                await self._send(writer, MessageType.LIST_TOOLS_RESPONSE, tools)

            elif msg_type == MessageType.CALL_TOOL:
                result = await self._execute_tool(payload)
                await self._send(writer, MessageType.CALL_TOOL_RESPONSE, result.__dict__)

            elif msg_type == MessageType.PING:
                await self._send(writer, MessageType.PONG, {})

            else:
                await self._send(
                    writer,
                    MessageType.ERROR,
                    {"message": f"Unknown message type: {msg_type}"},
                )

        except Exception as e:
            await self._send(writer, MessageType.ERROR, {"message": str(e)})

    async def _execute_tool(self, call: dict[str, Any]) -> ToolResult:
        """Execute a tool call."""
        name = call.get("name", "")
        args = call.get("args", {})
        call_id = call.get("id", "")

        if name not in self._tools:
            return ToolResult(id=call_id, content=None, error=f"Unknown tool: {name}")

        _, handler = self._tools[name]
        try:
            result = handler(name, args)
            if asyncio.iscoroutine(result):
                result = await result
            return ToolResult(id=call_id, content=result)
        except Exception as e:
            return ToolResult(id=call_id, content=None, error=str(e))

    async def _send(
        self,
        writer: asyncio.StreamWriter,
        msg_type: MessageType,
        payload: Any,
    ) -> None:
        """Send a message."""
        payload_bytes = json.dumps(payload).encode("utf-8") if payload else b""
        total_len = 1 + len(payload_bytes)
        header = struct.pack("<IB", total_len, msg_type)
        writer.write(header + payload_bytes)
        await writer.drain()
