"""Test LLM service."""

import json

import pytest

from hanzo_memory.services.llm import LLMService


class TestLLMService:
    """Test LLM service."""

    @pytest.fixture
    def llm_service(self, mock_litellm_completion):
        """Create LLM service."""

        # Configure mock to return appropriate responses
        def side_effect(*args, **kwargs):
            mock_response = type("MockResponse", (), {})()
            mock_choice = type("MockChoice", (), {})()
            mock_message = type("MockMessage", (), {})()

            # Check if JSON response is requested
            if kwargs.get("response_format", {}).get("type") == "json_object":
                mock_message.content = json.dumps(
                    {
                        "action": "add_fact",
                        "facts": [{"content": "Test fact", "metadata": {}}],
                        "reasoning": "Test reasoning",
                    }
                )
            else:
                mock_message.content = "Test response"

            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_litellm_completion.side_effect = side_effect
        return LLMService()

    def test_complete(self, llm_service):
        """Test basic completion."""
        # This will use the configured model or fallback
        result = llm_service.complete("Hello, ")
        assert isinstance(result, str)

    def test_chat(self, llm_service):
        """Test chat functionality."""
        messages = [
            {"role": "user", "content": "Hello!"},
        ]
        result = llm_service.chat(messages)
        assert isinstance(result, str)

    def test_summarize_for_knowledge_skip(self, llm_service):
        """Test knowledge summarization with skip."""
        content = "This is some test content."

        result = llm_service.summarize_for_knowledge(
            content=content,
            skip_summarization=True,
        )

        assert result["summary"] == content
        assert "knowledge_instructions" in result
        assert result["knowledge_instructions"]["action"] == "add_fact"

    def test_summarize_for_knowledge_provided(self, llm_service):
        """Test knowledge summarization with provided summary."""
        content = "Long content that needs summarization..."
        provided_summary = "Short summary"

        result = llm_service.summarize_for_knowledge(
            content=content,
            provided_summary=provided_summary,
        )

        assert result["summary"] == provided_summary
        assert "knowledge_instructions" in result

    def test_summarize_for_knowledge_generated(self, llm_service):
        """Test knowledge summarization with generation."""
        content = "This is a test document about Python programming."

        result = llm_service.summarize_for_knowledge(
            content=content,
            context="Programming tutorial",
        )

        assert "summary" in result
        assert "knowledge_instructions" in result

        # Check if instructions are valid JSON structure
        instructions = result["knowledge_instructions"]
        assert "action" in instructions
        assert "facts" in instructions
        assert "reasoning" in instructions
