"""Basic tests for hanzo package."""

import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_import():
    """Test that hanzo package can be imported."""
    import hanzo

    assert hanzo is not None


def test_cli_exists():
    """Test that CLI module exists."""
    import hanzo.cli

    assert hanzo.cli is not None


def test_dev_module():
    """Test that dev module exists and has key functions."""
    from hanzo.dev import HanzoDevOrchestrator, run_dev_orchestrator

    assert run_dev_orchestrator is not None
    assert HanzoDevOrchestrator is not None


def test_orchestrator_config():
    """Test orchestrator configuration module."""
    from hanzo.orchestrator_config import OrchestratorMode, get_orchestrator_config

    # Test getting a predefined config
    config = get_orchestrator_config("gpt-4")
    assert config is not None
    assert config.primary_model == "gpt-4"

    # Test router mode
    config = get_orchestrator_config("router:gpt-5")
    assert config.mode == OrchestratorMode.ROUTER
    assert config.primary_model == "router:gpt-5"


def test_memory_manager():
    """Test memory manager functionality."""
    from hanzo.memory_manager import MemoryManager

    manager = MemoryManager("/tmp/test_hanzo")

    # Test adding memory
    memory_id = manager.add_memory("Test memory", type="fact")
    assert memory_id is not None

    # Test retrieving memories
    memories = manager.get_memories()
    assert len(memories) > 0

    # Test removing memory
    success = manager.remove_memory(memory_id)
    assert success is True


def test_fallback_handler():
    """Test fallback handler."""
    from hanzo.fallback_handler import FallbackHandler

    handler = FallbackHandler()

    # Should always have at least free APIs available
    assert handler.available_options["free_apis"] is True

    # Should have fallback order
    assert len(handler.fallback_order) > 0

    # Should get best option
    best = handler.get_best_option()
    assert best is not None
