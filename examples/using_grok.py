#!/usr/bin/env python
"""Example of using xAI Grok with Hanzo Python SDK.

This example demonstrates:
1. Direct API usage with Grok
2. Streaming responses
3. Batch operations with Grok
4. Consensus with multiple models including Grok
"""

import os
import sys
import asyncio

# Add paths for development (remove in production)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pkg", "hanzoai"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pkg", "hanzo", "src"))

try:
    from hanzoai import Hanzo, AsyncHanzo
except ImportError:
    print("Error: hanzoai not installed")
    print("Install with: pip install hanzoai")
    sys.exit(1)

# Note: Requires XAI_API_KEY environment variable to be set
# Get your API key from https://x.ai/api


def basic_grok_usage():
    """Basic usage of Grok through Hanzo SDK."""
    client = Hanzo()  # Uses HANZO_API_KEY env var

    # Simple completion
    response = client.chat.completions.create(
        model="grok-4",  # or "grok" or "xai-grok"
        messages=[
            {"role": "system", "content": "You have real-time knowledge."},
            {"role": "user", "content": "What are the latest AI developments this week?"},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    print("Grok Response:")
    print(response.choices[0].message.content)
    print("\n" + "=" * 50 + "\n")


def streaming_grok():
    """Stream responses from Grok for real-time output."""
    client = Hanzo()

    print("Streaming from Grok:")
    stream = client.chat.completions.create(
        model="grok-4", messages=[{"role": "user", "content": "Explain quantum computing in simple terms"}], stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

    print("\n\n" + "=" * 50 + "\n")


async def async_grok_usage():
    """Async usage of Grok for concurrent operations."""
    client = AsyncHanzo()

    # Concurrent requests to different models
    tasks = [
        client.chat.completions.create(
            model="grok-4", messages=[{"role": "user", "content": "What's happening in tech today?"}]
        ),
        client.chat.completions.create(
            model="claude-3-5-sonnet", messages=[{"role": "user", "content": "Explain machine learning"}]
        ),
        client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "Write a haiku about AI"}]),
    ]

    print("Concurrent requests to Grok, Claude, and GPT-4:")
    responses = await asyncio.gather(*tasks)

    for i, (model, response) in enumerate(zip(["Grok", "Claude", "GPT-4"], responses, strict=False)):
        print(f"\n{model} Response:")
        print(response.choices[0].message.content[:200] + "...")

    print("\n" + "=" * 50 + "\n")


def batch_operations_with_grok():
    """Demonstrate batch operations using Grok."""
    from hanzo.batch_orchestrator import BatchConfig, BatchOrchestrator

    print("Batch Operations with Grok:")

    # Parse different batch configurations
    configs = [
        "batch:5 agent:grok analyze code quality",
        "consensus:3 agent:grok,claude,gemini review architecture",
        "critic:2 agent:grok,gpt-4 chain:true security audit",
    ]

    for cmd in configs:
        config = BatchConfig.from_command(cmd)
        print(f"\nCommand: {cmd}")
        print(f"  - Batch size: {config.batch_size}")
        print(f"  - Agent model: {config.agent_model}")
        if config.consensus_mode:
            print(f"  - Consensus models: {config.consensus_models}")
        if config.critic_mode:
            print(f"  - Critic chain: {config.critic_chain}")

    print("\n" + "=" * 50 + "\n")


def grok_with_tools():
    """Use Grok with MCP tools."""
    try:
        from hanzo_mcp.tools.agent.cli_tools import GrokCLITool

        print("Grok CLI Tool Configuration:")
        grok_tool = GrokCLITool()

        print(f"Tool name: {grok_tool.name}")
        print(f"Description: {grok_tool.description}")
        print(f"Default model: {grok_tool.default_model}")
        print(f"API key env: {grok_tool.api_key_env}")

        # Get auth environment
        env = grok_tool.get_auth_env()
        if "XAI_API_KEY" in env:
            print("✅ XAI_API_KEY is configured")
        else:
            print("⚠️ XAI_API_KEY not found in environment")

    except ImportError:
        print("hanzo-mcp not installed. Install with: pip install hanzo-mcp")

    print("\n" + "=" * 50 + "\n")


def main():
    """Run all Grok examples."""
    print("=" * 50)
    print("xAI Grok Examples with Hanzo SDK")
    print("=" * 50 + "\n")

    # Check for API key
    if not os.environ.get("XAI_API_KEY"):
        print("⚠️ Warning: XAI_API_KEY not set")
        print("Get your API key from https://x.ai/api")
        print("Set it with: export XAI_API_KEY='your-key-here'")
        print("\nRunning examples that don't require actual API calls...\n")

        # Run non-API examples
        batch_operations_with_grok()
        grok_with_tools()
        return

    # Run all examples
    try:
        # Basic usage
        basic_grok_usage()

        # Streaming
        streaming_grok()

        # Async operations
        asyncio.run(async_grok_usage())

        # Batch operations
        batch_operations_with_grok()

        # MCP tools
        grok_with_tools()

        print("✅ All Grok examples completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set XAI_API_KEY environment variable")
        print("2. Set HANZO_API_KEY environment variable (or pass api_key to client)")
        print("3. Installed hanzoai: pip install hanzoai")
        print("4. (Optional) Installed hanzo-mcp: pip install hanzo-mcp")


if __name__ == "__main__":
    main()
