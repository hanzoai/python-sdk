"""Simplified gRPC server for distributed Hanzo networks."""

from typing import Dict, Any


class GRPCServer:
    """Simplified gRPC server for agent network communication.

    This is a minimal implementation that simulates gRPC communication
    for testing purposes without requiring full gRPC infrastructure.
    """

    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.is_running = False
        self.handlers: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start the gRPC server."""
        self.is_running = True
        print(f"gRPC server started for node {self.node_id} on port {self.port}")

        # Register default handlers
        self.handlers["list_agents"] = self._handle_list_agents
        self.handlers["execute_agent"] = self._handle_execute_agent
        self.handlers["health_check"] = self._handle_health_check

    async def stop(self) -> None:
        """Stop the gRPC server."""
        self.is_running = False
        print(f"gRPC server stopped for node {self.node_id}")

    def register_handler(self, action: str, handler) -> None:
        """Register a handler for an action."""
        self.handlers[action] = handler

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming request."""
        if not self.is_running:
            return {"success": False, "error": "Server not running"}

        action = request.get("action")
        if not action:
            return {"success": False, "error": "No action specified"}

        handler = self.handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(request)
        except Exception as e:
            return {"success": False, "error": f"Handler error: {str(e)}"}

    async def _handle_list_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_agents request."""
        # This should be overridden by the network implementation
        return {"success": True, "agents": []}

    async def _handle_execute_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_agent request."""
        # This should be overridden by the network implementation
        return {"success": False, "error": "Not implemented"}

    async def _handle_health_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check request."""
        return {"success": True, "healthy": True, "node_id": self.node_id}
