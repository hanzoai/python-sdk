"""
ZAP Cloud Client — speaks the luxfi/zap binary wire protocol.

Connects to Hanzo Node (port 3692) or Engine via native binary transport.
Compatible with the Rust `hanzo-zap` crate server.

Example:
    >>> from hanzo_zap import CloudClient
    >>> async with CloudClient.connect("localhost:3692") as client:
    ...     status, body, error = await client.call("chat.completions", "", body_bytes)
"""

from __future__ import annotations

import asyncio
import json
import ssl
import struct
from typing import Any

from .wire import (
    REQ_FLAG_REQ,
    REQ_FLAG_RESP,
    Message,
    build_cloud_request,
    build_handshake,
    parse_cloud_response,
    parse_handshake,
    read_frame,
    write_frame,
)

DEFAULT_ENDPOINT = "localhost:3692"
CLIENT_NODE_ID = "python-sdk"


class CloudClient:
    """
    A client that speaks the luxfi/zap binary wire protocol.

    Supports both plain TCP (localhost) and TLS (remote endpoints).
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        peer_id: str,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._peer_id = peer_id
        self._req_id = 0

    @classmethod
    async def connect(
        cls,
        endpoint: str | None = None,
        *,
        use_tls: bool | None = None,
        node_id: str = CLIENT_NODE_ID,
    ) -> "CloudClient":
        """
        Connect to a ZAP endpoint, perform handshake.

        Args:
            endpoint: "host:port" (default: localhost:3692)
            use_tls: Force TLS on/off. None = auto-detect (TLS for non-localhost).
            node_id: Client node ID for handshake.
        """
        addr = endpoint or DEFAULT_ENDPOINT
        host, _, port_str = addr.rpartition(":")
        if not host:
            host = addr
            port_str = "3692"
        port = int(port_str)

        # Auto-detect TLS: skip for localhost
        if use_tls is None:
            use_tls = host not in ("localhost", "127.0.0.1", "::1")

        ssl_ctx = None
        if use_tls:
            ssl_ctx = ssl.create_default_context()

        reader, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx)

        # Send handshake
        hs_bytes = build_handshake(node_id)
        await write_frame(writer, hs_bytes)

        # Read handshake response
        resp_data = await read_frame(reader)
        resp_msg = Message.parse(resp_data)
        peer_id = parse_handshake(resp_msg)

        return cls(reader, writer, peer_id)

    @property
    def peer_id(self) -> str:
        return self._peer_id

    async def call(
        self,
        method: str,
        auth: str,
        body: bytes,
    ) -> tuple[int, bytes, str]:
        """
        Send a MsgType 100 cloud service request and return (status, body, error).
        """
        self._req_id += 1
        req_id = self._req_id

        # Build ZAP message
        msg_bytes = build_cloud_request(method, auth, body)

        # Wrap with 8-byte Call correlation header
        wrapped = struct.pack("<II", req_id, REQ_FLAG_REQ) + msg_bytes

        # Send
        await write_frame(self._writer, wrapped)

        # Read response — loop until we match our req_id
        while True:
            data = await read_frame(self._reader)
            if len(data) < 8:
                continue

            resp_id, resp_flag = struct.unpack_from("<II", data, 0)
            if resp_flag != REQ_FLAG_RESP:
                continue
            if resp_id != req_id:
                continue

            # Parse ZAP message (skip 8-byte Call header)
            msg = Message.parse(data[8:])
            return parse_cloud_response(msg)

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        auth_token: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        High-level: send an OpenAI-compatible chat completion request via ZAP.

        Returns the parsed JSON response dict.
        """
        request_body: dict[str, Any] = {"model": model, "messages": messages}
        request_body.update(kwargs)

        body_bytes = json.dumps(request_body).encode("utf-8")
        auth = f"Bearer {auth_token}" if auth_token and not auth_token.startswith("Bearer ") else auth_token

        status, resp_body, error = await self.call("chat.completions", auth, body_bytes)

        if status != 200:
            err_msg = error or resp_body.decode("utf-8", errors="replace") or f"ZAP status {status}"
            raise RuntimeError(f"ZAP cloud error: {err_msg}")

        return json.loads(resp_body)

    async def close(self) -> None:
        """Close the connection."""
        self._writer.close()
        await self._writer.wait_closed()

    async def __aenter__(self) -> "CloudClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
