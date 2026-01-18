"""Test LiteLLM with different providers."""

import litellm
import pytest
from hanzo_tools.agent.tool_adapter import convert_tools_to_openai_functions

from hanzo_mcp.tools.common.base import BaseTool


class EchoTool(BaseTool):
    """A simple tool that echoes back the input."""

    @property
    def name(self) -> str:
        """Get the tool name."""
        return "echo"

    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Echo back the input message."

    @property
    def parameters(self) -> dict:
        """Get the parameter specifications for the tool."""
        return {
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back",
                },
            },
            "required": ["message"],
            "type": "object",
        }

    @property
    def required(self) -> list[str]:
        """Get the list of required parameter names."""
        return ["message"]

    def register(self, ctx):
        """Register the tool with the context."""
        # This is a required abstract method from BaseTool
        pass

    async def call(self, ctx, **params):
        """Execute the tool with the given parameters."""
        message = params.get("message", "")
        return f"Echo: {message}"


@pytest.fixture
def echo_tool():
    """Fixture for the EchoTool."""
    return EchoTool()


def test_convert_echo_tool_to_openai_functions(echo_tool):
    """Test convert_tools_to_openai_functions with echo_tool."""
    openai_functions = convert_tools_to_openai_functions([echo_tool])

    assert len(openai_functions) == 1
    assert openai_functions[0]["type"] == "function"
    assert openai_functions[0]["function"]["name"] == "echo"
    assert (
        openai_functions[0]["function"]["description"] == "Echo back the input message."
    )
    assert "parameters" in openai_functions[0]["function"]


def test_litellm_openai_provider_mocked():
    """Test LiteLLM with OpenAI provider using mocks."""
    from unittest.mock import MagicMock, patch

    messages = [{"role": "user", "content": "Hello, how are you?"}]

    # Create mock response
    mock_message = MagicMock()
    mock_message.content = "I'm doing well, thank you!"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        litellm, "completion", return_value=mock_response
    ) as mock_completion:
        response = litellm.completion(
            model="openai/gpt-3.5-turbo",
            messages=messages,
        )

        assert response.choices[0].message.content is not None
        mock_completion.assert_called_once_with(
            model="openai/gpt-3.5-turbo",
            messages=messages,
        )


def test_litellm_anthropic_provider_mocked():
    """Test LiteLLM with Anthropic provider using mocks."""
    from unittest.mock import MagicMock, patch

    messages = [{"role": "user", "content": "Hello, how are you?"}]

    # Create mock response
    mock_message = MagicMock()
    mock_message.content = "Hello! I'm Claude, and I'm doing well."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        litellm, "completion", return_value=mock_response
    ) as mock_completion:
        response = litellm.completion(
            model="anthropic/claude-3-haiku-20240307",
            messages=messages,
        )

        assert response.choices[0].message.content is not None
        mock_completion.assert_called_once_with(
            model="anthropic/claude-3-haiku-20240307",
            messages=messages,
        )


# Integration tests moved to tests/e2e/test_litellm_integration.py
# They require real API keys and only run in CI


# Only run this test if explicitly requested with pytest -xvs tests/test_agent/test_litellm_providers.py
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
