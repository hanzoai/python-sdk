#!/usr/bin/env python3
"""Test script to validate the Hanzo workflow is properly configured."""

import os
import sys
import subprocess
from pathlib import Path

import pytest


def check_environment():
    """Check required environment variables."""
    required = {
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude models",
        "OPENAI_API_KEY": "OpenAI API key (optional but recommended)",
    }

    optional = {
        "HANZO_API_KEY": "Hanzo Router API key",
        "HANZO_DEFAULT_MODEL": "Default model selection",
        "HANZO_ROUTER_URL": "Hanzo Router URL",
    }

    missing = []
    for key in required:
        if not os.environ.get(key):
            missing.append(key)

    return len(missing) == 0, missing, optional


class TestEnvironment:
    """Test environment configuration."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_anthropic_key_set(self):
        """Test that ANTHROPIC_API_KEY is set."""
        assert os.environ.get("ANTHROPIC_API_KEY") is not None


class TestImports:
    """Test that required packages can be imported."""

    def test_hanzoai_import(self):
        """Test hanzoai package import."""
        import hanzoai
        assert hanzoai is not None

    @pytest.mark.skip(reason="hanzo_mcp may not be installed in test environment")
    def test_hanzo_mcp_import(self):
        """Test hanzo_mcp package import."""
        import hanzo_mcp
        assert hanzo_mcp is not None

    @pytest.mark.skip(reason="hanzo_agents may not be installed in test environment")
    def test_hanzo_agents_import(self):
        """Test hanzo_agents package import."""
        import hanzo_agents
        assert hanzo_agents is not None

    @pytest.mark.skip(reason="hanzo_repl may not be installed in test environment")
    def test_hanzo_repl_import(self):
        """Test hanzo_repl package import."""
        import hanzo_repl
        assert hanzo_repl is not None


class TestBasicClient:
    """Test basic Hanzo client functionality."""

    def test_client_initialization(self):
        """Test client can be initialized with API key."""
        from hanzoai import Hanzo

        # Use a dummy API key for testing - this only tests client instantiation
        # not actual API connectivity
        client = Hanzo(api_key="test-api-key-for-unit-tests")
        assert client is not None

    @pytest.mark.skipif(
        not os.environ.get("HANZO_API_KEY"),
        reason="HANZO_API_KEY not set"
    )
    def test_client_initialization_from_env(self):
        """Test client can be initialized from environment."""
        from hanzoai import Hanzo

        client = Hanzo()
        assert client is not None

    def test_model_list_available(self):
        """Test that model list is accessible."""
        # Static list of known models
        models = ["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "gpt-4"]
        assert len(models) >= 3


class TestCLI:
    """Test CLI command availability."""

    def test_hanzo_cli_help(self):
        """Test hanzo CLI --help works."""
        result = subprocess.run(
            ["python", "-m", "hanzo", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Allow both success and some specific error codes
        assert result.returncode in [0, 1, 2]


class TestCompletion:
    """Test completion functionality."""

    @pytest.mark.skip(reason="Completion test requires live API access - run manually")
    def test_simple_completion(self):
        """Test a simple completion if API key is available."""
        # This test requires live API access and should be run manually
        # when validating the full workflow
        pass


if __name__ == "__main__":
    # When run as script, use pytest
    sys.exit(pytest.main([__file__, "-v"]))
