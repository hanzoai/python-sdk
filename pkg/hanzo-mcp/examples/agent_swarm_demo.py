#!/usr/bin/env python3
"""Agent swarm demo using hanzo/net for local private AI inference."""

import asyncio
import sys
from pathlib import Path

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))

from hanzo_network import (
    create_local_agent,
    create_local_distributed_network,
    create_router,
    create_tool,
)
from hanzo_network.core.router import RouterArgs
from hanzo_network.llm import HanzoNetProvider


async def main():
    """Run agent swarm with local AI inference."""

    print("🐝 Hanzo Agent Swarm Demo - Local Private AI Inference")
    print("=" * 60)

    # Check hanzo/net availability
    print("\n📡 Checking hanzo/net distributed inference...")
    provider = HanzoNetProvider("dummy")  # Use dummy for demo
    is_available = await provider.is_available()
    models = await provider.list_models()

    print(f"Status: {'✅ Available' if is_available else '❌ Not Available'}")
    print(f"Models: {', '.join(models)}")
    print(f"Engine: {provider.engine_type}")

    # Create specialized agents for the swarm
    print("\n🤖 Creating agent swarm...")

    # 1. Research Agent
    def search_codebase(query: str) -> str:
        return f"Found 10 results for '{query}' in codebase"

    research_agent = create_local_agent(
        name="researcher",
        description="Searches and analyzes codebase",
        system="You are a code research specialist. Search for patterns and analyze code.",
        tools=[
            create_tool(
                name="search_codebase",
                description="Search codebase for patterns",
                handler=search_codebase,
            )
        ],
        local_model="llama3.2",
    )

    # 2. Analyzer Agent
    def analyze_complexity(code: str) -> str:
        return "Complexity analysis: Low complexity, well-structured"

    analyzer_agent = create_local_agent(
        name="analyzer",
        description="Analyzes code quality and complexity",
        system="You are a code quality analyst. Analyze complexity and suggest improvements.",
        tools=[
            create_tool(
                name="analyze_complexity",
                description="Analyze code complexity",
                handler=analyze_complexity,
            )
        ],
        local_model="llama3.2",
    )

    # 3. Refactor Agent
    def suggest_refactoring(code: str) -> str:
        return "Suggested refactoring: Extract method, improve naming"

    refactor_agent = create_local_agent(
        name="refactorer",
        description="Suggests code refactoring",
        system="You are a refactoring expert. Suggest clean code improvements.",
        tools=[
            create_tool(
                name="suggest_refactoring",
                description="Suggest refactoring improvements",
                handler=suggest_refactoring,
            )
        ],
        local_model="llama3.2",
    )

    # 4. Test Agent
    def generate_tests(function: str) -> str:
        return f"Generated 5 unit tests for '{function}'"

    test_agent = create_local_agent(
        name="tester",
        description="Generates test cases",
        system="You are a test engineer. Generate comprehensive test cases.",
        tools=[
            create_tool(
                name="generate_tests",
                description="Generate test cases",
                handler=generate_tests,
            )
        ],
        local_model="llama3.2",
    )

    # Create smart router for the swarm
    def swarm_router(args: RouterArgs):
        """Intelligent routing for agent swarm."""
        last_output = args.get_last_output() or ""

        # Initial call - start with researcher
        if args.call_count == 0:
            return research_agent

        # After research, analyze
        if args.last_agent and args.last_agent.name == "researcher":
            return analyzer_agent

        # After analysis, suggest refactoring
        if args.last_agent and args.last_agent.name == "analyzer":
            return refactor_agent

        # After refactoring, generate tests
        if args.last_agent and args.last_agent.name == "refactorer":
            return test_agent

        # Stop after all agents have run
        return None

    router = create_router(
        handler=swarm_router,
        name="swarm_router",
        description="Routes tasks through agent swarm",
    )

    # Create distributed network
    network = create_local_distributed_network(
        agents=[research_agent, analyzer_agent, refactor_agent, test_agent],
        name="agent-swarm",
        router=router,
        listen_port=16200,
        broadcast_port=16200,
    )

    # Start the network
    print("\n🌐 Starting agent swarm network...")
    await network.start()

    print(f"Network: {network.name}")
    print(f"Node ID: {network.node_id}")
    print(f"Agents: {len(network.agents)}")
    for agent in network.agents:
        print(f"  - {agent.name}: {agent.description}")

    # Run swarm on different tasks
    print("\n🚀 Running agent swarm tasks...")

    # Task 1: Code improvement workflow
    print("\n📋 Task 1: Full code improvement workflow")
    result = await network.run("Find and improve the authentication code")

    print("\n📊 Swarm Results:")
    print(f"Agents used: {result.get('agent_count', 0)}")
    if "agent_outputs" in result:
        for agent_name, output in result["agent_outputs"].items():
            print(f"\n{agent_name}:")
            if isinstance(output, dict) and "output" in output:
                for item in output["output"]:
                    if item.get("type") == "text":
                        print(f"  {item['content']}")

    # Task 2: Parallel analysis
    print("\n📋 Task 2: Analyze multiple components")
    components = ["database", "api", "frontend"]

    print("Starting parallel analysis...")
    tasks = []
    for component in components:
        # Each component gets its own mini-swarm
        task = network.run(f"Analyze the {component} module")
        tasks.append(task)

    # Wait for all parallel tasks
    results = await asyncio.gather(*tasks)

    print("\n📊 Parallel Analysis Results:")
    for component, result in zip(components, results, strict=False):
        print(f"\n{component.upper()}:")
        agent_count = result.get("agent_count", 0)
        print(f"  Agents used: {agent_count}")

    # Show network statistics
    print("\n📈 Network Statistics:")
    status = network.get_network_status()
    print(f"Total runs: {status.get('total_runs', 0)}")
    print(f"Device: {status.get('device', {}).get('model', 'Unknown')}")
    print("Inference: hanzo/net distributed (no API calls)")

    # Stop the network
    print("\n🛑 Stopping agent swarm...")
    await network.stop()

    print("\n✅ Agent swarm demo complete!")
    print("   - All inference done locally via hanzo/net")
    print("   - No external API calls made")
    print("   - Fully private and distributed")


if __name__ == "__main__":
    asyncio.run(main())
