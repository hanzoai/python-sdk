#!/usr/bin/env python
"""Test distributed network functionality."""

import asyncio
from hanzo_network import create_distributed_network, create_agent, create_tool


async def echo_tool(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


async def main():
    """Test distributed network."""
    print("Testing Hanzo Distributed Network")
    print("=" * 50)

    # Create a simple agent
    agent = create_agent(
        name="test_agent",
        description="Test agent",
        system="You are a test agent.",
        tools=[create_tool(echo_tool, "Echo a message")],
    )

    # Create distributed network
    network = create_distributed_network(
        agents=[agent],
        name="test-network",
        node_id="test-node-1",
        listen_port=15690,
        broadcast_port=15690,
    )

    print("Starting network...")
    await network.start(wait_for_peers=0)

    # Get status
    status = network.get_network_status()
    print("\nNetwork Status:")
    print(f"  Node ID: {status['node_id']}")
    print(f"  Running: {status['is_running']}")
    print(f"  Device: {status['device_capabilities']['model']}")
    print(f"  Chip: {status['device_capabilities']['chip']}")
    print(f"  Memory: {status['device_capabilities']['memory']} MB")
    print(f"  Local agents: {status['local_agents']}")

    # Wait a bit for any peers
    print("\nWaiting for peer discovery...")
    await asyncio.sleep(2)

    # Check peers
    status = network.get_network_status()
    print(f"  Discovered peers: {status['peer_count']}")

    print("\nStopping network...")
    await network.stop()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
