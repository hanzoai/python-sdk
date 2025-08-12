"""Simple E2E test for hanzo-mcp with hanzo-network."""

import sys
from pathlib import Path

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))


def test_imports():
    """Test that all imports work correctly."""
    # Test hanzo-network imports

    # Test core imports

    # Test hanzo-mcp imports
    from hanzo_mcp import __version__

    assert __version__ is not None
    print(f"✅ All imports successful! hanzo-mcp version: {__version__}")


def test_hanzo_net_provider():
    """Test that hanzo/net provider is available."""
    from hanzo_network.llm import HanzoNetProvider

    provider = HanzoNetProvider("dummy")
    assert provider is not None
    assert provider.engine_type == "dummy"
    print("✅ HanzoNetProvider created successfully")


def test_local_agent_creation():
    """Test creating a local agent."""
    from hanzo_network import create_tool, create_local_agent

    def dummy_tool(text: str) -> str:
        return f"Processed: {text}"

    agent = create_local_agent(
        name="test_agent",
        description="Test agent",
        system="You are a test agent",
        tools=[
            create_tool(
                name="dummy_tool", description="A dummy tool", handler=dummy_tool
            )
        ],
        local_model="llama3.2",
    )

    assert agent.name == "test_agent"
    assert agent.model.provider.value == "local"
    assert agent.model.model == "llama3.2"
    assert len(agent.tools) == 1
    print("✅ Local agent created successfully")


def test_network_config():
    """Test distributed network configuration."""
    from hanzo_network import create_local_agent, create_local_distributed_network

    agent = create_local_agent(
        name="test_agent", description="Test agent", local_model="llama3.2"
    )

    network = create_local_distributed_network(
        agents=[agent], name="test-network", listen_port=16100, broadcast_port=16100
    )

    assert network.name == "test-network"
    assert network.node_id is not None  # node_id is auto-generated
    assert network.listen_port == 16100
    assert len(network.agents) == 1
    print("✅ Distributed network configured successfully")


if __name__ == "__main__":
    print("Running E2E tests for hanzo-mcp with hanzo-network...\n")

    test_imports()
    test_hanzo_net_provider()
    test_local_agent_creation()
    test_network_config()

    print("\n✅ All tests passed! E2E integration working correctly.")
