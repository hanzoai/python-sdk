"""Distributed Network implementation using Hanzo Net infrastructure."""

import asyncio
from typing import Any, Dict, List, Optional, Union, TypeVar
from dataclasses import dataclass

from .core.network import Network, NetworkConfig
from .core.agent import Agent
from .core.router import Router, RouterFunction, RoutingAgent
from .core.state import NetworkState
from .distributed.discovery import Discovery
from .distributed.simplified_peer_handle import SimplifiedPeerHandle as PeerHandle
from .distributed.udp_discovery import UDPDiscovery
from .distributed.grpc_server import GRPCServer
from .topology.device_capabilities import DeviceCapabilities, device_capabilities


T = TypeVar("T")


@dataclass
class DistributedNetworkConfig(NetworkConfig[T]):
    """Configuration for a distributed network."""

    discovery_method: str = "udp"  # udp, manual, tailscale
    listen_port: int = 5678
    broadcast_port: int = 5678
    node_id: Optional[str] = None
    device_capabilities: Optional[DeviceCapabilities] = None


class DistributedNetwork(Network[T]):
    """A distributed network of agents across multiple nodes.

    Extends the base Network with:
    - Automatic peer discovery
    - Distributed agent execution
    - Cross-node state synchronization
    - Load balancing across nodes
    """

    def __init__(self, config: DistributedNetworkConfig[T]):
        """Initialize distributed network with configuration."""
        super().__init__(config)

        self.discovery_method = config.discovery_method
        self.listen_port = config.listen_port
        self.broadcast_port = config.broadcast_port
        self.node_id = config.node_id or self._generate_node_id()
        self.device_capabilities = config.device_capabilities or device_capabilities()

        # Discovery and networking
        self.discovery: Optional[Discovery] = None
        self.grpc_server: Optional[GRPCServer] = None
        self.peers: List[PeerHandle] = []
        self.peer_agents: Dict[str, List[Agent]] = {}  # peer_id -> agents

        # Distributed state
        self.is_running = False
        self.sync_task = None

    async def start(self, wait_for_peers: int = 0) -> None:
        """Start the distributed network node.

        Args:
            wait_for_peers: Number of peers to wait for before starting
        """
        if self.is_running:
            return

        # Initialize discovery based on method
        if self.discovery_method == "udp":
            self.discovery = UDPDiscovery(
                node_id=self.node_id,
                device_capabilities=self.device_capabilities,
                listen_port=self.listen_port,
                broadcast_port=self.broadcast_port,
            )
        # Add other discovery methods as needed

        # Start discovery
        await self.discovery.start()

        # Start GRPC server for peer communication
        self.grpc_server = GRPCServer(node_id=self.node_id, port=self.listen_port)

        # Register handlers for distributed operations
        self.grpc_server.register_handler("list_agents", self._handle_list_agents)
        self.grpc_server.register_handler("execute_agent", self._handle_execute_agent)

        await self.grpc_server.start()

        # Discover initial peers
        self.peers = await self.discovery.discover_peers(wait_for_peers)

        # Start state synchronization
        self.sync_task = asyncio.create_task(self._sync_loop())

        self.is_running = True
        print(
            f"Distributed network node {self.node_id} started with {len(self.peers)} peers"
        )

    async def stop(self) -> None:
        """Stop the distributed network node."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop sync
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        # Stop servers
        if self.grpc_server:
            await self.grpc_server.stop()

        if self.discovery:
            await self.discovery.stop()

        print(f"Distributed network node {self.node_id} stopped")

    async def run(
        self,
        prompt: str,
        initial_agent: Optional[Agent] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the distributed network with a user prompt.

        This extends the base run method to support distributed execution.
        """
        if not self.is_running:
            await self.start()

        # Add distributed context
        dist_context = {
            "node_id": self.node_id,
            "peer_count": len(self.peers),
            "distributed": True,
            **(context or {}),
        }

        # Check if we need to execute on a remote node
        if initial_agent and not self._is_local_agent(initial_agent):
            # Find peer with this agent
            peer_id = self._find_peer_with_agent(initial_agent.name)
            if peer_id:
                peer = self._get_peer(peer_id)
                if peer:
                    # Execute remotely
                    return await self._execute_remote(
                        peer, prompt, initial_agent, dist_context
                    )

        # Execute locally (using base implementation)
        return await super().run(prompt, initial_agent, dist_context)

    async def _execute_remote(
        self, peer: PeerHandle, prompt: str, agent: Agent, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an agent on a remote peer."""
        try:
            # Send execution request to peer
            request = {
                "action": "execute_agent",
                "agent_name": agent.name,
                "prompt": prompt,
                "context": context,
                "state": self.state.to_dict(),
            }

            response = await peer.send_request(request)

            # Update local state with remote results
            if response.get("state"):
                self.state.from_dict(response["state"])

            return response

        except Exception as e:
            return {"success": False, "error": f"Remote execution failed: {str(e)}"}

    async def _sync_loop(self) -> None:
        """Background task to sync state with peers."""
        while self.is_running:
            try:
                # Discover new peers
                new_peers = await self.discovery.discover_peers()
                self._update_peers(new_peers)

                # Sync agent information
                for peer in self.peers:
                    try:
                        # Get peer's agents
                        response = await peer.send_request({"action": "list_agents"})

                        if response.get("agents"):
                            self.peer_agents[peer.id] = response["agents"]
                    except Exception:
                        pass

                # Wait before next sync
                await asyncio.sleep(5)

            except Exception as e:
                if self.is_running:
                    print(f"Sync error: {e}")
                    await asyncio.sleep(5)

    def _update_peers(self, new_peers: List[PeerHandle]) -> None:
        """Update peer list with newly discovered peers."""
        # Add new peers
        existing_ids = {p.id for p in self.peers}
        for peer in new_peers:
            if peer.id not in existing_ids:
                self.peers.append(peer)
                print(f"New peer discovered: {peer.id}")

    def _is_local_agent(self, agent: Agent) -> bool:
        """Check if an agent is available locally."""
        return agent.name in self.agent_map

    def _find_peer_with_agent(self, agent_name: str) -> Optional[str]:
        """Find which peer has a specific agent."""
        for peer_id, agents in self.peer_agents.items():
            if any(a.get("name") == agent_name for a in agents):
                return peer_id
        return None

    def _get_peer(self, peer_id: str) -> Optional[PeerHandle]:
        """Get peer by ID."""
        for peer in self.peers:
            if peer.id == peer_id:
                return peer
        return None

    def _generate_node_id(self) -> str:
        """Generate a unique node ID."""
        import uuid

        return f"node-{uuid.uuid4().hex[:8]}"

    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status."""
        return {
            "node_id": self.node_id,
            "is_running": self.is_running,
            "peer_count": len(self.peers),
            "peers": [
                {
                    "id": p.id,
                    "address": p.address,
                    "capabilities": (
                        p.device_capabilities.__dict__ if p.device_capabilities else {}
                    ),
                }
                for p in self.peers
            ],
            "local_agents": list(self.agent_map.keys()),
            "peer_agents": self.peer_agents,
            "device_capabilities": self.device_capabilities.__dict__,
        }

    async def _handle_list_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request to list agents on this node."""
        agents = []
        for name, agent in self.agent_map.items():
            agents.append(
                {
                    "name": name,
                    "type": agent.__class__.__name__,
                    "has_tools": (
                        len(agent.tools) > 0 if hasattr(agent, "tools") else False
                    ),
                }
            )

        return {"success": True, "agents": agents, "node_id": self.node_id}

    async def _handle_execute_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request to execute an agent remotely."""
        agent_name = request.get("agent_name")
        prompt = request.get("prompt")
        context = request.get("context", {})

        if not agent_name or agent_name not in self.agent_map:
            return {
                "success": False,
                "error": f"Agent {agent_name} not found on node {self.node_id}",
            }

        try:
            # Execute the agent locally
            agent = self.agent_map[agent_name]
            result = await super().run(prompt, agent, context)

            # Include state in response
            result["state"] = self.state.to_dict()

            return result

        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}"}


def create_distributed_network(
    agents: List[Agent],
    name: Optional[str] = None,
    router: Optional[Union[Router, RouterFunction, RoutingAgent]] = None,
    default_model: Optional[str] = None,
    max_iterations: int = 10,
    default_state: Optional[NetworkState] = None,
    discovery_method: str = "udp",
    listen_port: int = 5678,
    broadcast_port: int = 5678,
    node_id: Optional[str] = None,
    device_capabilities: Optional[DeviceCapabilities] = None,
    **metadata,
) -> DistributedNetwork:
    """Create a distributed network of agents.

    Args:
        agents: List of agents in the network
        name: Network name
        router: Router for agent orchestration
        default_model: Default model for routing
        max_iterations: Maximum execution iterations
        default_state: Initial state
        discovery_method: Method for peer discovery (udp, manual, tailscale)
        listen_port: Port to listen on
        broadcast_port: Port for UDP broadcast
        node_id: Optional node identifier
        device_capabilities: Device capabilities
        **metadata: Additional metadata

    Returns:
        Configured DistributedNetwork instance
    """
    config = DistributedNetworkConfig(
        name=name or "distributed-network",
        agents=agents,
        router=router,
        default_model=default_model,
        max_iterations=max_iterations,
        default_state=default_state,
        discovery_method=discovery_method,
        listen_port=listen_port,
        broadcast_port=broadcast_port,
        node_id=node_id,
        device_capabilities=device_capabilities,
        metadata=metadata,
    )

    return DistributedNetwork(config)
