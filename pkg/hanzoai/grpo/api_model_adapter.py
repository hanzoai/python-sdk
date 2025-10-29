# Copyright 2025 Zoo Labs Foundation Inc. and the Gym team.
#
# API Model Adapter for Training-Free GRPO
# Enables using DeepSeek API-hosted models as the target model
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

from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class APIModelConfig:
    """Configuration for API-hosted models.
    
    Supports DeepSeek, OpenAI, and any OpenAI-compatible API.
    """
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95


class APIModelAdapter:
    """Adapter for using API-hosted models in Training-Free GRPO.
    
    This enables using models like:
    - DeepSeek-V3 (deepseek-chat, deepseek-reasoner)
    - OpenAI GPT-4o (gpt-4o, gpt-4o-mini)
    - Any OpenAI-compatible API
    
    Benefits over local models:
    - No GPU required
    - Faster inference (optimized infrastructure)
    - Better base models (DeepSeek-V3 is SOTA)
    - Lower total cost (no local compute)
    - Easy scaling
    
    Example:
        >>> config = APIModelConfig(
        ...     api_key="sk-xxx",
        ...     base_url="https://api.deepseek.com/v1",
        ...     model="deepseek-chat"
        ... )
        >>> adapter = APIModelAdapter(config)
        >>> response = adapter.generate("What is 5 + 3?")
        >>> print(response)  # "8"
    """

    def __init__(self, config: APIModelConfig):
        """Initialize API model adapter.
        
        Args:
            config: API model configuration
        """
        self.config = config
        
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not found. Install with: pip install openai"
            )
        
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    def generate(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response from the API model.
        
        Args:
            prompt: User prompt/query
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            system_prompt: Optional system prompt
            
        Returns:
            response: Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            top_p=self.config.top_p
        )
        
        return response.choices[0].message.content
    
    def generate_batch(
        self, 
        prompts: List[str],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> List[str]:
        """Generate responses for a batch of prompts.
        
        Note: Currently sequential. For true parallel execution,
        use asyncio version or API batching features.
        
        Args:
            prompts: List of prompts
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            system_prompt: Optional system prompt
            
        Returns:
            responses: List of generated texts
        """
        responses = []
        for prompt in prompts:
            response = self.generate(
                prompt, 
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
            responses.append(response)
        return responses
    
    def generate_with_experiences(
        self,
        query: str,
        experiences: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response with experiences injected into prompt.
        
        This is the core method for Training-Free GRPO rollout generation.
        
        Args:
            query: Problem/query to solve
            experiences: Formatted experience library
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            response: Generated solution/output
        """
        # Inject experiences into prompt
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
            max_tokens=max_tokens
        )
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"APIModelAdapter(model={self.config.model}, base_url={self.config.base_url})"


class DeepSeekAdapter(APIModelAdapter):
    """Convenience wrapper for DeepSeek models.
    
    Supports:
    - deepseek-chat (V3, recommended for Training-Free GRPO)
    - deepseek-reasoner (V3 with reasoning traces)
    
    Example:
        >>> adapter = DeepSeekAdapter(
        ...     api_key="sk-xxx",
        ...     model="deepseek-chat"
        ... )
        >>> response = adapter.generate("Solve: x + 5 = 10")
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7
    ):
        """Initialize DeepSeek adapter.
        
        Args:
            api_key: DeepSeek API key
            model: Model name (deepseek-chat or deepseek-reasoner)
            temperature: Sampling temperature
        """
        config = APIModelConfig(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model,
            temperature=temperature
        )
        super().__init__(config)


class OpenAIAdapter(APIModelAdapter):
    """Convenience wrapper for OpenAI models.
    
    Supports:
    - gpt-4o (latest GPT-4 Omni)
    - gpt-4o-mini (smaller, faster, cheaper)
    - o1-preview (reasoning model)
    
    Example:
        >>> adapter = OpenAIAdapter(
        ...     api_key="sk-xxx",
        ...     model="gpt-4o-mini"
        ... )
        >>> response = adapter.generate("Solve: x + 5 = 10")
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        """Initialize OpenAI adapter.
        
        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4o, gpt-4o-mini, etc.)
            temperature: Sampling temperature
        """
        config = APIModelConfig(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model=model,
            temperature=temperature
        )
        super().__init__(config)
