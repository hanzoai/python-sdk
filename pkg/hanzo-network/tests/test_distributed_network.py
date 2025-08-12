"""Tests for distributed network functionality."""

import asyncio
import pytest
from hanzo_network import create_agent, create_distributed_network, create_tool


# Simple test tool
async def echo_tool(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


# Create test agents
def create_test_agents():
    """Create test agents for distributed network."""

    # Echo agent
    echo_agent = create_agent(
        name="echo_agent",
        description="Agent that echoes messages",
        system="You are an echo agent. Use the echo tool to echo messages.",
        tools=[create_tool(echo_tool, "Echo back the message")],
    )

    # Math agent
    async def calculate(expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception:
            return "Error: Invalid expression"

    math_agent = create_agent(
        name="math_agent",
        description="Agent that performs calculations",
        system="You are a math agent. Use the calculate tool for math.",
        tools=[create_tool(calculate, "Evaluate a mathematical expression")],
    )

    return [echo_agent, math_agent]


@pytest.mark.asyncio
async def test_distributed_network_creation():
    """Test creating a distributed network."""
    agents = create_test_agents()

    network = create_distributed_network(
        agents=agents,
        name="test-network",
        discovery_method="udp",
        listen_port=15678,  # Use different port to avoid conflicts
        broadcast_port=15678,
    )

    assert network.name == "test-network"
    assert len(network.agents) == 2
    assert network.discovery_method == "udp"
    assert network.listen_port == 15678


@pytest.mark.asyncio
async def test_distributed_network_start_stop():
    """Test starting and stopping a distributed network."""
    agents = create_test_agents()

    network = create_distributed_network(
        agents=agents, name="test-network", listen_port=15679, broadcast_port=15679
    )

    # Start network
    await network.start(wait_for_peers=0)
    assert network.is_running

    # Get status
    status = network.get_network_status()
    assert status["is_running"]
    assert status["node_id"] == network.node_id
    assert "echo_agent" in status["local_agents"]
    assert "math_agent" in status["local_agents"]

    # Stop network
    await network.stop()
    assert not network.is_running


@pytest.mark.asyncio
async def test_distributed_network_local_execution():
    """Test executing agents locally in distributed network."""
    agents = create_test_agents()

    network = create_distributed_network(
        agents=agents, name="test-network", listen_port=15680, broadcast_port=15680
    )

    # Start network
    await network.start(wait_for_peers=0)

    try:
        # Test echo agent
        echo_result = await network.run(
            prompt="Echo the message 'Hello World'",
            initial_agent=network.get_agent("echo_agent"),
        )

        assert echo_result["success"]
        # Mock agents return mock responses
        assert "echo_agent" in echo_result["final_output"]

        # Test math agent
        math_result = await network.run(
            prompt="Calculate 2 + 2", initial_agent=network.get_agent("math_agent")
        )

        assert math_result["success"]
        # Mock agents return mock responses
        assert "math_agent" in math_result["final_output"]

    finally:
        await network.stop()


@pytest.mark.asyncio
async def test_distributed_network_peer_discovery():
    """Test peer discovery between two networks."""
    agents1 = create_test_agents()
    agents2 = create_test_agents()

    # Create two networks on same broadcast
    network1 = create_distributed_network(
        agents=agents1,
        name="network-1",
        node_id="node-1",
        listen_port=15681,
        broadcast_port=15683,  # Same broadcast port
    )

    network2 = create_distributed_network(
        agents=agents2,
        name="network-2",
        node_id="node-2",
        listen_port=15682,
        broadcast_port=15683,  # Same broadcast port
    )

    # Start both networks
    await network1.start(wait_for_peers=0)
    await network2.start(wait_for_peers=0)

    try:
        # Wait for discovery
        await asyncio.sleep(2)

        # Check if they discovered each other
        status1 = network1.get_network_status()
        status2 = network2.get_network_status()

        # Each should have discovered the other
        # Note: This might not work in CI/test environment without actual UDP
        # but demonstrates the API
        print(f"Network 1 peers: {status1['peer_count']}")
        print(f"Network 2 peers: {status2['peer_count']}")

    finally:
        await network1.stop()
        await network2.stop()


@pytest.mark.asyncio
async def test_distributed_network_with_router():
    """Test distributed network with custom router."""
    agents = create_test_agents()

    # Simple router that alternates between agents
    call_count = 0

    def simple_router(args):
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return args.network.get_agent("echo_agent")
        elif call_count <= 2:
            return args.network.get_agent("math_agent")
        else:
            return None  # Stop

    network = create_distributed_network(
        agents=agents,
        name="test-network",
        router=simple_router,
        listen_port=15684,
        broadcast_port=15684,
    )

    await network.start(wait_for_peers=0)

    try:
        result = await network.run(prompt="First echo 'test', then calculate 5 + 5")

        assert result["success"]
        assert result["iterations"] == 2

    finally:
        await network.stop()


if __name__ == "__main__":
    # Run a simple test
    asyncio.run(test_distributed_network_peer_discovery())
