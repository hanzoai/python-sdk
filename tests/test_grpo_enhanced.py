"""Test enhanced Training-Free GRPO features with full Tencent parity."""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest


def test_enhanced_imports():
    """Test that all enhanced GRPO components can be imported."""
    from hanzoai.grpo import (
        EnhancedAPIModelAdapter,
        EnhancedAPIModelConfig,
        EnhancedDeepSeekAdapter,
        EnhancedLLMClient,
        EnhancedOpenAIAdapter,
        EnhancedSemanticExtractor,
        EnhancedTrajectory,
        rollout_with_timeout,
    )

    assert EnhancedSemanticExtractor is not None
    assert EnhancedLLMClient is not None
    assert EnhancedTrajectory is not None
    assert EnhancedAPIModelAdapter is not None
    assert EnhancedDeepSeekAdapter is not None
    assert EnhancedOpenAIAdapter is not None
    assert EnhancedAPIModelConfig is not None
    assert rollout_with_timeout is not None
    print("✓ All enhanced imports successful")


def test_enhanced_trajectory():
    """Test enhanced trajectory with reasoning and retry count."""
    from hanzoai.grpo import EnhancedTrajectory

    traj = EnhancedTrajectory(
        query="What is 2+2?",
        output="The answer is 4.",
        reward=1.0,
        groundtruth="4",
        reasoning="First, I identify this as addition. Then I add 2+2=4.",
        retry_count=1,
        task_time=1.5,
    )

    assert traj.query == "What is 2+2?"
    assert traj.reasoning == "First, I identify this as addition. Then I add 2+2=4."
    assert traj.retry_count == 1
    assert traj.task_time == 1.5
    print("✓ Enhanced trajectory works")


def test_enhanced_config_from_env():
    """Test enhanced config creation from environment variables."""
    from hanzoai.grpo import EnhancedAPIModelConfig

    # Set test env vars
    os.environ["HANZO_GRPO_API_KEY"] = "test-key"
    os.environ["HANZO_GRPO_BASE_URL"] = "https://test.api.com"
    os.environ["HANZO_GRPO_MODEL"] = "test-model"
    os.environ["HANZO_GRPO_MAX_RETRIES"] = "5"

    config = EnhancedAPIModelConfig.from_env()

    assert config.api_key == "test-key"
    assert config.base_url == "https://test.api.com"
    assert config.model == "test-model"
    assert config.max_retries == 5

    # Test override
    config2 = EnhancedAPIModelConfig.from_env(model="override-model")
    assert config2.model == "override-model"

    # Cleanup
    del os.environ["HANZO_GRPO_API_KEY"]
    del os.environ["HANZO_GRPO_BASE_URL"]
    del os.environ["HANZO_GRPO_MODEL"]
    del os.environ["HANZO_GRPO_MAX_RETRIES"]

    print("✓ Enhanced config from env works")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_enhanced_llm_client_with_retry():
    """Test enhanced LLM client with retry logic."""
    from hanzoai.grpo import EnhancedLLMClient

    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = EnhancedLLMClient(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        max_retries=3,
    )

    # Test basic chat
    response = client.chat("What is 2+2?", max_tokens=50)
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"✓ Enhanced LLM client works (response: {len(response)} chars)")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_enhanced_deepseek_adapter():
    """Test enhanced DeepSeek adapter with retry and env config."""
    from hanzoai.grpo import EnhancedDeepSeekAdapter

    api_key = os.getenv("DEEPSEEK_API_KEY")
    adapter = EnhancedDeepSeekAdapter(api_key=api_key, max_retries=2)

    # Test basic generation
    response = adapter.generate("What is 3+3?", max_tokens=50)
    assert isinstance(response, str)
    assert len(response) > 0

    print(f"✓ Enhanced DeepSeek adapter works (response: {len(response)} chars)")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
@pytest.mark.asyncio
async def test_enhanced_adapter_async():
    """Test enhanced adapter async generation."""
    from hanzoai.grpo import EnhancedDeepSeekAdapter

    api_key = os.getenv("DEEPSEEK_API_KEY")
    adapter = EnhancedDeepSeekAdapter(api_key=api_key)

    # Test async generation
    response = await adapter.generate_async("What is 4+4?", max_tokens=50, timeout=30.0)
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"✓ Enhanced async generation works (response: {len(response)} chars)")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
@pytest.mark.asyncio
async def test_rollout_with_timeout():
    """Test async rollout with timeout."""
    from hanzoai.grpo import EnhancedDeepSeekAdapter, rollout_with_timeout

    api_key = os.getenv("DEEPSEEK_API_KEY")
    adapter = EnhancedDeepSeekAdapter(api_key=api_key)

    # Test rollout with timeout
    result = await rollout_with_timeout(
        generate_func=adapter.generate,
        query="What is 5+5?",
        timeout=30.0,
        max_retries=2,
        max_tokens=50,
    )

    assert isinstance(result, str)
    assert len(result) > 0
    print(f"✓ Rollout with timeout works (response: {len(result)} chars)")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_enhanced_semantic_extractor_with_caching():
    """Test enhanced semantic extractor with file caching."""
    from hanzoai.grpo import (
        EnhancedDeepSeekAdapter,
        EnhancedLLMClient,
        EnhancedSemanticExtractor,
        EnhancedTrajectory,
        ExperienceManager,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        api_key = os.getenv("DEEPSEEK_API_KEY")

        # Initialize components
        llm_client = EnhancedLLMClient(
            api_key=api_key,
            max_retries=2,
        )

        extractor = EnhancedSemanticExtractor(
            llm_client=llm_client,
            max_operations=2,
            max_workers=2,
            cache_dir=tmpdir,
            enable_caching=True,
            enable_parallel=True,
            filter_partial_correct=False,  # Disable for test
        )

        # Create test trajectories
        trajectories = [
            EnhancedTrajectory(
                query="What is 2x + 5 = 13?",
                output="Let me solve: 2x = 13 - 5 = 8, so x = 4",
                reward=1.0,
                groundtruth="4",
            ),
            EnhancedTrajectory(
                query="What is 2x + 5 = 13?",
                output="2x = 8, x = 3",  # Wrong
                reward=0.0,
                groundtruth="4",
            ),
        ]

        # Test Stage 1: Summarize with caching
        summarized = extractor.summarize_trajectories(trajectories, use_groundtruth=True)

        assert len(summarized) > 0
        assert "What is 2x + 5 = 13?" in summarized

        # Check cache file created
        cache_file = Path(tmpdir) / "single_rollout_summary.json"
        assert cache_file.exists()

        # Test loading from cache (should be instant)
        summarized2 = extractor.summarize_trajectories(trajectories, use_groundtruth=True)
        assert summarized == summarized2

        print(f"✓ Enhanced semantic extractor with caching works")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_enhanced_partial_correct_filtering():
    """Test partial correct filtering feature."""
    from hanzoai.grpo import (
        EnhancedLLMClient,
        EnhancedSemanticExtractor,
        EnhancedTrajectory,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        api_key = os.getenv("DEEPSEEK_API_KEY")

        llm_client = EnhancedLLMClient(api_key=api_key)

        extractor = EnhancedSemanticExtractor(
            llm_client=llm_client,
            cache_dir=tmpdir,
            filter_partial_correct=True,  # Enable filtering
        )

        # Create all-correct group (should be filtered out)
        all_correct = [
            EnhancedTrajectory(query="Q1", output="A1", reward=1.0),
            EnhancedTrajectory(query="Q1", output="A1", reward=1.0),
        ]

        # Create partial-correct group (should be processed)
        partial_correct = [
            EnhancedTrajectory(query="Q2", output="A2a", reward=1.0, groundtruth="X"),
            EnhancedTrajectory(query="Q2", output="A2b", reward=0.0, groundtruth="X"),
        ]

        trajectories = all_correct + partial_correct

        # Summarize with filtering
        summarized = extractor.summarize_trajectories(trajectories, use_groundtruth=True)

        # Should only have Q2 (partial correct)
        assert "Q2" in summarized
        # Q1 should be filtered out
        assert "Q1" not in summarized

        print("✓ Partial correct filtering works")


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Training-Free GRPO Tests")
    print("=" * 60)

    try:
        test_enhanced_imports()
        test_enhanced_trajectory()
        test_enhanced_config_from_env()

        if os.getenv("DEEPSEEK_API_KEY"):
            print("\n--- DeepSeek API Tests ---")
            test_enhanced_llm_client_with_retry()
            test_enhanced_deepseek_adapter()

            print("\n--- Async Tests ---")
            asyncio.run(test_enhanced_adapter_async())
            asyncio.run(test_rollout_with_timeout())

            print("\n--- Advanced Features Tests ---")
            test_enhanced_semantic_extractor_with_caching()
            test_enhanced_partial_correct_filtering()
        else:
            print("\n⚠ Skipping API tests (DEEPSEEK_API_KEY not set)")

        print("\n" + "=" * 60)
        print("✅ ALL ENHANCED TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
