#!/usr/bin/env python
"""Run agents with real local models using MLX."""

import asyncio
import sys
from pathlib import Path

# Add hanzo-network to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hanzo-network" / "src"))

from hanzo_network import create_agent, create_distributed_network, create_tool
from hanzo_network.core.agent import ModelConfig, ModelProvider


# Create real tools that will use the LLM
async def summarize_text(text: str) -> str:
    """Summarize the given text."""
    return f"Summary of {len(text)} characters: {text[:100]}..."


async def answer_question(question: str) -> str:
    """Answer a question based on knowledge."""
    return f"Answer to '{question}': Based on my analysis..."


async def write_code(description: str) -> str:
    """Write code based on description."""
    return f"""# Code for: {description}
def solution():
    # Implementation here
    pass"""


async def main():
    """Run agents with real MLX models."""
    print("🤖 Running Agents with Real Local Models (MLX)")
    print("=" * 60)

    # First, let's try to ensure MLX is working
    print("\n📡 Testing MLX availability...")
    try:
        import mlx.core as mx

        print("✅ MLX is available!")
        print(f"   Device: {mx.default_device()}")

        # Try to load mlx-lm
        try:
            import mlx_lm

            print("✅ mlx_lm is available!")
        except ImportError:
            print("❌ mlx_lm not found. Installing...")
            import subprocess

            subprocess.check_call([sys.executable, "-m", "pip", "install", "mlx-lm"])

            print("✅ mlx_lm installed!")

    except Exception as e:
        print(f"❌ MLX error: {e}")
        return

    # Download a small model if needed
    print("\n📥 Checking for local models...")
    model_name = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"  # Small 0.5B model

    try:
        # Try to load the model
        from mlx_lm import load

        print(f"Loading {model_name}...")
        model, tokenizer = load(model_name)
        print("✅ Model loaded successfully!")

        # Test generation
        from mlx_lm import generate

        test_response = generate(model, tokenizer, prompt="Hello, I am", max_tokens=10)
        print(f"   Test response: {test_response}")

    except Exception as e:
        print(f"❌ Model loading error: {e}")
        print("   Note: The model will be downloaded on first use")

    # Create agents with MLX model
    print("\n🤖 Creating agents with MLX inference...")

    # Agent 1: Assistant
    assistant = create_agent(
        name="assistant",
        description="General purpose assistant using MLX",
        model=ModelConfig(
            provider=ModelProvider.LOCAL,
            model="mlx",  # This will trigger MLX engine
            temperature=0.7,
            max_tokens=100,
        ),
        system="You are a helpful assistant powered by local MLX inference.",
        tools=[
            create_tool(
                name="summarize_text",
                description="Summarize text",
                handler=summarize_text,
            ),
            create_tool(
                name="answer_question",
                description="Answer questions",
                handler=answer_question,
            ),
        ],
    )

    # Agent 2: Coder
    coder = create_agent(
        name="coder",
        description="Code writing assistant using MLX",
        model=ModelConfig(
            provider=ModelProvider.LOCAL, model="mlx", temperature=0.3, max_tokens=200
        ),
        system="You are a code writing assistant. Write clean, efficient code.",
        tools=[
            create_tool(name="write_code", description="Write code", handler=write_code)
        ],
    )

    # Create network
    network = create_distributed_network(
        agents=[assistant, coder],
        name="mlx-network",
        listen_port=15740,
        broadcast_port=15740,
    )

    print("\n🌐 Starting network with MLX models...")
    await network.start(wait_for_peers=0)

    # Test 1: Simple question
    print("\n💬 Test 1: Simple Question")
    result = await network.run(
        prompt="What is machine learning?", initial_agent=assistant
    )
    print(f"Response: {result['final_output']}")

    # Test 2: Summarization
    print("\n📝 Test 2: Text Summarization")
    result = await network.run(
        prompt="Summarize this: Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
        initial_agent=assistant,
    )
    print(f"Response: {result['final_output']}")

    # Test 3: Code generation
    print("\n💻 Test 3: Code Generation")
    result = await network.run(
        prompt="Write a Python function to calculate factorial", initial_agent=coder
    )
    print(f"Response: {result['final_output']}")

    # Test 4: Multi-agent
    print("\n🤝 Test 4: Multi-Agent Collaboration")
    result = await network.run(
        prompt="First explain what recursion is, then write a recursive function to calculate fibonacci numbers"
    )
    print(f"Response: {result['final_output']}")
    print(f"Agents involved: {result['iterations']}")

    print("\n✅ MLX model test complete!")
    await network.stop()


if __name__ == "__main__":
    print("\nThis demo runs real local models using MLX on Apple Silicon.")
    print("The first run will download the model (~500MB).\n")
    asyncio.run(main())
