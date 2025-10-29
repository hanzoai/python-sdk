"""Test Training-Free GRPO integration in Python SDK."""

import os
import tempfile
from pathlib import Path

import pytest


def test_grpo_imports():
    """Test that all GRPO components can be imported."""
    from hanzoai.grpo import (
        APIModelAdapter,
        APIModelConfig,
        DeepSeekAdapter,
        ExperienceManager,
        LLMClient,
        OpenAIAdapter,
        SemanticExtractor,
        Trajectory,
    )

    # Verify classes exist
    assert ExperienceManager is not None
    assert SemanticExtractor is not None
    assert Trajectory is not None
    assert LLMClient is not None
    assert APIModelAdapter is not None
    assert DeepSeekAdapter is not None
    assert OpenAIAdapter is not None
    assert APIModelConfig is not None


def test_experience_manager_basic():
    """Test basic ExperienceManager functionality."""
    from hanzoai.grpo import ExperienceManager

    with tempfile.TemporaryDirectory() as tmpdir:
        exp_path = Path(tmpdir) / "experiences.json"

        # Create manager
        manager = ExperienceManager(checkpoint_path=str(exp_path))

        # Add experiences
        exp_id1 = manager.add("When solving equations, isolate the variable.")
        exp_id2 = manager.add("Always check your answer by substitution.")

        assert len(manager.experiences) == 2
        assert exp_id1 == "G0"
        assert exp_id2 == "G1"

        # Format for prompt
        formatted = manager.format_for_prompt()
        assert "[G0]" in formatted
        assert "[G1]" in formatted
        assert "isolate the variable" in formatted

        # Save and reload
        manager.save(str(exp_path))
        assert exp_path.exists()

        # Load in new manager
        manager2 = ExperienceManager(checkpoint_path=str(exp_path))
        assert len(manager2.experiences) == 2
        assert manager2.experiences[exp_id1] == manager.experiences[exp_id1]


def test_trajectory_dataclass():
    """Test Trajectory dataclass."""
    from hanzoai.grpo import Trajectory

    traj = Trajectory(
        query="What is 2+2?",
        output="The answer is 4.",
        reward=1.0,
        groundtruth="4",
    )

    assert traj.query == "What is 2+2?"
    assert traj.output == "The answer is 4."
    assert traj.reward == 1.0
    assert traj.groundtruth == "4"
    assert traj.summary is None


def test_api_model_config():
    """Test APIModelConfig dataclass."""
    from hanzoai.grpo import APIModelConfig

    config = APIModelConfig(
        api_key="test-key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.7,
    )

    assert config.api_key == "test-key"
    assert config.base_url == "https://api.deepseek.com/v1"
    assert config.model == "deepseek-chat"
    assert config.temperature == 0.7


def test_experience_operations():
    """Test experience CRUD operations."""
    from hanzoai.grpo import ExperienceManager

    manager = ExperienceManager()

    # Add
    id1 = manager.add("Experience 1")
    id2 = manager.add("Experience 2")
    id3 = manager.add("Experience 3")

    assert len(manager.experiences) == 3

    # Delete
    manager.delete(id2)
    assert len(manager.experiences) == 2
    assert id2 not in manager.experiences

    # Modify
    manager.modify(id1, "Modified Experience 1")
    assert manager.experiences[id1] == "Modified Experience 1"

    # Merge
    merged_id = manager.merge([id1, id3], "Merged Experience")
    assert merged_id in manager.experiences
    assert manager.experiences[merged_id] == "Merged Experience"
    assert id1 not in manager.experiences
    assert id3 not in manager.experiences


def test_apply_operations():
    """Test applying batch operations."""
    from hanzoai.grpo import ExperienceManager

    manager = ExperienceManager()
    id1 = manager.add("Experience 1")
    id2 = manager.add("Experience 2")

    operations = [
        {"option": "add", "experience": "New experience from LLM"},
        {"option": "modify", "modified_from": id1, "experience": "Modified by LLM"},
        {"option": "delete", "delete_id": id2},
    ]

    manager.apply_operations(operations)

    assert len(manager.experiences) == 2  # 1 original - 1 deleted + 1 added
    assert manager.experiences[id1] == "Modified by LLM"
    assert id2 not in manager.experiences


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_deepseek_adapter_basic():
    """Test DeepSeekAdapter basic functionality (requires API key)."""
    from hanzoai.grpo import DeepSeekAdapter

    api_key = os.getenv("DEEPSEEK_API_KEY")
    adapter = DeepSeekAdapter(api_key=api_key, model="deepseek-chat")

    # Test basic generation
    response = adapter.generate("What is 2+2?", max_tokens=50)
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)
def test_generate_with_experiences():
    """Test generation with experience injection."""
    from hanzoai.grpo import DeepSeekAdapter, ExperienceManager

    api_key = os.getenv("DEEPSEEK_API_KEY")
    adapter = DeepSeekAdapter(api_key=api_key)
    exp_manager = ExperienceManager()

    # Add some experiences
    exp_manager.add("When solving math problems, show your work step by step.")
    exp_manager.add("Always check your answer makes sense.")

    # Generate with experiences
    query = "What is 15 * 7?"
    response = adapter.generate_with_experiences(
        query=query,
        experiences=exp_manager.format_for_prompt(),
        max_tokens=200,
    )

    assert isinstance(response, str)
    assert len(response) > 0


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Testing GRPO imports...")
    test_grpo_imports()
    print("✓ Imports successful")

    print("\nTesting ExperienceManager...")
    test_experience_manager_basic()
    print("✓ ExperienceManager works")

    print("\nTesting Trajectory dataclass...")
    test_trajectory_dataclass()
    print("✓ Trajectory works")

    print("\nTesting APIModelConfig...")
    test_api_model_config()
    print("✓ APIModelConfig works")

    print("\nTesting experience operations...")
    test_experience_operations()
    print("✓ Experience operations work")

    print("\nTesting apply_operations...")
    test_apply_operations()
    print("✓ Apply operations works")

    if os.getenv("DEEPSEEK_API_KEY"):
        print("\nTesting DeepSeekAdapter (API key found)...")
        test_deepseek_adapter_basic()
        print("✓ DeepSeekAdapter works")

        print("\nTesting generate_with_experiences...")
        test_generate_with_experiences()
        print("✓ Generate with experiences works")
    else:
        print("\n⚠ Skipping API tests (DEEPSEEK_API_KEY not set)")

    print("\n✅ ALL TESTS PASSED!")
