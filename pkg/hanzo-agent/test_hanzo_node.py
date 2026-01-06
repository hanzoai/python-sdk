#!/usr/bin/env python3
"""
Test script to verify Hanzo Agent SDK works with local Hanzo Node (hanzod) at port 3690.
"""

import asyncio
import os
import sys
from typing import Optional

# Add src to path if running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents import (
    Agent,
    Runner,
    RunConfig,
    HanzoNodeProvider,
    create_hanzo_node_provider,
    function_tool
)

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


@function_tool
def get_weather(location: str) -> str:
    """Get the weather for a specific location."""
    return f"The weather in {location} is sunny with a temperature of 72°F."


@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating {expression}: {str(e)}"


async def test_hanzo_node_connection():
    """Test connection to Hanzo Node."""
    print(f"\n{CYAN}Testing Hanzo Node Connection...{RESET}")

    # Create provider for Hanzo Node at port 3690
    provider = create_hanzo_node_provider(port=3690)

    # Check health
    is_healthy = await provider.health_check()

    if is_healthy:
        print(f"{GREEN}✓ Successfully connected to Hanzo Node at {provider.base_url}{RESET}")
        return provider
    else:
        print(f"{RED}✗ Failed to connect to Hanzo Node at {provider.base_url}{RESET}")
        print(f"{YELLOW}Make sure hanzod is running on port 3690{RESET}")
        return None


async def test_simple_agent(provider: HanzoNodeProvider):
    """Test a simple agent with Hanzo Node."""
    print(f"\n{CYAN}Testing Simple Agent...{RESET}")

    # Create a simple agent
    agent = Agent(
        name="TestAgent",
        model=provider.get_model("gpt-oss:20b"),  # Use local OSS model
        instructions="""You are a helpful assistant that can:
        1. Get weather information
        2. Perform calculations
        Always be concise and friendly.""",
        tools=[get_weather, calculate],
    )

    # Test queries
    test_queries = [
        "What's 2 + 2?",
        "What's the weather in San Francisco?",
        "Calculate 15 * 3 + 7",
    ]

    for query in test_queries:
        print(f"\n{YELLOW}Query: {query}{RESET}")

        try:
            runner = Runner(agent)
            result = await runner.run(query)

            print(f"{GREEN}Response:{RESET}")
            for item in result.items:
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'text'):
                            print(f"  {content.text}")
                        elif hasattr(content, 'name') and hasattr(content, 'result'):
                            print(f"  Tool: {content.name}")
                            print(f"  Result: {content.result}")
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")


async def test_streaming_agent(provider: HanzoNodeProvider):
    """Test streaming responses with Hanzo Node."""
    print(f"\n{CYAN}Testing Streaming Agent...{RESET}")

    agent = Agent(
        name="StreamingAgent",
        model=provider.get_model(),
        instructions="You are a creative storyteller. Keep responses brief.",
    )

    runner = Runner(agent)
    query = "Tell me a very short story about a robot learning to paint."

    print(f"\n{YELLOW}Query: {query}{RESET}")
    print(f"{GREEN}Streaming Response:{RESET}")

    try:
        async with runner.run_stream(query) as stream:
            async for chunk in stream:
                if hasattr(chunk, 'content'):
                    for content in chunk.content:
                        if hasattr(content, 'text'):
                            print(content.text, end='', flush=True)
        print()  # New line after streaming
    except Exception as e:
        print(f"\n{RED}Error during streaming: {e}{RESET}")


async def main():
    """Main test function."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Hanzo Agent SDK - Hanzo Node Integration Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Test connection
    provider = await test_hanzo_node_connection()

    if provider:
        # Run tests
        await test_simple_agent(provider)
        await test_streaming_agent(provider)

        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}All tests completed!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    else:
        print(f"\n{RED}Tests aborted: Could not connect to Hanzo Node{RESET}")
        print(f"{YELLOW}To start Hanzo Node:{RESET}")
        print(f"  cd /Users/z/work/hanzo/node")
        print(f"  cargo run --release --bin hanzod")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())