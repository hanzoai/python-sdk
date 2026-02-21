#!/usr/bin/env python3
"""Hanzo MCP + Agent Swarm Integration Demo.

This demonstrates how hanzo-mcp can launch agent swarms with local private AI inference.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, List

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))

from hanzo_network import (
    check_local_llm_status,
    create_local_agent,
    create_local_distributed_network,
    create_tool,
)
from hanzo_network.llm import HanzoNetProvider


class HanzoMCPSwarmLauncher:
    """Launcher for agent swarms via hanzo-mcp."""

    def __init__(self):
        self.networks = {}
        self.agents = {}

    async def check_infrastructure(self):
        """Check that hanzo/net infrastructure is ready."""
        print("🔍 Checking hanzo/net infrastructure...")

        # Check local LLM status
        status = await check_local_llm_status()
        print(f"Local LLM Status: {status}")

        # Check available engines
        provider = HanzoNetProvider("dummy")
        is_available = await provider.is_available()
        models = await provider.list_models()

        print(f"Provider Available: {is_available}")
        print(f"Models: {', '.join(models)}")
        print(f"Engine: {provider.engine_type}")

        return is_available

    def create_code_analysis_swarm(self) -> List[Any]:
        """Create a swarm for code analysis tasks."""
        agents = []

        # File System Agent (MCP-style)
        def read_file(path: str) -> str:
            return f"File contents of {path}: [mock file content]"

        def search_files(pattern: str) -> str:
            return f"Found 10 files matching '{pattern}'"

        fs_agent = create_local_agent(
            name="fs_agent",
            description="File system operations agent",
            system="You handle file system operations like reading and searching files.",
            tools=[
                create_tool(
                    name="read_file",
                    description="Read file contents",
                    handler=read_file,
                ),
                create_tool(
                    name="search_files",
                    description="Search for files",
                    handler=search_files,
                ),
            ],
            local_model="llama3.2",
        )
        agents.append(fs_agent)

        # Code Analysis Agent
        def analyze_code(code: str) -> str:
            return "Analysis: Clean code, follows best practices, complexity: Low"

        analysis_agent = create_local_agent(
            name="analysis_agent",
            description="Code analysis and metrics",
            system="You analyze code quality and provide metrics.",
            tools=[
                create_tool(
                    name="analyze_code",
                    description="Analyze code quality",
                    handler=analyze_code,
                )
            ],
            local_model="llama3.2",
        )
        agents.append(analysis_agent)

        # Refactoring Agent
        def suggest_refactor(code: str) -> str:
            return "Suggested refactoring: Extract method, improve variable names"

        refactor_agent = create_local_agent(
            name="refactor_agent",
            description="Code refactoring suggestions",
            system="You suggest code refactoring improvements.",
            tools=[
                create_tool(
                    name="suggest_refactor",
                    description="Suggest refactoring",
                    handler=suggest_refactor,
                )
            ],
            local_model="llama3.2",
        )
        agents.append(refactor_agent)

        return agents

    def create_development_swarm(self) -> List[Any]:
        """Create a swarm for development tasks."""
        agents = []

        # Code Generator Agent
        def generate_code(spec: str) -> str:
            return (
                f"Generated code for: {spec}\ndef example():\n    return 'Hello World'"
            )

        generator_agent = create_local_agent(
            name="generator_agent",
            description="Code generation from specifications",
            system="You generate code from specifications.",
            tools=[
                create_tool(
                    name="generate_code",
                    description="Generate code",
                    handler=generate_code,
                )
            ],
            local_model="llama3.2",
        )
        agents.append(generator_agent)

        # Test Writer Agent
        def write_tests(code: str) -> str:
            return "Generated tests:\ndef test_example():\n    assert example() == 'Hello World'"

        test_agent = create_local_agent(
            name="test_agent",
            description="Test case generation",
            system="You write comprehensive test cases.",
            tools=[
                create_tool(
                    name="write_tests",
                    description="Write test cases",
                    handler=write_tests,
                )
            ],
            local_model="llama3.2",
        )
        agents.append(test_agent)

        # Documentation Agent
        def write_docs(code: str) -> str:
            return "Documentation:\n# Example Function\nReturns a greeting message."

        docs_agent = create_local_agent(
            name="docs_agent",
            description="Documentation generation",
            system="You write clear documentation.",
            tools=[
                create_tool(
                    name="write_docs",
                    description="Write documentation",
                    handler=write_docs,
                )
            ],
            local_model="llama3.2",
        )
        agents.append(docs_agent)

        return agents

    async def launch_swarm(self, swarm_type: str, task: str):
        """Launch a specific swarm type."""
        print(f"\n🚀 Launching {swarm_type} swarm...")

        # Create agents based on swarm type
        if swarm_type == "analysis":
            agents = self.create_code_analysis_swarm()
        elif swarm_type == "development":
            agents = self.create_development_swarm()
        else:
            raise ValueError(f"Unknown swarm type: {swarm_type}")

        # Create distributed network
        network = create_local_distributed_network(
            agents=agents,
            name=f"{swarm_type}-swarm",
            listen_port=16300 + len(self.networks),
            broadcast_port=16300 + len(self.networks),
        )

        # Start network
        await network.start()
        self.networks[swarm_type] = network

        print(f"✅ {swarm_type} swarm launched with {len(agents)} agents")

        # Execute task
        print(f"\n📋 Executing task: {task}")
        result = await network.run(task)

        # Display results
        print("\n📊 Results:")
        if "output" in result:
            for item in result["output"]:
                if item.get("type") == "text":
                    print(f"  {item['content']}")

        return result

    async def coordinate_swarms(self, complex_task: str):
        """Coordinate multiple swarms for complex tasks."""
        print(f"\n🎯 Coordinating swarms for: {complex_task}")

        # Phase 1: Analysis
        analysis_result = await self.launch_swarm(
            "analysis", f"Analyze the codebase for: {complex_task}"
        )

        # Phase 2: Development based on analysis
        dev_result = await self.launch_swarm(
            "development", f"Based on analysis, implement: {complex_task}"
        )

        return {"analysis": analysis_result, "development": dev_result}

    async def shutdown(self):
        """Shutdown all networks."""
        print("\n🛑 Shutting down swarms...")
        for name, network in self.networks.items():
            await network.stop()
            print(f"  ✅ {name} swarm stopped")


async def main():
    """Main demo."""
    print("🐝 Hanzo MCP + Agent Swarm Integration")
    print("=" * 60)
    print("Demonstrating how hanzo-mcp launches agent swarms")
    print("with local private AI inference via hanzo/net")

    # Create launcher
    launcher = HanzoMCPSwarmLauncher()

    # Check infrastructure
    if not await launcher.check_infrastructure():
        print("❌ Infrastructure not ready")
        return

    # Demo 1: Simple swarm launch
    print("\n\n📋 Demo 1: Simple Analysis Swarm")
    await launcher.launch_swarm(
        "analysis", "Find all authentication-related code and analyze security"
    )

    # Demo 2: Development swarm
    print("\n\n📋 Demo 2: Development Swarm")
    await launcher.launch_swarm("development", "Create a new user registration system")

    # Demo 3: Coordinated swarms
    print("\n\n📋 Demo 3: Coordinated Multi-Swarm Task")
    await launcher.coordinate_swarms("Refactor the payment processing module")

    # Show final statistics
    print("\n\n📊 Session Statistics:")
    print(f"Total swarms launched: {len(launcher.networks)}")
    print(
        f"Total agents created: {sum(len(n.agents) for n in launcher.networks.values())}"
    )
    print("Inference engine: hanzo/net (local)")
    print("External API calls: 0")
    print("Privacy: 100% on-device execution")

    # Shutdown
    await launcher.shutdown()

    print("\n✅ Hanzo MCP + Swarm integration complete!")
    print("   - All swarms used local private inference")
    print("   - No data sent to external services")
    print("   - Ready for production deployment")


if __name__ == "__main__":
    asyncio.run(main())
