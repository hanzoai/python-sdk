"""Minimal discovery implementation for testing."""

from typing import List, Dict, Any, Optional
from .discovery import Discovery
from .simplified_peer_handle import SimplifiedPeerHandle
from ..device_capabilities import DeviceCapabilities


class MinimalPeerHandle(SimplifiedPeerHandle):
    """Minimal peer handle implementation."""
    
    def __init__(self, peer_id: str, address: str, capabilities: Optional[DeviceCapabilities] = None):
        self._id = peer_id
        self._address = address
        self._device_capabilities = capabilities
        self._connected = True
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def address(self) -> str:
        return self._address
    
    @property
    def device_capabilities(self) -> Optional[DeviceCapabilities]:
        return self._device_capabilities
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the peer."""
        # For testing, just echo back
        return {
            "success": True,
            "peer_id": self._id,
            "request": request,
            "response": f"Response from {self._id}"
        }
    
    async def is_connected(self) -> bool:
        return self._connected


class MinimalDiscovery(Discovery):
    """Minimal discovery for testing."""
    
    def __init__(self, node_id: str, device_capabilities: DeviceCapabilities, **kwargs):
        self.node_id = node_id
        self.device_capabilities = device_capabilities
        self.is_running = False
        self.discovered_peers: List[MinimalPeerHandle] = []
    
    async def start(self) -> None:
        """Start discovery."""
        self.is_running = True
        print(f"MinimalDiscovery started for node {self.node_id}")
    
    async def stop(self) -> None:
        """Stop discovery."""
        self.is_running = False
        print(f"MinimalDiscovery stopped for node {self.node_id}")
    
    async def discover_peers(self, wait_for_peers: int = 0) -> List[SimplifiedPeerHandle]:
        """Discover peers (returns empty list for now)."""
        # For testing, we don't actually discover peers
        # Real implementation would use UDP broadcast, mDNS, etc.
        return self.discovered_peers
    
    def add_test_peer(self, peer: MinimalPeerHandle) -> None:
        """Add a test peer manually."""
        self.discovered_peers.append(peer)