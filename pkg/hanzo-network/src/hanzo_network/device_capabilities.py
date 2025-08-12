"""Device capabilities module for hanzo_network."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceCapabilities:
    """Represents the capabilities of a device in the network."""
    
    cpu_cores: int = 1
    memory_gb: float = 1.0
    gpu_available: bool = False
    gpu_memory_gb: Optional[float] = None
    network_bandwidth_mbps: float = 100.0
    storage_gb: float = 10.0
    
    def __post_init__(self):
        """Validate capabilities after initialization."""
        if self.cpu_cores < 1:
            raise ValueError("CPU cores must be at least 1")
        if self.memory_gb <= 0:
            raise ValueError("Memory must be positive")
        if self.gpu_available and self.gpu_memory_gb is None:
            self.gpu_memory_gb = 0.0
        if self.network_bandwidth_mbps <= 0:
            raise ValueError("Network bandwidth must be positive")
        if self.storage_gb <= 0:
            raise ValueError("Storage must be positive")
    
    def to_dict(self) -> dict:
        """Convert capabilities to dictionary."""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "gpu_available": self.gpu_available,
            "gpu_memory_gb": self.gpu_memory_gb,
            "network_bandwidth_mbps": self.network_bandwidth_mbps,
            "storage_gb": self.storage_gb,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeviceCapabilities":
        """Create capabilities from dictionary."""
        return cls(
            cpu_cores=data.get("cpu_cores", 1),
            memory_gb=data.get("memory_gb", 1.0),
            gpu_available=data.get("gpu_available", False),
            gpu_memory_gb=data.get("gpu_memory_gb"),
            network_bandwidth_mbps=data.get("network_bandwidth_mbps", 100.0),
            storage_gb=data.get("storage_gb", 10.0),
        )
    
    def can_handle_workload(self, required_memory_gb: float, required_cpu_cores: int = 1, requires_gpu: bool = False) -> bool:
        """Check if this device can handle a given workload."""
        if self.memory_gb < required_memory_gb:
            return False
        if self.cpu_cores < required_cpu_cores:
            return False
        if requires_gpu and not self.gpu_available:
            return False
        return True