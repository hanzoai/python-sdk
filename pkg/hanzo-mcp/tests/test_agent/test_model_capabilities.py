"""Tests for model capability checking functions."""

from hanzo_mcp.tools.agent.tool_adapter import (
    supports_parallel_function_calling,
)


class TestModelCapabilities:
    """Tests for model capability checking functions."""

    def test_supports_parallel_function_calling(self):
        """Test that supports_parallel_function_calling properly identifies capable models."""
        # Test models that support parallel function calling
        assert supports_parallel_function_calling("gpt-4-turbo-preview") is True
        assert supports_parallel_function_calling("openai/gpt-4-turbo-preview") is True
        assert supports_parallel_function_calling("gpt-4o") is True
        assert supports_parallel_function_calling("openai/gpt-4o-mini") is True
        assert supports_parallel_function_calling("claude-3-5-sonnet-20241022") is True
        assert supports_parallel_function_calling("anthropic/claude-3-opus") is True

        # Test models that don't support parallel function calling
        assert supports_parallel_function_calling("gpt-4") is False
        assert supports_parallel_function_calling("gpt-3.5") is False
        assert supports_parallel_function_calling("text-davinci-003") is False
        assert supports_parallel_function_calling("unknown-model") is False
