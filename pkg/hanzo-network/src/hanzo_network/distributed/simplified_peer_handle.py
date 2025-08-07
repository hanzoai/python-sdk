"""Simplified peer handle for distributed networking without full inference support."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from ..topology.device_capabilities import DeviceCapabilities


class SimplifiedPeerHandle(ABC):
    """Simplified peer handle for basic distributed networking."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Get peer ID."""
        pass
    
    @property
    @abstractmethod
    def address(self) -> str:
        """Get peer address."""
        pass
    
    @property
    @abstractmethod 
    def device_capabilities(self) -> Optional[DeviceCapabilities]:
        """Get device capabilities."""
        pass
    
    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the peer."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if peer is connected."""
        pass
    
    def description(self) -> str:
        """Get peer description."""
        return f"{self.id} at {self.address}"