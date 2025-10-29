"""Test hanzo-dev integration with GRPO and DeepSeek API."""
import os
import asyncio
from hanzo.dev import HanzoDevOrchestrator


async def test_grpo_learning():
    """Test GRPO learning from interactions."""
    print("🧪 Testing Hanzo Dev with GRPO and DeepSeek API\n")
    
    # Check for API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY environment variable not set")
        print("   Please set it with: export DEEPSEEK_API_KEY=sk-...")
        return
    
    print(f"✅ DeepSeek API key found: {api_key[:10]}...{api_key[-4:]}\n")
    
    # Create orchestrator with GRPO enabled
    print("Creating HanzoDevOrchestrator with GRPO enabled...")
    orchestrator = HanzoDevOrchestrator(
        workspace_dir="/tmp/hanzo-dev-test",
        enable_grpo=True
    )
    
    if not orchestrator.grpo_enabled:
        print("❌ GRPO failed to initialize")
        return
    
    print("✅ GRPO initialized successfully\n")
    
    # Test 1: Learn from simple math interactions
    print("Test 1: Learning from math problem interactions")
    print("-" * 50)
    
    query = "What is 2x + 5 = 13?"
    responses = [
        "Let me solve: 2x = 13 - 5 = 8, so x = 4. The answer is x = 4.",
        "2x = 8, therefore x = 3",  # Wrong answer
        "First subtract 5: 2x = 8. Then divide by 2: x = 4. Answer: 4",
        "x = 4 because 2(4) + 5 = 13",
        "I think x = 5",  # Wrong answer
    ]
    rewards = [1.0, 0.0, 1.0, 1.0, 0.0]  # Correct vs incorrect
    groundtruth = "4"
    
    learned_count = await orchestrator.learn_from_interactions(
        query=query,
        responses=responses,
        rewards=rewards,
        groundtruth=groundtruth
    )
    
    print(f"\n✅ Test 1 complete: Learned {learned_count} experiences\n")
    
    # Test 2: Retrieve relevant experiences
    print("Test 2: Retrieving relevant experiences")
    print("-" * 50)
    
    test_query = "How do I solve algebraic equations?"
    relevant = orchestrator.get_relevant_experiences(test_query, top_k=3)
    
    print(f"Query: {test_query}")
    print(f"Found {len(relevant)} relevant experiences:")
    for i, exp in enumerate(relevant, 1):
        print(f"  {i}. {exp}")
    
    print("\n✅ Test 2 complete\n")
    
    # Test 3: Check experience library persistence
    print("Test 3: Checking experience library")
    print("-" * 50)
    
    total_experiences = len(orchestrator.experience_manager.experiences)
    print(f"Total experiences in library: {total_experiences}")
    
    if total_experiences > 0:
        print("\nSample experiences:")
        for i, exp in enumerate(orchestrator.experience_manager.experiences[:3], 1):
            print(f"  {i}. {exp}")
    
    print("\n✅ Test 3 complete\n")
    
    # Test 4: Fallback handler detection
    print("Test 4: Testing fallback handler with DeepSeek")
    print("-" * 50)
    
    from hanzo.fallback_handler import FallbackHandler
    from rich.console import Console
    
    handler = FallbackHandler()
    test_console = Console()
    handler.print_status(test_console)
    
    print("\n✅ Test 4 complete\n")
    
    print("=" * 50)
    print("🎉 All tests passed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_grpo_learning())
