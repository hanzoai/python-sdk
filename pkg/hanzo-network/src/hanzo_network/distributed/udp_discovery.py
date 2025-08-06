"""UDP-based peer discovery for distributed Hanzo networks."""

import asyncio
import json
import socket
import time
from typing import List, Dict, Tuple

from hanzo_network.distributed.discovery import Discovery
from hanzo_network.distributed.minimal_discovery import MinimalPeerHandle
from hanzo_network.topology.device_capabilities import DeviceCapabilities


def get_broadcast_address(ip_addr: str) -> str:
    """Get broadcast address for a given IP."""
    try:
        # Split IP into octets and create broadcast address for the subnet
        ip_parts = ip_addr.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.255"
    except:
        return "255.255.255.255"


def get_local_ip() -> str:
    """Get the local IP address."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


class ListenProtocol(asyncio.DatagramProtocol):
    """Protocol for listening to UDP broadcasts."""
    
    def __init__(self, on_message):
        super().__init__()
        self.on_message = on_message
        self.loop = asyncio.get_event_loop()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        asyncio.create_task(self.on_message(data, addr))


class BroadcastProtocol(asyncio.DatagramProtocol):
    """Protocol for broadcasting UDP messages."""
    
    def __init__(self, message: str, broadcast_port: int, source_ip: str):
        self.message = message
        self.broadcast_port = broadcast_port
        self.source_ip = source_ip

    def connection_made(self, transport):
        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Try both subnet-specific and global broadcast
        broadcast_addr = get_broadcast_address(self.source_ip)
        transport.sendto(self.message.encode("utf-8"), (broadcast_addr, self.broadcast_port))
        if broadcast_addr != "255.255.255.255":
            transport.sendto(self.message.encode("utf-8"), ("255.255.255.255", self.broadcast_port))
        transport.close()


class UDPDiscovery(Discovery):
    """UDP-based discovery for finding peers on the local network."""
    
    def __init__(
        self,
        node_id: str,
        device_capabilities: DeviceCapabilities,
        listen_port: int = 5678,
        broadcast_port: int = 5678,
        broadcast_interval: float = 2.5,
        discovery_timeout: float = 30.0,
        **kwargs
    ):
        self.node_id = node_id
        self.device_capabilities = device_capabilities
        self.listen_port = listen_port
        self.broadcast_port = broadcast_port
        self.broadcast_interval = broadcast_interval
        self.discovery_timeout = discovery_timeout
        
        # Track known peers: peer_id -> (peer_handle, first_seen, last_seen)
        self.known_peers: Dict[str, Tuple[MinimalPeerHandle, float, float]] = {}
        
        # Background tasks
        self.broadcast_task = None
        self.listen_task = None
        self.cleanup_task = None
        self.is_running = False
        
        # Local IP
        self.local_ip = get_local_ip()
        
    async def start(self) -> None:
        """Start UDP discovery."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start background tasks
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        self.listen_task = asyncio.create_task(self._listen_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        print(f"UDP Discovery started for node {self.node_id} on port {self.listen_port}")
        
    async def stop(self) -> None:
        """Stop UDP discovery."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Cancel tasks
        for task in [self.broadcast_task, self.listen_task, self.cleanup_task]:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        if any([self.broadcast_task, self.listen_task, self.cleanup_task]):
            await asyncio.gather(
                self.broadcast_task, 
                self.listen_task, 
                self.cleanup_task, 
                return_exceptions=True
            )
        
        print(f"UDP Discovery stopped for node {self.node_id}")
        
    async def discover_peers(self, wait_for_peers: int = 0) -> List[MinimalPeerHandle]:
        """Discover peers on the network."""
        if wait_for_peers > 0:
            # Wait until we have enough peers
            start_time = time.time()
            while len(self.known_peers) < wait_for_peers:
                if time.time() - start_time > 30:  # 30 second timeout
                    print(f"Timeout waiting for {wait_for_peers} peers, found {len(self.known_peers)}")
                    break
                await asyncio.sleep(0.1)
        
        return [peer_handle for peer_handle, _, _ in self.known_peers.values()]
    
    async def _broadcast_loop(self) -> None:
        """Broadcast presence to network."""
        while self.is_running:
            try:
                # Create discovery message
                message = json.dumps({
                    "type": "discovery",
                    "node_id": self.node_id,
                    "listen_port": self.listen_port,
                    "device_capabilities": self.device_capabilities.to_dict() if self.device_capabilities else {},
                    "timestamp": time.time()
                })
                
                # Create socket and broadcast
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except AttributeError:
                    pass  # Not available on all platforms
                sock.bind((self.local_ip, 0))
                
                transport, _ = await asyncio.get_event_loop().create_datagram_endpoint(
                    lambda: BroadcastProtocol(message, self.broadcast_port, self.local_ip),
                    sock=sock
                )
                
                await asyncio.sleep(0.1)  # Give time for broadcast
                
            except Exception as e:
                print(f"Error in broadcast loop: {e}")
            
            await asyncio.sleep(self.broadcast_interval)
    
    async def _listen_loop(self) -> None:
        """Listen for discovery broadcasts."""
        try:
            await asyncio.get_event_loop().create_datagram_endpoint(
                lambda: ListenProtocol(self._handle_discovery_message),
                local_addr=("0.0.0.0", self.listen_port)
            )
            print(f"Listening for peers on port {self.listen_port}")
            
            # Keep the task running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error in listen loop: {e}")
    
    async def _handle_discovery_message(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming discovery message."""
        try:
            # Decode message
            message = json.loads(data.decode("utf-8"))
            
            # Check if it's a discovery message
            if message.get("type") != "discovery":
                return
            
            peer_id = message.get("node_id")
            if not peer_id or peer_id == self.node_id:
                return  # Ignore our own broadcasts
            
            # Extract peer info
            peer_host = addr[0]
            peer_port = message.get("listen_port", 5678)
            peer_caps_dict = message.get("device_capabilities", {})
            
            # Create device capabilities if provided
            peer_caps = None
            if peer_caps_dict:
                try:
                    peer_caps = DeviceCapabilities(**peer_caps_dict)
                except:
                    pass
            
            # Create or update peer
            current_time = time.time()
            peer_address = f"{peer_host}:{peer_port}"
            
            if peer_id not in self.known_peers:
                # New peer discovered
                peer_handle = MinimalPeerHandle(
                    peer_id=peer_id,
                    address=peer_address,
                    capabilities=peer_caps
                )
                self.known_peers[peer_id] = (peer_handle, current_time, current_time)
                print(f"Discovered new peer: {peer_id} at {peer_address}")
            else:
                # Update last seen time
                peer_handle, first_seen, _ = self.known_peers[peer_id]
                self.known_peers[peer_id] = (peer_handle, first_seen, current_time)
                
        except Exception as e:
            print(f"Error handling discovery message from {addr}: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Clean up stale peers."""
        while self.is_running:
            try:
                current_time = time.time()
                peers_to_remove = []
                
                # Check each peer
                for peer_id, (peer_handle, first_seen, last_seen) in self.known_peers.items():
                    # Remove if not seen recently
                    if current_time - last_seen > self.discovery_timeout:
                        peers_to_remove.append(peer_id)
                
                # Remove stale peers
                for peer_id in peers_to_remove:
                    del self.known_peers[peer_id]
                    print(f"Removed stale peer: {peer_id}")
                    
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
            
            await asyncio.sleep(self.broadcast_interval)