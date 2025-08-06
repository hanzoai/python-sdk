#!/usr/bin/env python
"""Test AI working on distributed network with local LLM."""

import asyncio
from hanzo_network import (
    create_local_agent,
    create_local_distributed_network,
    create_tool,
    check_local_llm_status
)


# Create a simple tool that simulates AI work
async def analyze_text(text: str) -> str:
    """Analyze text using AI capabilities."""
    # This would normally use the LLM, but for testing we'll simulate
    word_count = len(text.split())
    char_count = len(text)
    return f"Analysis: {word_count} words, {char_count} characters. The text appears to be about: {text[:50]}..."


async def generate_code(description: str) -> str:
    """Generate code based on description."""
    # Simulate code generation
    return f"""# Generated code for: {description}
def generated_function():
    # This would be AI-generated code
    print("Hello from generated code!")
    return True
"""


async def main():
    """Test AI working on the distributed network."""
    print("🤖 Testing AI on Distributed Network with Local LLM")
    print("=" * 60)
    
    # Check LLM status
    ollama_status = await check_local_llm_status("ollama")
    print(f"\n📡 Ollama status: {'✅ Available' if ollama_status['available'] else '❌ Not available'}")
    
    # Create AI agents
    analyzer = create_local_agent(
        name="text_analyzer",
        description="Analyzes text using AI",
        system="You are an AI text analysis agent. Use the analyze_text tool to analyze text content.",
        tools=[create_tool(name="analyze_text", description="Analyze text using AI", handler=analyze_text)],
        local_model="llama3.2"
    )
    
    coder = create_local_agent(
        name="code_generator",
        description="Generates code using AI",
        system="You are an AI code generation agent. Use the generate_code tool to create code.",
        tools=[create_tool(name="generate_code", description="Generate code from description", handler=generate_code)],
        local_model="llama3.2"
    )
    
    # Create network
    network = create_local_distributed_network(
        agents=[analyzer, coder],
        name="ai-test-network",
        node_id="ai-node",
        listen_port=15720,
        broadcast_port=15720
    )
    
    print("\n🚀 Starting AI network...")
    await network.start(wait_for_peers=0)
    
    # Test 1: Text analysis
    print("\n📝 Test 1: AI Text Analysis")
    result = await network.run(
        prompt="Analyze this text: 'Artificial intelligence is transforming how we build software'",
        initial_agent=analyzer
    )
    print(f"Result: {result['final_output']}")
    
    # Test 2: Code generation
    print("\n💻 Test 2: AI Code Generation")
    result = await network.run(
        prompt="Generate a Python function that calculates fibonacci numbers",
        initial_agent=coder
    )
    print(f"Result: {result['final_output']}")
    
    # Test 3: Multi-agent collaboration
    print("\n🤝 Test 3: AI Collaboration")
    result = await network.run(
        prompt="First analyze the concept of 'recursive algorithms', then generate code for a recursive factorial function"
    )
    print(f"Result: {result['final_output']}")
    print(f"Agents involved: {result['iterations']}")
    
    # Network stats
    status = network.get_network_status()
    print(f"\n📊 Network Stats:")
    print(f"  Node ID: {status['node_id']}")
    print(f"  Local agents: {', '.join(status['local_agents'])}")
    print(f"  Peer count: {status['peer_count']}")
    print(f"  Device: {status['device_capabilities']['model']}")
    print(f"  Memory: {status['device_capabilities']['memory'] / 1024:.1f} GB")
    
    print("\n✅ AI test complete!")
    await network.stop()


if __name__ == "__main__":
    asyncio.run(main())