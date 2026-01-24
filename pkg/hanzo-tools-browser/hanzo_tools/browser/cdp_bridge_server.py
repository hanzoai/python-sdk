"""
CDP Bridge Server for Hanzo Browser Extension Integration.

This server acts as a bridge between:
1. hanzo-mcp's browser tool (Playwright)
2. The Hanzo browser extension (Chrome/Firefox)

MULTI-CLIENT SUPPORT:
- Multiple browser extensions can connect simultaneously
- Each client has a unique client_id (uuid sent on registration)
- Target IDs are namespaced: "<client_id>:<tab_id>"
- Commands can specify client_id or target_id for routing
- Default client = most recently active

Usage:
    # Start the bridge server (typically on port 9223)
    python -m hanzo_tools.browser.cdp_bridge_server

    # Or programmatically
    from hanzo_tools.browser.cdp_bridge_server import CDPBridgeServer
    server = CDPBridgeServer(port=9223)
    await server.start()

Environment Variables:
    HANZO_CDP_BRIDGE_PORT: Port for the WebSocket server (default: 9223)
    HANZO_CDP_BRIDGE_HOST: Host to bind to (default: localhost)
"""

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

try:
    import websockets
    from websockets.server import serve as ws_serve
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any

logger = logging.getLogger(__name__)


@dataclass
class ExtensionClient:
    """Represents a connected browser extension client."""
    client_id: str
    websocket: WebSocketServerProtocol
    browser: str = "unknown"
    profile: str = "default"
    user_agent: str = ""
    capabilities: list = field(default_factory=list)
    connected_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "browser": self.browser,
            "profile": self.profile,
            "capabilities": self.capabilities,
            "connected_at": self.connected_at,
            "last_active": self.last_active,
        }


class CDPBridgeServer:
    """WebSocket server that bridges hanzo-mcp and browser extensions.

    Supports multiple browser extension clients simultaneously.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9223,
    ):
        self.host = host
        self.port = port

        # Multi-client registry: client_id -> ExtensionClient
        self.extension_clients: dict[str, ExtensionClient] = {}
        # Reverse lookup: websocket -> client_id
        self._ws_to_client_id: dict[WebSocketServerProtocol, str] = {}

        self.mcp_clients: set[WebSocketServerProtocol] = set()
        self.pending_requests: dict[int, asyncio.Future] = {}
        self.request_id = 0
        self._server = None

    @property
    def default_client_id(self) -> Optional[str]:
        """Get the default client (most recently active)."""
        if not self.extension_clients:
            return None
        # Return the client with most recent last_active timestamp
        return max(
            self.extension_clients.keys(),
            key=lambda cid: self.extension_clients[cid].last_active
        )

    @property
    def default_client(self) -> Optional[ExtensionClient]:
        """Get the default ExtensionClient."""
        cid = self.default_client_id
        return self.extension_clients.get(cid) if cid else None

    async def start(self) -> None:
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package required for CDP bridge. "
                "Install with: pip install websockets"
            )

        self._server = await ws_serve(
            self._handle_connection,
            self.host,
            self.port,
        )
        logger.info(f"CDP Bridge Server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("CDP Bridge Server stopped")

    async def _handle_connection(
        self,
        websocket: WebSocketServerProtocol,
        path: str,
    ) -> None:
        """Handle incoming WebSocket connections."""
        logger.info(f"New connection from {websocket.remote_address} on {path}")

        try:
            # First message identifies the client type
            message = await websocket.recv()
            data = json.loads(message)

            if data.get("type") == "register":
                role = data.get("role")

                if role == "cdp-provider":
                    # This is a browser extension
                    # Client can provide its own ID or we generate one
                    client_id = data.get("client_id") or str(uuid.uuid4())[:8]

                    client = ExtensionClient(
                        client_id=client_id,
                        websocket=websocket,
                        browser=data.get("browser", "unknown"),
                        profile=data.get("profile", "default"),
                        user_agent=data.get("userAgent", ""),
                        capabilities=data.get("capabilities", []),
                    )

                    self.extension_clients[client_id] = client
                    self._ws_to_client_id[websocket] = client_id

                    logger.info(
                        f"Browser extension registered: {client_id} "
                        f"({client.browser}/{client.profile})"
                    )

                    # Send back the assigned client_id
                    await websocket.send(json.dumps({
                        "type": "registered",
                        "client_id": client_id,
                    }))

                    # Notify MCP clients
                    for mcp in self.mcp_clients:
                        await mcp.send(json.dumps({
                            "type": "provider_connected",
                            "client_id": client_id,
                            "browser": client.browser,
                            "profile": client.profile,
                            "capabilities": client.capabilities,
                            "total_clients": len(self.extension_clients),
                        }))

                elif role == "mcp-client":
                    # This is hanzo-mcp or another MCP tool
                    self.mcp_clients.add(websocket)
                    logger.info("MCP client connected")

                    # Send status with all connected clients
                    await websocket.send(json.dumps({
                        "type": "status",
                        "connected": len(self.extension_clients) > 0,
                        "clients": [c.to_dict() for c in self.extension_clients.values()],
                        "default_client_id": self.default_client_id,
                    }))

            # Handle subsequent messages
            async for message in websocket:
                await self._route_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {websocket.remote_address}")
        finally:
            # Clean up
            if websocket in self._ws_to_client_id:
                client_id = self._ws_to_client_id.pop(websocket)
                self.extension_clients.pop(client_id, None)
                logger.info(f"Extension client disconnected: {client_id}")

                # Notify MCP clients
                for mcp in self.mcp_clients:
                    try:
                        await mcp.send(json.dumps({
                            "type": "provider_disconnected",
                            "client_id": client_id,
                            "remaining_clients": len(self.extension_clients),
                        }))
                    except Exception:
                        pass

            elif websocket in self.mcp_clients:
                self.mcp_clients.discard(websocket)

    def _resolve_client(
        self,
        client_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Optional[ExtensionClient]:
        """Resolve which client to route to.

        Args:
            client_id: Explicit client ID
            target_id: Namespaced target like "clientid:tabid"

        Returns:
            ExtensionClient or None
        """
        # Parse target_id if provided (format: "client_id:tab_id")
        if target_id and ":" in target_id:
            cid = target_id.split(":")[0]
            if cid in self.extension_clients:
                return self.extension_clients[cid]

        # Use explicit client_id
        if client_id and client_id in self.extension_clients:
            return self.extension_clients[client_id]

        # Fall back to default (most recently active)
        return self.default_client

    async def _route_message(
        self,
        sender: WebSocketServerProtocol,
        message: str,
    ) -> None:
        """Route messages between extensions and MCP clients."""
        data = json.loads(message)

        # Check if message is from an extension
        if sender in self._ws_to_client_id:
            client_id = self._ws_to_client_id[sender]
            # Update last_active
            if client_id in self.extension_clients:
                self.extension_clients[client_id].last_active = time.time()

            # Message from extension (response or event)
            if "id" in data and data["id"] in self.pending_requests:
                # This is a response to a pending request
                future = self.pending_requests.pop(data["id"])
                # Add source client_id to response
                data["_client_id"] = client_id
                future.set_result(data)
            elif data.get("type") == "event":
                # Add source client_id to event
                data["_client_id"] = client_id
                # Broadcast event to all MCP clients
                for mcp in self.mcp_clients:
                    try:
                        await mcp.send(json.dumps(data))
                    except Exception:
                        pass

        elif sender in self.mcp_clients:
            # Message from MCP client (command)
            # Resolve target client
            target_client = self._resolve_client(
                client_id=data.get("client_id"),
                target_id=data.get("target_id"),
            )

            if not target_client:
                # No extension connected or specified client not found
                await sender.send(json.dumps({
                    "id": data.get("id"),
                    "error": {
                        "code": -32000,
                        "message": "No browser extension connected"
                            if not self.extension_clients
                            else f"Client not found: {data.get('client_id') or data.get('target_id')}"
                    }
                }))
                return

            # Update target client's last_active
            target_client.last_active = time.time()

            # Forward to target extension and wait for response
            request_id = data.get("id", self._next_request_id())
            data["id"] = request_id

            future: asyncio.Future = asyncio.get_event_loop().create_future()
            self.pending_requests[request_id] = future

            try:
                await target_client.websocket.send(json.dumps(data))

                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=30.0)
                # Include client_id in response
                response["client_id"] = target_client.client_id
                await sender.send(json.dumps(response))

            except asyncio.TimeoutError:
                self.pending_requests.pop(request_id, None)
                await sender.send(json.dumps({
                    "id": request_id,
                    "error": {
                        "code": -32001,
                        "message": f"Request timeout (client: {target_client.client_id})"
                    }
                }))
            except Exception as e:
                self.pending_requests.pop(request_id, None)
                await sender.send(json.dumps({
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }))

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self.request_id += 1
        return self.request_id


class CDPBridgeClient:
    """Client for connecting to CDP Bridge Server from hanzo-mcp."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9223,
    ):
        self.host = host
        self.port = port
        self._websocket: Optional[WebSocketServerProtocol] = None
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._event_handlers: list[Callable] = []
        self._clients: list[dict] = []
        self._default_client_id: Optional[str] = None

    @property
    def clients(self) -> list[dict]:
        """List of connected browser extension clients."""
        return self._clients

    @property
    def default_client_id(self) -> Optional[str]:
        """ID of the default (most recently active) client."""
        return self._default_client_id

    async def connect(self) -> bool:
        """Connect to the CDP bridge server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets not available, CDP bridge disabled")
            return False

        try:
            import websockets
            uri = f"ws://{self.host}:{self.port}/cdp"
            self._websocket = await websockets.connect(uri)

            # Register as MCP client
            await self._websocket.send(json.dumps({
                "type": "register",
                "role": "mcp-client"
            }))

            # Wait for status response
            status_msg = await self._websocket.recv()
            status = json.loads(status_msg)
            if status.get("type") == "status":
                self._clients = status.get("clients", [])
                self._default_client_id = status.get("default_client_id")

            # Start message handler
            asyncio.create_task(self._message_loop())

            logger.info(f"Connected to CDP bridge at {uri}")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to CDP bridge: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the bridge server."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def _message_loop(self) -> None:
        """Process incoming messages."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                data = json.loads(message)

                # Handle status updates
                if data.get("type") == "provider_connected":
                    # New client connected
                    self._clients.append({
                        "client_id": data.get("client_id"),
                        "browser": data.get("browser"),
                        "profile": data.get("profile"),
                        "capabilities": data.get("capabilities"),
                    })
                elif data.get("type") == "provider_disconnected":
                    # Client disconnected
                    cid = data.get("client_id")
                    self._clients = [c for c in self._clients if c.get("client_id") != cid]

                # Handle responses
                if "id" in data and data["id"] in self._pending:
                    future = self._pending.pop(data["id"])
                    if "error" in data:
                        future.set_exception(Exception(data["error"]["message"]))
                    else:
                        future.set_result(data.get("result"))

                elif data.get("type") == "event":
                    for handler in self._event_handlers:
                        try:
                            handler(data)
                        except Exception:
                            pass

        except Exception as e:
            logger.error(f"Message loop error: {e}")

    async def send(
        self,
        method: str,
        params: dict = None,
        client_id: str = None,
        target_id: str = None,
    ) -> Any:
        """Send a CDP command and wait for response.

        Args:
            method: CDP method name
            params: Method parameters
            client_id: Optional specific client to target
            target_id: Optional namespaced target (client_id:tab_id)

        Returns:
            Result from the extension
        """
        if not self._websocket:
            raise Exception("Not connected to CDP bridge")

        self._request_id += 1
        request_id = self._request_id

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future

        payload = {
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        # Add routing hints
        if client_id:
            payload["client_id"] = client_id
        if target_id:
            payload["target_id"] = target_id

        await self._websocket.send(json.dumps(payload))

        return await asyncio.wait_for(future, timeout=30.0)

    def on_event(self, handler: Callable) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    # High-level commands

    async def navigate(
        self,
        url: str,
        tab_id: int = None,
        client_id: str = None,
    ) -> None:
        """Navigate to a URL."""
        await self.send(
            "Page.navigate",
            {"url": url, "tabId": tab_id},
            client_id=client_id,
        )

    async def screenshot(
        self,
        tab_id: int = None,
        full_page: bool = False,
        format: str = "png",
        client_id: str = None,
    ) -> str:
        """Take a screenshot, returns base64 data."""
        result = await self.send(
            "hanzo.screenshot",
            {"tabId": tab_id, "fullPage": full_page, "format": format},
            client_id=client_id,
        )
        return result.get("data", "")

    async def click(
        self,
        selector: str,
        tab_id: int = None,
        client_id: str = None,
    ) -> bool:
        """Click an element by selector."""
        result = await self.send(
            "hanzo.click",
            {"selector": selector, "tabId": tab_id},
            client_id=client_id,
        )
        return result.get("success", False)

    async def fill(
        self,
        selector: str,
        value: str,
        tab_id: int = None,
        client_id: str = None,
    ) -> bool:
        """Fill an input element."""
        result = await self.send(
            "hanzo.fill",
            {"selector": selector, "value": value, "tabId": tab_id},
            client_id=client_id,
        )
        return result.get("success", False)

    async def evaluate(
        self,
        expression: str,
        tab_id: int = None,
        client_id: str = None,
    ) -> Any:
        """Evaluate JavaScript in the page."""
        return await self.send(
            "Runtime.evaluate",
            {"expression": expression, "tabId": tab_id},
            client_id=client_id,
        )

    async def list_clients(self) -> list[dict]:
        """Get list of connected browser extension clients."""
        # Refresh from server
        result = await self.send("hanzo.listClients", {})
        return result.get("clients", self._clients)


async def main():
    """Run the CDP bridge server."""
    host = os.environ.get("HANZO_CDP_BRIDGE_HOST", "localhost")
    port = int(os.environ.get("HANZO_CDP_BRIDGE_PORT", "9223"))

    server = CDPBridgeServer(host=host, port=port)
    await server.start()

    print(f"CDP Bridge Server running on ws://{host}:{port}")
    print("Waiting for browser extension(s) to connect...")
    print("Supports multiple browsers simultaneously")
    print("Press Ctrl+C to stop")

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down...")
        await server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
