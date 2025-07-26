"""LLM service for AI operations using LiteLLM."""

import json
from typing import Any, Optional

import litellm
from structlog import get_logger

from ..config import settings

logger = get_logger()

# Configure LiteLLM
litellm.drop_params = True  # Drop unsupported params instead of failing
litellm.set_verbose = False  # Disable verbose logging


class LLMService:
    """Service for LLM operations using LiteLLM."""

    def __init__(self) -> None:
        """Initialize LLM service."""
        self.default_model = settings.llm_model
        self.api_base = settings.llm_api_base
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        # Set up API keys
        if settings.llm_api_key:
            litellm.api_key = settings.llm_api_key
        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key

    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Complete a prompt using LiteLLM.

        Args:
            prompt: The prompt to complete
            model: Model to use (defaults to config)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            response_format: Optional response format ("json" for JSON mode)

        Returns:
            Generated text
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add API base if configured (for local models)
            if self.api_base:
                kwargs["api_base"] = self.api_base

            # Add response format if specified
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            return ""

    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Chat with the LLM using LiteLLM.

        Args:
            messages: List of message dicts with "role" and "content"
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            response_format: Optional response format ("json" for JSON mode)

        Returns:
            Generated response
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add API base if configured
            if self.api_base:
                kwargs["api_base"] = self.api_base

            # Add response format if specified
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = litellm.completion(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return ""

    def summarize_for_knowledge(
        self,
        content: str,
        context: Optional[str] = None,
        skip_summarization: bool = False,
        provided_summary: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Summarize content and generate knowledge update instructions.

        Args:
            content: Content to summarize
            context: Additional context
            skip_summarization: Skip summarization step
            provided_summary: Pre-provided summary

        Returns:
            JSON with summary and knowledge instructions
        """
        if skip_summarization and not provided_summary:
            # Just return the content as-is with basic instructions
            return {
                "summary": content,
                "knowledge_instructions": {
                    "action": "add_fact",
                    "facts": [{"content": content}],
                    "reasoning": "Content added without summarization",
                },
            }

        if provided_summary:
            summary = provided_summary
        else:
            # Generate summary
            summary_prompt = f"""Summarize the following content concisely, preserving key information:

Content: {content}"""
            if context:
                summary_prompt += f"\n\nContext: {context}"

            summary = self.complete(summary_prompt, temperature=0.3)

        # Generate knowledge instructions
        instruction_prompt = f"""Based on this summary, generate instructions for updating a knowledge base.
Return a JSON object with the following structure:
{{
    "action": "add_fact" or "update_fact" or "add_relation",
    "facts": [
        {{
            "content": "fact content",
            "metadata": {{"tags": [], "source": "..."}},
            "parent_id": null or "parent_fact_id"
        }}
    ],
    "reasoning": "explanation of why these facts should be added"
}}

Summary: {summary}"""

        if context:
            instruction_prompt += f"\n\nContext: {context}"

        instructions_json = self.complete(
            instruction_prompt, temperature=0.3, response_format="json"
        )

        try:
            instructions = json.loads(instructions_json)
        except json.JSONDecodeError:
            instructions = {
                "action": "add_fact",
                "facts": [{"content": summary}],
                "reasoning": "Failed to parse LLM response, using summary as fact",
            }

        return {"summary": summary, "knowledge_instructions": instructions}


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
