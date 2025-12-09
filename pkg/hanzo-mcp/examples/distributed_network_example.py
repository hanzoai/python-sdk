#!/usr/bin/env python
"""Example of hanzo-mcp using distributed hanzo-network with local LLM."""

import asyncio

from hanzo_network import (
    create_tool,
    create_local_agent,
    check_local_llm_status,
    create_local_distributed_network,
)


# MCP-style tools that could be exposed
async def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    import os

    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


async def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a pattern."""
    import os
    import glob

    try:
        matches = glob.glob(os.path.join(directory, pattern))
        return "\n".join(matches) if matches else "No matches found"
    except Exception as e:
        return f"Error searching: {str(e)}"


async def main():
    """Demonstrate hanzo-mcp integration with distributed network."""
    print("🌐 Hanzo MCP + Distributed Network Demo")
    print("=" * 50)

    # Check local LLM status
    print("\n📡 Checking local LLM availability...")
    ollama_status = await check_local_llm_status("ollama")

    if not ollama_status["available"]:
        print("⚠️  Ollama not available. Install and run with:")
        print("    brew install ollama")
        print("    ollama serve")
        print("    ollama pull llama3.2")
        print("\nContinuing with mock responses...")
    else:
        print(f"✅ Ollama available with models: {ollama_status['models']}")

    # Create MCP-style agents with local LLM
    file_agent = create_local_agent(
        name="file_agent",
        description="Agent that handles file operations",
        system="""You are a file system assistant. You have access to tools for:
- read_file: Read file contents
- list_files: List directory contents  
- search_files: Search for files by pattern

Help users explore and understand the filesystem.""",
        tools=[
            create_tool(
                name="read_file",
                description="Read a file from the filesystem",
                handler=read_file,
            ),
            create_tool(
                name="list_files",
                description="List files in a directory",
                handler=list_files,
            ),
            create_tool(
                name="search_files",
                description="Search for files matching a pattern",
                handler=search_files,
            ),
        ],
        local_model="llama3.2",
    )

    # Create a code analysis agent
    code_agent = create_local_agent(
        name="code_agent",
        description="Agent that analyzes code",
        system="""You are a code analysis assistant. When given code or file paths:
- Explain what the code does
- Identify potential issues
- Suggest improvements
Work with the file_agent to read code files.""",
        tools=[],  # This agent focuses on analysis, not tools
        local_model="llama3.2",
    )

    # Create distributed network
    network = create_local_distributed_network(
        agents=[file_agent, code_agent],
        name="mcp-network",
        node_id="mcp-node-1",
        listen_port=15710,
        broadcast_port=15710,
    )

    print("\n🚀 Starting MCP-compatible network...")
    await network.start(wait_for_peers=0)

    # Network status
    status = network.get_network_status()
    print("\n📊 Network Status:")
    print(f"  Node: {status['node_id']}")
    print(f"  Agents: {', '.join(status['local_agents'])}")

    # Example 1: List files
    print("\n📁 Example 1: List files in current directory")
    result = await network.run(
        prompt="List all Python files in the current directory",
        initial_agent=file_agent,
    )
    print(f"Response: {result['final_output']}")

    # Example 2: Read and analyze
    print("\n📖 Example 2: Read and analyze a file")
    result = await network.run(prompt="Read the pyproject.toml file and tell me what this project is about")
    print(f"Response: {result['final_output']}")

    # Example 3: Multi-agent collaboration
    print("\n🤝 Example 3: Multi-agent collaboration")
    result = await network.run(prompt="Find all Python files that might contain the main entry point and analyze them")
    print(f"Response: {result['final_output']}")
    print(f"Agents used: {result['iterations']}")

    # Simulate multiple nodes
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        print("\n🌍 Starting second node...")

        # Create another agent on a different "node"
        search_agent = create_local_agent(
            name="search_agent",
            description="Agent that searches code",
            system="You are a code search specialist.",
            tools=[
                create_tool(
                    name="search_files",
                    description="Search for files",
                    handler=search_files,
                )
            ],
            local_model="llama3.2",
        )

        # Second network node
        network2 = create_local_distributed_network(
            agents=[search_agent],
            name="mcp-network",
            node_id="mcp-node-2",
            listen_port=15711,
            broadcast_port=15710,  # Same broadcast port!
        )

        await network2.start(wait_for_peers=1)

        print("\n🔍 Testing cross-node discovery...")
        await asyncio.sleep(2)

        status1 = network.get_network_status()
        status2 = network2.get_network_status()

        print(f"Node 1 peers: {status1['peer_count']}")
        print(f"Node 2 peers: {status2['peer_count']}")

    print("\n✅ Demo complete!")
    await network.stop()


if __name__ == "__main__":
    print("\nUsage:")
    print("  python distributed_network_example.py          # Single node demo")
    print("  python distributed_network_example.py --multi  # Multi-node demo\n")

    asyncio.run(main())
