#!/usr/bin/env python3
"""Working agent swarm demo with hanzo/net local inference."""

import asyncio
import sys
from pathlib import Path

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))

from hanzo_network import create_local_agent, create_tool


class LocalAgentSwarm:
    """A swarm of agents using local hanzo/net inference."""

    def __init__(self):
        self.agents = {}
        self.results = {}

    def create_agents(self):
        """Create specialized agents for the swarm."""

        # Code Scanner Agent
        def scan_files(pattern: str) -> str:
            return (
                f"Scanned files matching '{pattern}': Found 15 Python files, 8 JS files"
            )

        self.agents["scanner"] = create_local_agent(
            name="scanner",
            description="Scans codebase for files",
            system="You scan codebases for specific file patterns.",
            tools=[
                create_tool(
                    name="scan_files",
                    description="Scan for files matching pattern",
                    handler=scan_files,
                )
            ],
            local_model="llama3.2",
        )

        # Vulnerability Detector Agent
        def detect_vulnerabilities(code: str) -> str:
            return (
                "Found 2 potential issues: SQL injection risk, missing input validation"
            )

        self.agents["detector"] = create_local_agent(
            name="detector",
            description="Detects security vulnerabilities",
            system="You detect security vulnerabilities in code.",
            tools=[
                create_tool(
                    name="detect_vulnerabilities",
                    description="Detect security issues",
                    handler=detect_vulnerabilities,
                )
            ],
            local_model="llama3.2",
        )

        # Code Optimizer Agent
        def optimize_code(code: str) -> str:
            return "Optimized: Reduced complexity from O(n²) to O(n log n)"

        self.agents["optimizer"] = create_local_agent(
            name="optimizer",
            description="Optimizes code performance",
            system="You optimize code for better performance.",
            tools=[
                create_tool(
                    name="optimize_code",
                    description="Optimize code performance",
                    handler=optimize_code,
                )
            ],
            local_model="llama3.2",
        )

        # Documentation Agent
        def generate_docs(code: str) -> str:
            return "Generated documentation: 3 classes, 15 methods documented"

        self.agents["documenter"] = create_local_agent(
            name="documenter",
            description="Generates documentation",
            system="You generate comprehensive documentation.",
            tools=[
                create_tool(
                    name="generate_docs",
                    description="Generate documentation",
                    handler=generate_docs,
                )
            ],
            local_model="llama3.2",
        )

        # Test Generator Agent
        def generate_tests(code: str) -> str:
            return "Generated 12 unit tests with 95% coverage"

        self.agents["test_generator"] = create_local_agent(
            name="test_generator",
            description="Generates test cases",
            system="You generate comprehensive test cases.",
            tools=[
                create_tool(
                    name="generate_tests",
                    description="Generate test cases",
                    handler=generate_tests,
                )
            ],
            local_model="llama3.2",
        )

    async def run_sequential_pipeline(self, task: str):
        """Run agents in a sequential pipeline."""
        print(f"\n📋 Sequential Pipeline: {task}")
        print("-" * 50)

        pipeline = ["scanner", "detector", "optimizer", "documenter", "test_generator"]
        previous_output = task

        for agent_name in pipeline:
            agent = self.agents[agent_name]
            print(f"\n▶️  Running {agent_name}...")

            result = await agent.run(previous_output)

            if "output" in result:
                output_text = result["output"][0]["content"]
                print(f"   Result: {output_text}")
                previous_output = output_text
                self.results[agent_name] = output_text

        return self.results

    async def run_parallel_analysis(self, modules: list):
        """Run agents in parallel on different modules."""
        print(f"\n📋 Parallel Analysis of {len(modules)} modules")
        print("-" * 50)

        async def analyze_module(module: str):
            """Analyze a single module with multiple agents."""
            tasks = []

            # Each module gets analyzed by multiple agents
            for agent_name in ["scanner", "detector", "optimizer"]:
                agent = self.agents[agent_name]
                task = agent.run(f"Analyze the {module} module")
                tasks.append((agent_name, task))

            # Wait for all agents to complete
            results = {}
            for agent_name, task in tasks:
                result = await task
                if "output" in result:
                    results[agent_name] = result["output"][0]["content"]

            return module, results

        # Run analysis for all modules in parallel
        module_tasks = [analyze_module(module) for module in modules]
        module_results = await asyncio.gather(*module_tasks)

        # Display results
        for module, results in module_results:
            print(f"\n📦 {module.upper()}:")
            for agent_name, output in results.items():
                print(f"   {agent_name}: {output}")

        return dict(module_results)

    async def run_consensus_decision(self, question: str):
        """Multiple agents vote on a decision."""
        print(f"\n📋 Consensus Decision: {question}")
        print("-" * 50)

        # Ask all agents for their opinion
        tasks = []
        for agent_name, agent in self.agents.items():
            task = agent.run(f"Should we {question}? Answer yes or no with reasoning.")
            tasks.append((agent_name, task))

        # Collect votes
        votes = {}
        for agent_name, task in tasks:
            result = await task
            if "output" in result:
                response = result["output"][0]["content"]
                votes[agent_name] = response
                print(f"\n{agent_name}: {response}")

        # Count consensus
        yes_count = sum(1 for v in votes.values() if "yes" in v.lower())
        no_count = len(votes) - yes_count

        print(
            f"\n🗳️  Consensus: {'YES' if yes_count > no_count else 'NO'} ({yes_count} yes, {no_count} no)"
        )

        return votes


async def main():
    """Run the agent swarm demo."""

    print("🐝 Hanzo Agent Swarm - Working Demo")
    print("=" * 60)
    print("Using hanzo/net for local private AI inference")
    print("No external API calls - everything runs locally")

    # Create and initialize swarm
    swarm = LocalAgentSwarm()
    swarm.create_agents()

    print(f"\n✅ Created {len(swarm.agents)} specialized agents:")
    for name, agent in swarm.agents.items():
        print(f"   - {name}: {agent.description}")

    # Demo 1: Sequential Pipeline
    await swarm.run_sequential_pipeline("Analyze and improve the authentication system")

    # Demo 2: Parallel Analysis
    modules = ["database", "api", "frontend", "auth"]
    await swarm.run_parallel_analysis(modules)

    # Demo 3: Consensus Decision
    await swarm.run_consensus_decision("refactor the entire codebase")

    # Show inference statistics
    print("\n\n📊 Swarm Statistics:")
    print(f"Total agents: {len(swarm.agents)}")
    print("Inference engine: hanzo/net (dummy)")
    print("External API calls: 0")
    print("Privacy: 100% local execution")

    print("\n✅ Agent swarm demo complete!")
    print("   - All agents used hanzo/net local inference")
    print("   - No data left the device")
    print("   - Ready for production use with real models")


if __name__ == "__main__":
    asyncio.run(main())
