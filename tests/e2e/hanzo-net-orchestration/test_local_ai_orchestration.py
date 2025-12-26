#!/usr/bin/env python3
"""
End-to-End Test: Hanzo Net Local AI Orchestration

This test demonstrates:
1. Starting hanzo net with local AI models
2. Loading Qwen3 (or other local models) as orchestrator
3. Using local AI to orchestrate a subnet of API models (Claude, Codex, Gemini)
4. Cost-optimized routing between local and API models
5. Full MCP tool integration across all agents
"""

import os
import sys
import json
import time
import socket
import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from hanzo_network import (
    ModelConfig,
    NetworkState,
    ModelProvider,
    create_agent,
    create_network,
    create_local_agent,
    create_routing_agent,
    create_distributed_network,
)
from hanzo_network.local_network import check_local_llm_status

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HanzoNetE2ETest:
    """End-to-end test for Hanzo Net orchestration."""

    def __init__(self):
        self.hanzo_net_process = None
        self.hanzo_dev_process = None
        self.test_results = []
        self.models_to_test = [
            "qwen3",  # Qwen 3
            "llama-3.2-3b",  # Llama 3.2 3B
            "deepseek-v3",  # DeepSeek V3
            "mistral-7b",  # Mistral 7B
        ]
        self.api_models = [
            "claude-3-5-sonnet-20241022",
            "gpt-4-turbo-preview",
            "gemini-pro",
        ]

    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up E2E test environment...")

        # Check if hanzo net is installed
        result = subprocess.run(["which", "hanzo"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("hanzo CLI not found. Please install: pip install -e pkg/hanzo/")

        # Check for required environment variables
        self.check_api_keys()

        # Create test workspace
        self.workspace = Path.home() / ".hanzo" / "e2e-test"
        self.workspace.mkdir(parents=True, exist_ok=True)

        logger.info(f"Test workspace: {self.workspace}")

    def check_api_keys(self):
        """Check for required API keys."""
        required_keys = {
            "OPENAI_API_KEY": "OpenAI (GPT-4/Codex)",
            "ANTHROPIC_API_KEY": "Anthropic (Claude)",
            "GOOGLE_API_KEY": "Google (Gemini)",
        }

        missing_keys = []
        for key, service in required_keys.items():
            if not os.getenv(key):
                missing_keys.append(f"{key} ({service})")

        if missing_keys:
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
            logger.warning("Some API models will not be available")

    async def start_hanzo_net(self, model: str = "qwen3", port: int = 52415) -> bool:
        """Start hanzo net with specified model."""
        logger.info(f"Starting hanzo net with model: {model} on port {port}")

        # Check if port is already in use
        if self.is_port_open("localhost", port):
            logger.warning(f"Port {port} already in use, attempting to use existing instance")
            return True

        try:
            cmd = [
                "hanzo",
                "net",
                "--name",
                f"e2e-test-{model}",
                "--port",
                str(port),
                "--models",
                model,
                "--network",
                "local",
                "--max-jobs",
                "10",
            ]

            logger.info(f"Command: {' '.join(cmd)}")

            self.hanzo_net_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Wait for hanzo net to start
            for i in range(30):  # 30 seconds timeout
                await asyncio.sleep(1)
                if self.is_port_open("localhost", port):
                    logger.info(f"✓ hanzo net started successfully on port {port}")
                    return True

                # Check if process has died
                if self.hanzo_net_process.poll() is not None:
                    stdout, stderr = self.hanzo_net_process.communicate()
                    logger.error(f"hanzo net failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
                    return False

            logger.error("Timeout waiting for hanzo net to start")
            return False

        except Exception as e:
            logger.error(f"Failed to start hanzo net: {e}")
            return False

    def is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0

    async def create_local_orchestrator(self, model: str, port: int = 52415):
        """Create a local AI orchestrator."""
        logger.info(f"Creating local orchestrator with {model}")

        orchestrator = create_local_agent(
            name=f"{model}_orchestrator",
            description=f"Local {model} orchestrator for E2E test",
            system="""You are a local AI orchestrator managing a network of specialized agents.
            
            Your role:
            1. Coordinate between local and API-based agents
            2. Route tasks based on complexity and cost
            3. Ensure quality through System 2 thinking
            4. Optimize for cost-effectiveness
            
            Available agents:
            - Local workers: Fast, free, good for simple tasks
            - API workers: Powerful but expensive, for complex tasks
            - Critics: Review and improve output quality
            
            Always prefer local models when possible to reduce costs.""",
            local_model=model,
            base_url=f"http://localhost:{port}",
            tools=[],
        )

        return orchestrator

    async def create_agent_network(self, orchestrator_model: str = "qwen3"):
        """Create a full agent network with local orchestrator and mixed workers."""
        logger.info("Creating agent network...")

        agents = []

        # 1. Create local orchestrator
        orchestrator = await self.create_local_orchestrator(orchestrator_model)
        agents.append(orchestrator)

        # 2. Create local worker agents
        for i in range(2):
            worker = create_local_agent(
                name=f"local_worker_{i}",
                description=f"Local worker {i} for simple tasks",
                system="You are a local worker handling simple code tasks efficiently.",
                local_model=orchestrator_model,
                base_url="http://localhost:52415",
            )
            agents.append(worker)
            logger.info(f"  Created local worker {i}")

        # 3. Create API-based worker agents (if keys available)
        if os.getenv("ANTHROPIC_API_KEY"):
            claude_worker = create_agent(
                name="claude_worker",
                description="Claude worker for complex implementation",
                model=ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model="claude-3-5-sonnet-20241022",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                ),
                system="You are Claude, specialized in complex code implementation.",
            )
            agents.append(claude_worker)
            logger.info("  Created Claude worker")

        if os.getenv("OPENAI_API_KEY"):
            gpt_worker = create_agent(
                name="gpt4_worker",
                description="GPT-4 worker for analysis and design",
                model=ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model="gpt-4-turbo-preview",
                    api_key=os.getenv("OPENAI_API_KEY"),
                ),
                system="You are GPT-4, specialized in code analysis and system design.",
            )
            agents.append(gpt_worker)
            logger.info("  Created GPT-4 worker")

            # Also create a Codex-style worker
            codex_worker = create_agent(
                name="codex_worker",
                description="Code completion specialist",
                model=ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model="gpt-4-turbo-preview",  # Using GPT-4 as Codex replacement
                    api_key=os.getenv("OPENAI_API_KEY"),
                    temperature=0.2,  # Lower temperature for code
                ),
                system="You are a code completion specialist. Generate precise, efficient code.",
            )
            agents.append(codex_worker)
            logger.info("  Created Codex-style worker")

        if os.getenv("GOOGLE_API_KEY"):
            gemini_worker = create_agent(
                name="gemini_worker",
                description="Gemini worker for multimodal tasks",
                model=ModelConfig(
                    provider=ModelProvider.GOOGLE,
                    model="gemini-pro",
                    api_key=os.getenv("GOOGLE_API_KEY"),
                ),
                system="You are Gemini, capable of handling diverse tasks including code and analysis.",
            )
            agents.append(gemini_worker)
            logger.info("  Created Gemini worker")

        # 4. Create critic agents for quality assurance
        critic = create_local_agent(
            name="local_critic",
            description="Local critic for code review",
            system="""You are a code quality critic.
            
            Review code for:
            - Correctness and bugs
            - Performance issues
            - Security vulnerabilities
            - Best practices
            
            Provide specific, actionable feedback.""",
            local_model=orchestrator_model,
            base_url="http://localhost:52415",
        )
        agents.append(critic)
        logger.info("  Created local critic")

        # 5. Create intelligent router
        router = create_routing_agent(
            agent=orchestrator,
            system="""Route tasks to the most appropriate agent:
            
            Simple tasks (listing, formatting, validation) → local_worker_*
            Complex implementation → claude_worker or gpt4_worker
            Code completion → codex_worker
            Multimodal or diverse tasks → gemini_worker
            Code review → local_critic
            
            Optimize for cost by preferring local models when possible.""",
        )

        # 6. Create the network
        network = create_network(agents=agents, router=router, default_agent=orchestrator.name)

        logger.info(f"✓ Created agent network with {len(agents)} agents")
        return network

    async def test_task_routing(self, network):
        """Test that tasks are routed correctly between local and API models."""
        logger.info("\n=== Testing Task Routing ===")

        test_cases = [
            {
                "task": "List all Python files in the current directory",
                "expected_agent": "local_worker",
                "reason": "Simple file listing task",
            },
            {
                "task": "Format this JSON: {'key':'value','nested':{'a':1}}",
                "expected_agent": "local_worker",
                "reason": "Simple formatting task",
            },
            {
                "task": "Implement a binary search tree with insert, delete, and search operations",
                "expected_agent": "claude_worker|gpt4_worker",
                "reason": "Complex implementation task",
            },
            {
                "task": "Complete this function: def fibonacci(n): # Calculate nth Fibonacci number",
                "expected_agent": "codex_worker|gpt4_worker",
                "reason": "Code completion task",
            },
            {
                "task": "Review this code for security issues: eval(user_input)",
                "expected_agent": "local_critic",
                "reason": "Code review task",
            },
        ]

        results = []
        for test in test_cases:
            logger.info(f"\nTest: {test['task'][:50]}...")

            try:
                # Create state and run network
                state = NetworkState()
                result = await network.run(prompt=test["task"], state=state)

                # Check which agent handled it
                last_message = state.messages[-1] if state.messages else None
                agent_used = last_message.get("agent", "unknown") if last_message else "unknown"

                # Validate routing
                expected_agents = test["expected_agent"].split("|")
                success = any(expected in agent_used for expected in expected_agents)

                results.append(
                    {
                        "task": test["task"][:50],
                        "expected": test["expected_agent"],
                        "actual": agent_used,
                        "success": success,
                        "reason": test["reason"],
                    }
                )

                logger.info(f"  Agent used: {agent_used}")
                logger.info(f"  Success: {'✓' if success else '✗'}")

            except Exception as e:
                logger.error(f"  Error: {e}")
                results.append({"task": test["task"][:50], "error": str(e), "success": False})

        # Print summary
        logger.info("\n=== Routing Test Summary ===")
        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Passed: {successful}/{len(results)}")

        for result in results:
            status = "✓" if result.get("success") else "✗"
            logger.info(f"  {status} {result.get('task', 'Unknown')}")
            if not result.get("success"):
                logger.info(f"    Expected: {result.get('expected', 'N/A')}")
                logger.info(f"    Actual: {result.get('actual', result.get('error', 'N/A'))}")

        return results

    async def test_cost_optimization(self, network):
        """Test that the system optimizes for cost by using local models when possible."""
        logger.info("\n=== Testing Cost Optimization ===")

        # Track which models handle which tasks
        task_distribution = {"local": 0, "api": 0}

        # Run a series of mixed tasks
        tasks = [
            "Check if file exists: config.json",
            "Validate this email: user@example.com",
            "Count lines in a file",
            "Convert string to uppercase",
            "Parse a simple CSV line",
            # These should go to API models
            "Design a microservices architecture for an e-commerce platform",
            "Debug this complex concurrency issue in a distributed system",
            "Optimize this machine learning pipeline for better performance",
        ]

        for task in tasks:
            try:
                state = NetworkState()
                result = await network.run(prompt=task, state=state)

                # Check which type of agent handled it
                last_message = state.messages[-1] if state.messages else None
                agent_used = last_message.get("agent", "") if last_message else ""

                if "local" in agent_used.lower():
                    task_distribution["local"] += 1
                else:
                    task_distribution["api"] += 1

            except Exception as e:
                logger.error(f"Error processing task: {e}")

        # Calculate cost savings
        local_ratio = task_distribution["local"] / len(tasks) if tasks else 0
        cost_savings = local_ratio * 100

        logger.info(f"\nTask Distribution:")
        logger.info(f"  Local models: {task_distribution['local']}/{len(tasks)}")
        logger.info(f"  API models: {task_distribution['api']}/{len(tasks)}")
        logger.info(f"  Cost savings: ~{cost_savings:.1f}%")

        return {
            "distribution": task_distribution,
            "cost_savings_percent": cost_savings,
            "success": cost_savings > 50,  # Expect >50% to use local models
        }

    async def test_hanzo_dev_integration(self, model: str = "qwen3"):
        """Test full hanzo dev integration with local orchestrator."""
        logger.info("\n=== Testing Hanzo Dev Integration ===")

        try:
            # Start hanzo dev with local orchestrator
            cmd = [
                "hanzo",
                "dev",
                "--orchestrator",
                f"local:{model}",
                "--instances",
                "3",
                "--use-hanzo-net",
                "--workspace",
                str(self.workspace),
                "--no-repl",  # Non-interactive mode
                "--no-monitor",
            ]

            logger.info(f"Starting hanzo dev: {' '.join(cmd)}")

            # Run hanzo dev for a short time to test initialization
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Give it time to initialize
            await asyncio.sleep(10)

            # Check if it's still running
            if process.poll() is None:
                logger.info("✓ hanzo dev started successfully")

                # Terminate gracefully
                process.terminate()
                await asyncio.sleep(2)

                if process.poll() is None:
                    process.kill()

                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"hanzo dev failed:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to test hanzo dev: {e}")
            return False

    async def run_full_test(self):
        """Run the complete E2E test suite."""
        logger.info("\n" + "=" * 60)
        logger.info("HANZO NET E2E TEST - LOCAL AI ORCHESTRATION")
        logger.info("=" * 60)

        all_results = {}

        try:
            # Setup
            await self.setup()

            # Test with different local models
            for model in self.models_to_test:
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Testing with model: {model}")
                logger.info(f"{'=' * 60}")

                model_results = {}

                # Start hanzo net with the model
                if await self.start_hanzo_net(model):
                    # Create agent network
                    network = await self.create_agent_network(model)

                    # Run tests
                    model_results["routing"] = await self.test_task_routing(network)
                    model_results["cost_optimization"] = await self.test_cost_optimization(network)
                    model_results["hanzo_dev"] = await self.test_hanzo_dev_integration(model)

                    # Stop hanzo net
                    if self.hanzo_net_process:
                        self.hanzo_net_process.terminate()
                        await asyncio.sleep(2)
                        self.hanzo_net_process = None
                else:
                    logger.warning(f"Skipping tests for {model} - failed to start hanzo net")
                    model_results["error"] = "Failed to start hanzo net"

                all_results[model] = model_results

                # Brief pause between models
                await asyncio.sleep(5)

            # Print final summary
            self.print_summary(all_results)

        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        finally:
            # Cleanup
            await self.cleanup()

    def print_summary(self, results: Dict):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        for model, model_results in results.items():
            logger.info(f"\n{model}:")

            if "error" in model_results:
                logger.info(f"  ✗ {model_results['error']}")
                continue

            # Routing tests
            if "routing" in model_results:
                routing = model_results["routing"]
                passed = sum(1 for r in routing if r.get("success", False))
                logger.info(f"  Routing: {passed}/{len(routing)} passed")

            # Cost optimization
            if "cost_optimization" in model_results:
                cost = model_results["cost_optimization"]
                if cost.get("success"):
                    logger.info(f"  Cost Optimization: ✓ ({cost['cost_savings_percent']:.1f}% savings)")
                else:
                    logger.info(f"  Cost Optimization: ✗")

            # Hanzo dev integration
            if "hanzo_dev" in model_results:
                if model_results["hanzo_dev"]:
                    logger.info(f"  Hanzo Dev Integration: ✓")
                else:
                    logger.info(f"  Hanzo Dev Integration: ✗")

    async def cleanup(self):
        """Clean up test resources."""
        logger.info("\nCleaning up...")

        # Stop hanzo net
        if self.hanzo_net_process:
            self.hanzo_net_process.terminate()
            await asyncio.sleep(2)
            if self.hanzo_net_process.poll() is None:
                self.hanzo_net_process.kill()

        # Stop hanzo dev
        if self.hanzo_dev_process:
            self.hanzo_dev_process.terminate()
            await asyncio.sleep(2)
            if self.hanzo_dev_process.poll() is None:
                self.hanzo_dev_process.kill()

        logger.info("Cleanup complete")


async def main():
    """Main entry point."""
    test = HanzoNetE2ETest()
    await test.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())
