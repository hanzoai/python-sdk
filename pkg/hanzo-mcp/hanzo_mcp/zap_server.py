"""ZAP (Zero-latency Agent Protocol) Server for hanzo-mcp.

Allows Hanzo browser extensions to discover this MCP server
and call tools directly over a binary WebSocket protocol.

Protocol: 9-byte header + JSON payload
  [0x5A 0x41 0x50 0x01] magic  "ZAP\x01"
  [type]                 1 byte message type
  [length]               4 bytes big-endian payload length
  [payload]              UTF-8 JSON
"""

from __future__ import annotations

import asyncio
import json
import logging
import struct
import time
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# ── Protocol Constants ──────────────────────────────────────────────────
ZAP_MAGIC = b"\x5a\x41\x50\x01"  # "ZAP\x01"
MSG_HANDSHAKE = 0x01
MSG_HANDSHAKE_OK = 0x02
MSG_REQUEST = 0x10
MSG_RESPONSE = 0x11
MSG_PING = 0xFE
MSG_PONG = 0xFF

ZAP_PORTS = [9999, 9998, 9997, 9996, 9995]
HEADER_SIZE = 9  # 4 (magic) + 1 (type) + 4 (length)


# ── Encode / Decode ─────────────────────────────────────────────────────

def encode(msg_type: int, payload: Any) -> bytes:
    """Encode a ZAP message: magic + type + length + JSON payload."""
    data = json.dumps(payload).encode("utf-8")
    header = ZAP_MAGIC + struct.pack("!BL", msg_type, len(data))
    return header + data


def decode(buf: bytes) -> tuple[int, Any] | None:
    """Decode a ZAP message. Returns (type, payload) or None."""
    if len(buf) < HEADER_SIZE:
        return None

    if buf[:4] != ZAP_MAGIC:
        # Not ZAP binary — try plain JSON fallback
        try:
            payload = json.loads(buf.decode("utf-8"))
            return (MSG_REQUEST, payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    msg_type = buf[4]
    length = struct.unpack("!L", buf[5:9])[0]
    if len(buf) < HEADER_SIZE + length:
        return None

    try:
        payload = json.loads(buf[HEADER_SIZE : HEADER_SIZE + length].decode("utf-8"))
        return (msg_type, payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ── Client tracking ─────────────────────────────────────────────────────

class ZapClient:
    __slots__ = ("writer", "client_id", "browser", "version", "connected_at")

    def __init__(
        self,
        writer: asyncio.StreamWriter,
        client_id: str = "unknown",
        browser: str = "unknown",
        version: str = "0",
    ):
        self.writer = writer
        self.client_id = client_id
        self.browser = browser
        self.version = version
        self.connected_at = time.time()


# ── WebSocket-like framing over raw TCP ─────────────────────────────────
# We use asyncio websockets for the actual WS server.


class ZapServer:
    """ZAP WebSocket server for browser extension discovery."""

    def __init__(
        self,
        tools: list[dict[str, Any]],
        call_tool: Callable[[str, dict[str, Any]], Awaitable[Any]],
        name: str = "hanzo-mcp",
    ):
        self.tools = tools
        self.call_tool = call_tool
        self.name = name
        self.server_id = f"mcp-{int(time.time()):x}"
        self.clients: dict[Any, ZapClient] = {}
        self._server: Any = None
        self.port: int | None = None

        self.tool_manifest = [
            {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "inputSchema": t.get("inputSchema", t.get("input_schema", {})),
            }
            for t in self.tools
        ]

    async def _handle_connection(self, websocket: Any) -> None:
        """Handle a single WebSocket connection."""
        client: ZapClient | None = None
        try:
            async for raw in websocket:
                if isinstance(raw, str):
                    raw = raw.encode("utf-8")

                result = decode(raw)
                if result is None:
                    continue

                msg_type, payload = result

                if msg_type == MSG_HANDSHAKE:
                    client_id = payload.get("clientId", "unknown")
                    browser = payload.get("browser", "unknown")
                    version = payload.get("version", "0")
                    client = ZapClient(
                        writer=websocket,
                        client_id=client_id,
                        browser=browser,
                        version=version,
                    )
                    self.clients[websocket] = client
                    logger.info(
                        f"[ZAP] Client connected: {client_id} ({browser} v{version})"
                    )
                    await websocket.send(
                        encode(
                            MSG_HANDSHAKE_OK,
                            {
                                "serverId": self.server_id,
                                "name": self.name,
                                "tools": self.tool_manifest,
                            },
                        )
                    )

                elif msg_type == MSG_REQUEST:
                    req_id = payload.get("id", "")
                    method = payload.get("method", "")
                    params = payload.get("params", {})
                    await self._handle_request(websocket, req_id, method, params)

                elif msg_type == MSG_PING:
                    await websocket.send(encode(MSG_PONG, {}))

        except Exception as e:
            logger.debug(f"[ZAP] Connection error: {e}")
        finally:
            if websocket in self.clients:
                client = self.clients.pop(websocket)
                logger.info(f"[ZAP] Client disconnected: {client.client_id}")

    async def _handle_request(
        self, websocket: Any, req_id: str, method: str, params: Any
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

            elif method == "notifications/elementSelected":
                result = {"acknowledged": True}

            else:
                raise ValueError(f"Unknown method: {method}")

            await websocket.send(encode(MSG_RESPONSE, {"id": req_id, "result": result}))

        except Exception as e:
            await websocket.send(
                encode(
                    MSG_RESPONSE,
                    {
                        "id": req_id,
                        "error": {"code": -1, "message": str(e)},
                    },
                )
            )

    async def start(self, preferred_port: int | None = None) -> bool:
        """Start the ZAP server on the first available port."""
        try:
            import websockets
        except ImportError:
            logger.warning(
                "[ZAP] websockets package not installed. "
                "Install with: pip install websockets"
            )
            return False

        ports = (
            [preferred_port, *[p for p in ZAP_PORTS if p != preferred_port]]
            if preferred_port
            else ZAP_PORTS
        )

        for port in ports:
            try:
                self._server = await websockets.serve(
                    self._handle_connection,
                    "127.0.0.1",
                    port,
                )
                self.port = port
                logger.info(
                    f"[ZAP] Server listening on ws://127.0.0.1:{port} "
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
            for ws in list(self.clients.keys()):
                try:
                    asyncio.ensure_future(ws.close())
                except Exception:
                    pass
            self.clients.clear()


async def start_zap_server(
    tools: list[dict[str, Any]],
    call_tool: Callable[[str, dict[str, Any]], Awaitable[Any]],
    name: str = "hanzo-mcp",
    preferred_port: int | None = None,
) -> ZapServer | None:
    """Create and start a ZAP server.

    Args:
        tools: List of tool dicts with name, description, inputSchema.
        call_tool: Async callable (name, args) -> result to route tool calls.
        name: Server name for handshake.
        preferred_port: Preferred port to try first.

    Returns:
        ZapServer instance if started, None otherwise.
    """
    server = ZapServer(tools=tools, call_tool=call_tool, name=name)
    ok = await server.start(preferred_port=preferred_port)
    return server if ok else None
