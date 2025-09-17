"""End-to-end test demonstrating hanzo-mcp with hanzo-network using local inference."""

import sys
from pathlib import Path

import pytest

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))

from hanzo_network import (
    create_tool,
    create_local_agent,
    check_local_llm_status,
    create_local_distributed_network,
)


# Test tools
async def echo_message(message: str) -> str:
    """Echo a message."""
    return f"Echo: {message}"


async def add_numbers(a: int, b: int) -> str:
    """Add two numbers."""
    return f"Result: {a + b}"


@pytest.mark.asyncio
async def test_e2e_local_inference():
    """Test end-to-end flow with local hanzo/net inference."""

    # Check hanzo/net status
    status = await check_local_llm_status("hanzo")
    assert status["available"] is True
    assert status["engine"] == "dummy"  # Using dummy for CI
    assert "hanzo/net" in status["provider"]

    # Create agents with local inference
    echo_agent = create_local_agent(
        name="echo_agent",
        description="Echoes messages",
        system="You are an echo agent. Use the echo_message tool when asked to echo.",
        tools=[create_tool(name="echo_message", description="Echo a message", handler=echo_message)],
        local_model="llama3.2",
    )

    math_agent = create_local_agent(
        name="math_agent",
        description="Does math",
        system="You are a math agent. Use the add_numbers tool when asked to add.",
        tools=[create_tool(name="add_numbers", description="Add numbers", handler=add_numbers)],
        local_model="llama3.2",
    )

    # Create distributed network
    network = create_local_distributed_network(
        agents=[echo_agent, math_agent],
        name="test-network",
        listen_port=16000,
        broadcast_port=16000,
    )

    # Start network
    await network.start(wait_for_peers=0)
    assert network.is_running

    # Test network status
    status = network.get_network_status()
    # Node ID is auto-generated, just check it exists
    assert "node_id" in status
    assert status["node_id"].startswith("node-")
    assert "echo_agent" in status["local_agents"]
    assert "math_agent" in status["local_agents"]

    # Test echo agent
    result = await network.run(prompt="Echo the message 'Hello from E2E test'", initial_agent=echo_agent)
    assert result["success"]
    # The dummy model returns generic responses, so just check for success
    assert result["final_output"] is not None
    assert len(result["final_output"]) > 0

    # Test math agent
    result = await network.run(prompt="Add 5 and 3", initial_agent=math_agent)
    assert result["success"]
    # The dummy model returns generic responses, so just check for success
    assert result["final_output"] is not None
    assert len(result["final_output"]) > 0

    # Stop network
    await network.stop()
    assert not network.is_running


@pytest.mark.asyncio
async def test_e2e_multi_agent_collaboration():
    """Test multi-agent collaboration with local inference."""

    # Create collaborative agents
    researcher = create_local_agent(
        name="researcher",
        description="Researches topics",
        system="You research and gather information.",
        tools=[],
        local_model="llama3.2",
    )

    writer = create_local_agent(
        name="writer",
        description="Writes content",
        system="You write clear, concise content.",
        tools=[],
        local_model="llama3.2",
    )

    # Create network
    network = create_local_distributed_network(
        agents=[researcher, writer],
        name="collab-network",
        listen_port=16001,
        broadcast_port=16001,
    )

    await network.start(wait_for_peers=0)

    # Test collaboration
    result = await network.run(prompt="Research what distributed inference is and write a brief explanation")
    assert result["success"]

    await network.stop()


@pytest.mark.asyncio
async def test_e2e_mcp_tools_with_local_llm():
    """Test MCP-style tools with local LLM."""

    # MCP-style file operations
    async def read_test_file(path: str) -> str:
        """Read a test file."""
        return f"Contents of {path}: This is a test file."

    async def list_test_files(directory: str) -> str:
        """List test files."""
        return f"Files in {directory}: test1.py, test2.py, test3.py"

    # Create file system agent
    fs_agent = create_local_agent(
        name="fs_agent",
        description="File system operations",
        system="You handle file system operations using the available tools.",
        tools=[
            create_tool(name="read_test_file", description="Read a file", handler=read_test_file),
            create_tool(
                name="list_test_files",
                description="List files",
                handler=list_test_files,
            ),
        ],
        local_model="llama3.2",
    )

    # Create network
    network = create_local_distributed_network(
        agents=[fs_agent],
        name="mcp-test-network",
        listen_port=16002,
        broadcast_port=16002,
    )

    await network.start(wait_for_peers=0)

    # Test file operations
    result = await network.run(prompt="List the files in the test directory", initial_agent=fs_agent)
    assert result["success"]
    # The dummy model returns generic responses, so just check for success
    assert result["final_output"] is not None
    assert len(result["final_output"]) > 0

    result = await network.run(prompt="Read the test.py file", initial_agent=fs_agent)
    assert result["success"]
    # The dummy model returns generic responses, so just check for success
    assert result["final_output"] is not None
    assert len(result["final_output"]) > 0

    await network.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
