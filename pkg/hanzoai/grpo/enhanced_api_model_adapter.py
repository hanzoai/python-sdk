# Copyright 2025 Zoo Labs Foundation Inc. and the Gym team.
#
# Enhanced API Model Adapter for Training-Free GRPO
# Based on Tencent youtu-agent: https://arxiv.org/abs/2510.08191v1
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import asyncio
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class EnhancedAPIModelConfig:
    """Enhanced configuration for API-hosted models with full feature support.

    Attributes:
        api_key: API key (can be set via HANZO_GRPO_API_KEY or DEEPSEEK_API_KEY env var)
        base_url: API base URL (default: https://api.deepseek.com/v1)
        model: Model name (e.g., "deepseek-chat", "gpt-4o", "o1-preview")
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        max_retries: Maximum retry attempts
        retry_delay: Initial retry delay in seconds (exponential backoff)
        timeout: Request timeout in seconds
        support_reasoning: Whether model supports reasoning content (e.g., o1 models)
    """

    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    support_reasoning: bool = False

    @classmethod
    def from_env(cls, **kwargs) -> "EnhancedAPIModelConfig":
        """Create config from environment variables with overrides.

        Environment variables:
        - HANZO_GRPO_API_KEY or DEEPSEEK_API_KEY: API key
        - HANZO_GRPO_BASE_URL: API base URL
        - HANZO_GRPO_MODEL: Model name
        - HANZO_GRPO_MAX_RETRIES: Maximum retries
        - HANZO_GRPO_TIMEOUT: Request timeout

        Args:
            **kwargs: Override any config parameter

        Returns:
            EnhancedAPIModelConfig instance
        """
        api_key = (
            kwargs.get("api_key")
            or os.getenv("HANZO_GRPO_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        if not api_key:
            raise ValueError(
                "API key required. Set HANZO_GRPO_API_KEY or DEEPSEEK_API_KEY env var"
            )

        defaults = {
            "api_key": api_key,
            "base_url": os.getenv("HANZO_GRPO_BASE_URL", "https://api.deepseek.com/v1"),
            "model": os.getenv("HANZO_GRPO_MODEL", "deepseek-chat"),
            "max_retries": int(os.getenv("HANZO_GRPO_MAX_RETRIES", "3")),
            "timeout": float(os.getenv("HANZO_GRPO_TIMEOUT", "0")) or None,
        }

        # Merge with provided kwargs
        defaults.update(kwargs)

        return cls(**defaults)


class EnhancedAPIModelAdapter:
    """Enhanced API model adapter with retry, reasoning, and async support.

    Features:
    - Automatic retry with exponential backoff
    - Reasoning content support (for o1 models)
    - Async generation with timeout
    - Environment variable configuration
    - Experience injection for Training-Free GRPO
    """

    def __init__(self, config: EnhancedAPIModelConfig):
        """Initialize enhanced adapter.

        Args:
            config: Enhanced API model configuration
        """
        from openai import OpenAI, AsyncOpenAI

        self.config = config
        self.client = OpenAI(
            api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
        )
        self.async_client = AsyncOpenAI(
            api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
        )

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_reasoning: bool = False,
    ) -> str | Tuple[str, Optional[str]]:
        """Generate response with retry logic.

        Args:
            prompt: User prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            return_reasoning: If True, return (response, reasoning) tuple

        Returns:
            Response string, or (response, reasoning) tuple if return_reasoning=True
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=tokens,
                    top_p=self.config.top_p,
                )

                response_text = response.choices[0].message.content.strip()

                if return_reasoning and self.config.support_reasoning:
                    reasoning = getattr(
                        response.choices[0].message, "reasoning_content", None
                    )
                    return response_text, reasoning

                return response_text

            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    print(
                        f"Generation failed (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                    )
                    print(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise Exception(
                        f"Generation failed after {self.config.max_retries} attempts: {e}"
                    )

    async def generate_async(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_reasoning: bool = False,
        timeout: Optional[float] = None,
    ) -> str | Tuple[str, Optional[str]]:
        """Generate response asynchronously with timeout.

        Args:
            prompt: User prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            return_reasoning: If True, return (response, reasoning) tuple
            timeout: Request timeout (overrides config.timeout)

        Returns:
            Response string, or (response, reasoning) tuple if return_reasoning=True
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        request_timeout = timeout or self.config.timeout

        for attempt in range(self.config.max_retries):
            try:

                async def make_request():
                    response = await self.async_client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temp,
                        max_tokens=tokens,
                        top_p=self.config.top_p,
                    )
                    return response

                if request_timeout:
                    response = await asyncio.wait_for(
                        make_request(), timeout=request_timeout
                    )
                else:
                    response = await make_request()

                response_text = response.choices[0].message.content.strip()

                if return_reasoning and self.config.support_reasoning:
                    reasoning = getattr(
                        response.choices[0].message, "reasoning_content", None
                    )
                    return response_text, reasoning

                return response_text

            except asyncio.TimeoutError:
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    print(
                        f"Generation timeout (attempt {attempt + 1}/{self.config.max_retries})"
                    )
                    print(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise Exception(
                        f"Generation timeout after {self.config.max_retries} attempts"
                    )
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    print(
                        f"Generation failed (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                    )
                    print(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise Exception(
                        f"Generation failed after {self.config.max_retries} attempts: {e}"
                    )

    def generate_with_experiences(
        self,
        query: str,
        experiences: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_reasoning: bool = False,
    ) -> str | Tuple[str, Optional[str]]:
        """Generate response with experiences injected into prompt.

        Args:
            query: User query/problem
            experiences: Formatted experiences string
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            return_reasoning: If True, return (response, reasoning) tuple

        Returns:
            Response string, or (response, reasoning) tuple if return_reasoning=True
        """
        if experiences and experiences != "None":
            enhanced_prompt = f"""Please solve the problem:
{query}

When solving problems, you MUST first carefully read and understand the helpful instructions and experiences:
{experiences}

Now solve the problem step by step."""
        else:
            enhanced_prompt = f"""Please solve the problem:
{query}

Solve the problem step by step."""

        return self.generate(
            enhanced_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            return_reasoning=return_reasoning,
        )

    async def generate_with_experiences_async(
        self,
        query: str,
        experiences: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_reasoning: bool = False,
        timeout: Optional[float] = None,
    ) -> str | Tuple[str, Optional[str]]:
        """Generate response with experiences asynchronously.

        Args:
            query: User query/problem
            experiences: Formatted experiences string
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            return_reasoning: If True, return (response, reasoning) tuple
            timeout: Request timeout

        Returns:
            Response string, or (response, reasoning) tuple if return_reasoning=True
        """
        if experiences and experiences != "None":
            enhanced_prompt = f"""Please solve the problem:
{query}

When solving problems, you MUST first carefully read and understand the helpful instructions and experiences:
{experiences}

Now solve the problem step by step."""
        else:
            enhanced_prompt = f"""Please solve the problem:
{query}

Solve the problem step by step."""

        return await self.generate_async(
            enhanced_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            return_reasoning=return_reasoning,
            timeout=timeout,
        )


class EnhancedDeepSeekAdapter(EnhancedAPIModelAdapter):
    """Convenience wrapper for DeepSeek models with enhanced features."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: Optional[float] = None,
    ):
        """Initialize DeepSeek adapter with env var fallback.

        Args:
            api_key: API key (or set DEEPSEEK_API_KEY env var)
            model: Model name
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
            timeout: Request timeout
        """
        config = EnhancedAPIModelConfig.from_env(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout,
        )
        super().__init__(config)


class EnhancedOpenAIAdapter(EnhancedAPIModelAdapter):
    """Convenience wrapper for OpenAI models with enhanced features."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        support_reasoning: bool = False,
    ):
        """Initialize OpenAI adapter with env var fallback.

        Args:
            api_key: API key (or set OPENAI_API_KEY env var)
            model: Model name (e.g., "gpt-4o", "o1-preview")
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
            timeout: Request timeout
            support_reasoning: Enable for o1 models
        """
        config = EnhancedAPIModelConfig(
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url="https://api.openai.com/v1",
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout,
            support_reasoning=support_reasoning,
        )
        super().__init__(config)
