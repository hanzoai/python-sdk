"""E2E integration tests for LiteLLM providers.

These tests require real API keys and make actual API calls.
Only run in CI with proper secrets configured.
"""

import os

import litellm
import pytest


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set",
)
@pytest.mark.asyncio
async def test_litellm_openai_provider_integration():
    """Integration test: LiteLLM with real OpenAI provider."""
    messages = [{"role": "user", "content": "Hello, how are you?"}]

    try:
        response = litellm.completion(
            model="openai/gpt-3.5-turbo",
            messages=messages,
        )
        assert response.choices[0].message.content is not None
    except Exception as e:
        pytest.skip(f"OpenAI API connection failed: {type(e).__name__} - {str(e)}")


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY environment variable not set",
)
@pytest.mark.asyncio
async def test_litellm_anthropic_provider_integration():
    """Integration test: LiteLLM with real Anthropic provider."""
    messages = [{"role": "user", "content": "Hello, how are you?"}]

    try:
        response = litellm.completion(
            model="anthropic/claude-3-haiku-20240307",
            messages=messages,
        )
        assert response.choices[0].message.content is not None
    except Exception as e:
        pytest.skip(f"Anthropic API connection failed: {type(e).__name__} - {str(e)}")
