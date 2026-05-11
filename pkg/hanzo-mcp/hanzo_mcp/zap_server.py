"""ZAP server adaptor for hanzo-mcp.

This module is a thin pass-through to ``hanzo_tools.browser.zap_server``,
which is the single source of truth for the ZAP wire protocol and the
WebSocket server hosted inside every hanzo-mcp process. Discovery is
mDNS-only (HIP-0069); the OS picks the port, mDNS carries it.

There is one and only one ZapServer implementation in the Python stack —
this module exists purely so existing callers that import
``hanzo_mcp.zap_server`` resolve to the canonical class.
"""

from __future__ import annotations

import logging

from hanzo_tools.browser.zap_server import (
    ZapServer,
    get_or_start_server,
    get_server,
    shutdown_server,
)

logger = logging.getLogger(__name__)


async def start_zap_server(
    tools,
    call_tool,
    handle_method=None,
    name: str = "hanzo-mcp",
    preferred_port=None,  # noqa: ARG001 — kept for legacy callers, ignored
):
    """Start (or reuse) the canonical ZAP server and wire MCP routing.

    Args:
        tools: List of tool dicts with name/description/inputSchema.
        call_tool: Async (name, args) -> result for tools/call dispatch.
        handle_method: Optional async (method, params) -> result for
            full MCP-method parity beyond tools/list and tools/call.
        name: Server name used in the handshake.
        preferred_port: Ignored — kept for API parity. Discovery is
            mDNS-only; the OS picks the port.

    Returns:
        The live ZapServer, or ``None`` if it could not start
        (websockets / zap-mdns missing).
    """
    server = await get_or_start_server(agent_label=name)
    if server is None:
        return None

    server.set_tools(list(tools))

    async def _on_request(method, params):
        if handle_method is not None:
            try:
                return await handle_method(method, params)
            except ValueError:
                # Fall through to defaults below.
                pass
        if method == "tools/list":
            return {"tools": list(tools)}
        if method == "tools/call":
            tool_name = (params or {}).get("name", "")
            args = (params or {}).get("arguments", {}) or {}
            if not tool_name:
                raise ValueError("Missing tool name")
            return await call_tool(tool_name, args)
        if method.startswith("notifications/"):
            return {"acknowledged": True}
        raise ValueError(f"unsupported method: {method}")

    server.set_request_handler(_on_request)
    logger.info(
        "hanzo-mcp ZAP transport up on :%d (%d tools)", server.port, len(list(tools))
    )
    return server


__all__ = [
    "ZapServer",
    "start_zap_server",
    "get_or_start_server",
    "get_server",
    "shutdown_server",
]
