"""ZAP (Zero-copy Agent Protocol) Server for hanzo-mcp.

Allows Hanzo browser extensions and agents to discover this MCP server
and call tools directly over the native ZAP binary protocol.

Uses the ``zap-protocol`` package for wire format and transport,
adding hanzo-mcp-specific request routing on top.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from zap.protocol import (
    HEADER_SIZE,
    MAX_MESSAGE_SIZE,
    MSG_HANDSHAKE,
    MSG_HANDSHAKE_OK,
    MSG_PING,
    MSG_PONG,
    MSG_REQUEST,
    MSG_RESPONSE,
    ZAP_MAGIC,
    ZAP_PORTS,
    decode,
    encode,
)

logger = logging.getLogger(__name__)


# ── Client tracking ─────────────────────────────────────────────────────


class ZapClient:
    __slots__ = ("writer", "client_id", "browser", "version", "connected_at")

    def __init__(
        self,
        writer: asyncio.StreamWriter,
        client_id: str = "unknown",
        browser: str = "unknown",
        version: str = "0",
    ) -> None:
        self.writer = writer
        self.client_id = client_id
        self.browser = browser
        self.version = version
        self.connected_at = time.time()


# ── ZAP TCP Server ──────────────────────────────────────────────────────


class ZapServer:
    """ZAP TCP server for agent and browser extension discovery.

    Provides full MCP protocol parity — any MCP method (tools/*, resources/*,
    prompts/*) can be called over the ZAP binary transport via the
    handle_method pass-through.
    """

    def __init__(
        self,
        tools: list[dict[str, Any]],
        call_tool: Callable[[str, dict[str, Any]], Awaitable[Any]],
        handle_method: Callable[[str, Any], Awaitable[Any]] | None = None,
        name: str = "hanzo-mcp",
    ) -> None:
        self.tools = tools
        self.call_tool = call_tool
        self.handle_method = handle_method
        self.name = name
        self.server_id = f"mcp-{int(time.time()):x}"
        self.clients: dict[str, ZapClient] = {}
        self._server: asyncio.Server | None = None
        self.port: int | None = None

        self.tool_manifest = [
            {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "inputSchema": t.get("inputSchema", t.get("input_schema", {})),
            }
            for t in self.tools
        ]

    async def _read_frame(self, reader: asyncio.StreamReader) -> tuple[int, Any] | None:
        """Read a single ZAP frame from the stream."""
        try:
            header = await reader.readexactly(HEADER_SIZE)
        except (asyncio.IncompleteReadError, ConnectionError):
            return None

        if header[:4] != ZAP_MAGIC:
            return None

        msg_type = header[4]
        import struct

        length = struct.unpack("!L", header[5:9])[0]

        if length > MAX_MESSAGE_SIZE:
            return None

        try:
            payload_bytes = await reader.readexactly(length)
        except (asyncio.IncompleteReadError, ConnectionError):
            return None

        import json

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
            return (msg_type, payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    async def _send_frame(
        self, writer: asyncio.StreamWriter, msg_type: int, payload: Any
    ) -> None:
        """Send a ZAP frame to the stream."""
        frame = encode(msg_type, payload)
        writer.write(frame)
        await writer.drain()

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a single TCP connection."""
        peer = writer.get_extra_info("peername")
        client: ZapClient | None = None
        client_key = f"{peer[0]}:{peer[1]}" if peer else f"unknown-{time.time()}"

        try:
            while True:
                result = await self._read_frame(reader)
                if result is None:
                    break

                msg_type, payload = result

                if msg_type == MSG_HANDSHAKE:
                    client_id = payload.get("clientId", "unknown")
                    browser = payload.get("browser", "unknown")
                    version = payload.get("version", "0")
                    client = ZapClient(
                        writer=writer,
                        client_id=client_id,
                        browser=browser,
                        version=version,
                    )
                    self.clients[client_key] = client
                    logger.info(
                        f"[ZAP] Client connected: {client_id} ({browser} v{version})"
                    )
                    await self._send_frame(
                        writer,
                        MSG_HANDSHAKE_OK,
                        {
                            "serverId": self.server_id,
                            "name": self.name,
                            "tools": self.tool_manifest,
                        },
                    )

                elif msg_type == MSG_REQUEST:
                    req_id = payload.get("id", "")
                    method = payload.get("method", "")
                    params = payload.get("params", {})
                    await self._handle_request(writer, req_id, method, params)

                elif msg_type == MSG_PING:
                    await self._send_frame(writer, MSG_PONG, {})

        except Exception as e:
            logger.debug(f"[ZAP] Connection error: {e}")
        finally:
            if client_key in self.clients:
                client = self.clients.pop(client_key)
                logger.info(f"[ZAP] Client disconnected: {client.client_id}")
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_request(
        self, writer: asyncio.StreamWriter, req_id: str, method: str, params: Any
    ) -> None:
        """Handle a ZAP RPC request."""
        try:
            if method == "tools/list":
                result = {"tools": self.tool_manifest}

            elif method == "tools/call":
                tool_name = (params or {}).get("name", "")
                args = (params or {}).get("arguments", {})
                if not tool_name:
                    raise ValueError("Missing tool name")
                result = await self.call_tool(tool_name, args)

            elif method.startswith("notifications/"):
                result = {"acknowledged": True}

            else:
                if self.handle_method:
                    result = await self.handle_method(method, params)
                else:
                    raise ValueError(f"Unsupported method: {method}")

            await self._send_frame(
                writer, MSG_RESPONSE, {"id": req_id, "result": result}
            )

        except Exception as e:
            await self._send_frame(
                writer,
                MSG_RESPONSE,
                {
                    "id": req_id,
                    "error": {"code": -1, "message": str(e)},
                },
            )

    async def start(self, preferred_port: int | None = None) -> bool:
        """Start the ZAP server on the first available TCP port."""
        ports = (
            [preferred_port, *[p for p in ZAP_PORTS if p != preferred_port]]
            if preferred_port
            else list(ZAP_PORTS)
        )

        for port in ports:
            try:
                self._server = await asyncio.start_server(
                    self._handle_connection,
                    "127.0.0.1",
                    port,
                )
                self.port = port
                logger.info(
                    f"[ZAP] Server listening on zap://127.0.0.1:{port} "
                    f"({len(self.tool_manifest)} tools)"
                )
                return True
            except OSError:
                continue

        logger.warning(
            "[ZAP] Could not bind to any port (9999-9995). ZAP discovery disabled."
        )
        return False

    def stop(self) -> None:
        """Stop the ZAP server."""
        if self._server:
            self._server.close()
            self._server = None
            self.port = None
            for client in list(self.clients.values()):
                try:
                    client.writer.close()
                except Exception:
                    pass
            self.clients.clear()


async def start_zap_server(
    tools: list[dict[str, Any]],
    call_tool: Callable[[str, dict[str, Any]], Awaitable[Any]],
    handle_method: Callable[[str, Any], Awaitable[Any]] | None = None,
    name: str = "hanzo-mcp",
    preferred_port: int | None = None,
) -> ZapServer | None:
    """Create and start a ZAP server.

    Args:
        tools: List of tool dicts with name, description, inputSchema.
        call_tool: Async callable (name, args) -> result to route tool calls.
        handle_method: Optional async callable (method, params) -> result for
            full MCP parity.
        name: Server name for handshake.
        preferred_port: Preferred port to try first.

    Returns:
        ZapServer instance if started, None otherwise.
    """
    server = ZapServer(
        tools=tools, call_tool=call_tool, handle_method=handle_method, name=name
    )
    ok = await server.start(preferred_port=preferred_port)
    return server if ok else None
