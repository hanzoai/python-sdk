#!/usr/bin/env python
"""Demo of hanzo-network with local LLM (Ollama)."""

import asyncio
from hanzo_network import (
    create_local_agent,
    create_local_distributed_network,
    create_tool,
    check_local_llm_status,
)


# Create some demo tools
async def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"The weather in {location} is sunny and 72°F"


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception:
        return "Error: Invalid expression"


async def main():
    """Demo local LLM with hanzo-network."""
    print("🤖 Hanzo Network with Local LLM Demo")
    print("=" * 50)

    # Check Ollama status
    print("\n📡 Checking Ollama status...")
    ollama_status = await check_local_llm_status("ollama")
    print(f"Ollama available: {ollama_status['available']}")
    if ollama_status["available"]:
        print(f"Available models: {ollama_status['models']}")
    else:
        print(f"⚠️  {ollama_status['instructions']}")
        print("Continuing with mock responses...")

    # Create agents with local LLM
    weather_tool = create_tool(
        name="get_weather",
        description="Get weather for a location",
        handler=get_weather,
    )

    calc_tool = create_tool(
        name="calculate",
        description="Evaluate a mathematical expression",
        handler=calculate,
    )

    weather_agent = create_local_agent(
        name="weather_agent",
        description="Agent that provides weather information",
        system="You are a helpful weather assistant. Use the get_weather tool to answer questions about weather.",
        tools=[weather_tool],
        local_model="llama3.2",  # Use Ollama's llama3.2 model
    )

    math_agent = create_local_agent(
        name="math_agent",
        description="Agent that performs calculations",
        system="You are a helpful math assistant. Use the calculate tool to solve math problems.",
        tools=[calc_tool],
        local_model="llama3.2",
    )

    # Create distributed network
    network = create_local_distributed_network(
        agents=[weather_agent, math_agent],
        name="local-demo-network",
        node_id="demo-node",
        listen_port=15700,
        broadcast_port=15700,
    )

    print("\n🚀 Starting network...")
    await network.start(wait_for_peers=0)

    # Get network status
    status = network.get_network_status()
    print("\n📊 Network Status:")
    print(f"  Node ID: {status['node_id']}")
    print(f"  Device: {status['device_capabilities']['model']}")
    print(f"  Agents: {status['local_agents']}")

    # Test weather agent
    print("\n🌤️  Testing weather agent...")
    weather_result = await network.run(prompt="What's the weather in Tokyo?", initial_agent=weather_agent)

    if weather_result["success"]:
        print(f"Response: {weather_result['final_output']}")

    # Test math agent
    print("\n🔢 Testing math agent...")
    math_result = await network.run(prompt="Calculate 42 * 17 + 3", initial_agent=math_agent)

    if math_result["success"]:
        print(f"Response: {math_result['final_output']}")

    # Test with router (let network decide which agent)
    print("\n🤔 Testing with router...")
    auto_result = await network.run(prompt="I need to know the weather in Paris and also calculate 100 / 4")

    if auto_result["success"]:
        print(f"Response: {auto_result['final_output']}")
        print(f"Used {auto_result['iterations']} agent(s)")

    print("\n✅ Demo complete!")
    await network.stop()


if __name__ == "__main__":
    asyncio.run(main())
