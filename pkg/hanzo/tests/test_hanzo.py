"""Basic tests for hanzo package."""

import sys
import os
# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


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
    from hanzo.dev import run_dev_orchestrator, HanzoDevOrchestrator
    assert run_dev_orchestrator is not None
    assert HanzoDevOrchestrator is not None


def test_orchestrator_config():
    """Test orchestrator configuration module."""
    from hanzo.orchestrator_config import get_orchestrator_config, OrchestratorMode
    
    # Test getting a predefined config
    config = get_orchestrator_config("gpt-4")
    assert config is not None
    assert config.primary_model == "gpt-4"
    
    # Test router mode
    config = get_orchestrator_config("router:gpt-5")
    assert config.mode == OrchestratorMode.ROUTER
    assert config.primary_model == "router:gpt-5"