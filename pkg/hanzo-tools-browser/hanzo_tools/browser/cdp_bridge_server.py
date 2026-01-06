"""
CDP Bridge Server for Hanzo Browser Extension Integration.

This server acts as a bridge between:
1. hanzo-mcp's browser tool (Playwright) 
2. The Hanzo browser extension (Chrome/Firefox)

The browser extension connects via WebSocket, and hanzo-mcp can send
commands through the extension to control browser tabs.

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


class CDPBridgeServer:
    """WebSocket server that bridges hanzo-mcp and browser extension."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9223,
    ):
        self.host = host
        self.port = port
        self.extension_client: Optional[WebSocketServerProtocol] = None
        self.mcp_clients: set[WebSocketServerProtocol] = set()
        self.pending_requests: dict[int, asyncio.Future] = {}
        self.request_id = 0
        self._server = None
        
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
                    # This is the browser extension
                    self.extension_client = websocket
                    logger.info("Browser extension registered as CDP provider")
                    
                    # Notify MCP clients
                    for client in self.mcp_clients:
                        await client.send(json.dumps({
                            "type": "provider_connected",
                            "capabilities": data.get("capabilities", [])
                        }))
                        
                elif role == "mcp-client":
                    # This is hanzo-mcp or another MCP tool
                    self.mcp_clients.add(websocket)
                    logger.info("MCP client connected")
                    
                    # Let client know if extension is connected
                    await websocket.send(json.dumps({
                        "type": "status",
                        "extension_connected": self.extension_client is not None
                    }))
            
            # Handle subsequent messages
            async for message in websocket:
                await self._route_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {websocket.remote_address}")
        finally:
            # Clean up
            if websocket == self.extension_client:
                self.extension_client = None
                # Notify MCP clients
                for client in self.mcp_clients:
                    try:
                        await client.send(json.dumps({
                            "type": "provider_disconnected"
                        }))
                    except Exception:
                        pass
            elif websocket in self.mcp_clients:
                self.mcp_clients.discard(websocket)
                
    async def _route_message(
        self,
        sender: WebSocketServerProtocol,
        message: str,
    ) -> None:
        """Route messages between extension and MCP clients."""
        data = json.loads(message)
        
        if sender == self.extension_client:
            # Message from extension (response or event)
            if "id" in data and data["id"] in self.pending_requests:
                # This is a response to a pending request
                future = self.pending_requests.pop(data["id"])
                future.set_result(data)
            elif data.get("type") == "event":
                # Broadcast event to all MCP clients
                for client in self.mcp_clients:
                    try:
                        await client.send(message)
                    except Exception:
                        pass
                        
        elif sender in self.mcp_clients:
            # Message from MCP client (command)
            if not self.extension_client:
                # No extension connected
                await sender.send(json.dumps({
                    "id": data.get("id"),
                    "error": {
                        "code": -32000,
                        "message": "Browser extension not connected"
                    }
                }))
                return
                
            # Forward to extension and wait for response
            request_id = data.get("id", self._next_request_id())
            data["id"] = request_id
            
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            self.pending_requests[request_id] = future
            
            try:
                await self.extension_client.send(json.dumps(data))
                
                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=30.0)
                await sender.send(json.dumps(response))
                
            except asyncio.TimeoutError:
                self.pending_requests.pop(request_id, None)
                await sender.send(json.dumps({
                    "id": request_id,
                    "error": {
                        "code": -32001,
                        "message": "Request timeout"
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
            
    async def send(self, method: str, params: dict = None) -> Any:
        """Send a CDP command and wait for response."""
        if not self._websocket:
            raise Exception("Not connected to CDP bridge")
            
        self._request_id += 1
        request_id = self._request_id
        
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        
        await self._websocket.send(json.dumps({
            "id": request_id,
            "method": method,
            "params": params or {}
        }))
        
        return await asyncio.wait_for(future, timeout=30.0)
        
    def on_event(self, handler: Callable) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)
        
    # High-level commands
    
    async def navigate(self, url: str, tab_id: int = None) -> None:
        """Navigate to a URL."""
        await self.send("Page.navigate", {"url": url, "tabId": tab_id})
        
    async def screenshot(
        self,
        tab_id: int = None,
        full_page: bool = False,
        format: str = "png",
    ) -> str:
        """Take a screenshot, returns base64 data."""
        result = await self.send("hanzo.screenshot", {
            "tabId": tab_id,
            "fullPage": full_page,
            "format": format
        })
        return result.get("data", "")
        
    async def click(self, selector: str, tab_id: int = None) -> bool:
        """Click an element by selector."""
        result = await self.send("hanzo.click", {
            "selector": selector,
            "tabId": tab_id
        })
        return result.get("success", False)
        
    async def fill(self, selector: str, value: str, tab_id: int = None) -> bool:
        """Fill an input element."""
        result = await self.send("hanzo.fill", {
            "selector": selector,
            "value": value,
            "tabId": tab_id
        })
        return result.get("success", False)
        
    async def evaluate(self, expression: str, tab_id: int = None) -> Any:
        """Evaluate JavaScript in the page."""
        return await self.send("Runtime.evaluate", {
            "expression": expression,
            "tabId": tab_id
        })


async def main():
    """Run the CDP bridge server."""
    host = os.environ.get("HANZO_CDP_BRIDGE_HOST", "localhost")
    port = int(os.environ.get("HANZO_CDP_BRIDGE_PORT", "9223"))
    
    server = CDPBridgeServer(host=host, port=port)
    await server.start()
    
    print(f"CDP Bridge Server running on ws://{host}:{port}")
    print("Waiting for browser extension to connect...")
    print("Press Ctrl+C to stop")
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down...")
        await server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
