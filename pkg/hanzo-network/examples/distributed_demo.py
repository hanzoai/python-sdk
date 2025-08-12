#!/usr/bin/env python
"""Demonstration of Hanzo distributed network with UDP discovery.

This example shows how to:
1. Create distributed networks on different ports
2. Have them discover each other via UDP broadcast
3. Execute agents across the network
"""

import asyncio
import sys
from hanzo_network import (
    create_agent,
    create_tool,
    create_distributed_network,
)


# Create some test tools
async def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"The weather in {location} is sunny and 72°F"


async def get_time(timezone: str = "UTC") -> str:
    """Get current time in timezone."""
    from datetime import datetime

    return f"Current time in {timezone}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception:
        return "Error: Invalid expression"


def create_demo_agents():
    """Create agents for the demo."""
    # Weather agent
    weather_agent = create_agent(
        name="weather_agent",
        description="Agent that provides weather information",
        system="You are a weather agent. Use the get_weather tool to get weather information.",
        tools=[create_tool(get_weather, "Get weather for a location")],
    )

    # Time agent
    time_agent = create_agent(
        name="time_agent",
        description="Agent that provides time information",
        system="You are a time agent. Use the get_time tool to get time information.",
        tools=[create_tool(get_time, "Get current time in timezone")],
    )

    # Math agent
    math_agent = create_agent(
        name="math_agent",
        description="Agent that performs calculations",
        system="You are a math agent. Use the calculate tool for math.",
        tools=[create_tool(calculate, "Evaluate a mathematical expression")],
    )

    return [weather_agent, time_agent, math_agent]


async def run_node(node_id: str, port: int, agents_subset: list):
    """Run a single network node."""
    print(f"\n🚀 Starting node {node_id} on port {port}")

    # Create distributed network
    network = create_distributed_network(
        agents=agents_subset,
        name=f"demo-network-{node_id}",
        node_id=node_id,
        listen_port=port,
        broadcast_port=5678,  # All nodes use same broadcast port
    )

    # Start the network
    await network.start(wait_for_peers=0)

    # Print status
    status = network.get_network_status()
    print(f"📡 Node {node_id} started with agents: {status['local_agents']}")

    # Keep running and periodically show peer status
    while True:
        await asyncio.sleep(5)
        status = network.get_network_status()
        print(
            f"📊 Node {node_id} status - Peers: {status['peer_count']}, Agents: {status['local_agents']}"
        )

        # Show discovered peers
        if status["peers"]:
            for peer in status["peers"]:
                print(f"  👥 Peer: {peer['id']} at {peer['address']}")


async def main():
    """Run the distributed network demo."""
    print("🌐 Hanzo Distributed Network Demo")
    print("=" * 50)

    # Create agents
    all_agents = create_demo_agents()

    # Split agents across nodes
    node1_agents = [all_agents[0]]  # Weather agent
    node2_agents = [all_agents[1]]  # Time agent
    node3_agents = [all_agents[2]]  # Math agent

    # Run multiple nodes
    if len(sys.argv) > 1:
        # Run specific node based on command line arg
        node_num = int(sys.argv[1])
        if node_num == 1:
            await run_node("node-1", 5681, node1_agents)
        elif node_num == 2:
            await run_node("node-2", 5682, node2_agents)
        elif node_num == 3:
            await run_node("node-3", 5683, node3_agents)
        else:
            print("Usage: python distributed_demo.py [1|2|3]")
    else:
        print("\nRunning all nodes in parallel (for demo only)")
        print("In production, run each node separately:\n")
        print("  Terminal 1: python distributed_demo.py 1")
        print("  Terminal 2: python distributed_demo.py 2")
        print("  Terminal 3: python distributed_demo.py 3\n")

        # Run all nodes in parallel for demo
        tasks = [
            run_node("node-1", 5681, node1_agents),
            run_node("node-2", 5682, node2_agents),
            run_node("node-3", 5683, node3_agents),
        ]

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Demo stopped by user")
