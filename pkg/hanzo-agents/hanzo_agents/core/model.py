"""Model adapters for different LLM providers."""

from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
import os
import asyncio
from urllib.parse import urlparse


class BaseModelAdapter(ABC):
    """Base adapter for LLM models."""
    
    name: str
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Simple completion API."""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Chat completion API."""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        return {
            "name": self.name,
            "type": self.__class__.__name__
        }


class ModelRegistry:
    """Global registry for model adapters."""
    
    _adapters: Dict[str, BaseModelAdapter] = {}
    _providers: Dict[str, type[BaseModelAdapter]] = {}
    
    @classmethod
    def register_provider(cls, name: str, adapter_class: type[BaseModelAdapter]):
        """Register a provider adapter class."""
        cls._providers[name] = adapter_class
    
    @classmethod
    def get_adapter(cls, model_uri: str, **kwargs) -> BaseModelAdapter:
        """Get or create adapter for model URI.
        
        URI format: model://provider/model-name
        Examples:
            - model://anthropic/claude-3-opus
            - model://openai/gpt-4
            - model://local/llama-70b
        """
        if model_uri in cls._adapters:
            return cls._adapters[model_uri]
        
        # Parse URI
        parsed = urlparse(model_uri)
        if parsed.scheme != "model":
            raise ValueError(f"Invalid model URI: {model_uri}")
        
        provider = parsed.netloc
        model_name = parsed.path.lstrip("/")
        
        # Create adapter
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        adapter_class = cls._providers[provider]
        adapter = adapter_class(model_name, **kwargs)
        
        # Cache it
        cls._adapters[model_uri] = adapter
        return adapter


# Mock adapters for demonstration

class MockAdapter(BaseModelAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, model_name: str, **kwargs):
        self.name = f"mock/{model_name}"
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Mock completion."""
        await asyncio.sleep(0.1)  # Simulate API call
        return f"Mock response to: {prompt[:50]}..."
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Mock chat."""
        await asyncio.sleep(0.1)
        last_message = messages[-1]["content"] if messages else "No message"
        return f"Mock chat response to: {last_message[:50]}..."


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic models."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.name = f"anthropic/{model_name}"
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model_name
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Anthropic completion."""
        # In real implementation, use anthropic SDK
        return await self._mock_call(prompt, **kwargs)
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Anthropic chat."""
        # In real implementation, use anthropic SDK
        return await self._mock_call(str(messages), **kwargs)
    
    async def _mock_call(self, content: str, **kwargs) -> str:
        """Mock API call."""
        await asyncio.sleep(0.2)
        return f"Claude says: Responding to {content[:30]}..."


class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI models."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.name = f"openai/{model_name}"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model_name
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """OpenAI completion."""
        # In real implementation, use openai SDK
        return await self._mock_call(prompt, **kwargs)
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """OpenAI chat."""
        # In real implementation, use openai SDK
        return await self._mock_call(str(messages), **kwargs)
    
    async def _mock_call(self, content: str, **kwargs) -> str:
        """Mock API call."""
        await asyncio.sleep(0.15)
        return f"GPT says: Processing {content[:30]}..."


class LocalAdapter(BaseModelAdapter):
    """Adapter for local models (llama.cpp, etc.)."""
    
    def __init__(self, model_name: str, model_path: Optional[str] = None):
        self.name = f"local/{model_name}"
        self.model_path = model_path
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Local model completion."""
        # In real implementation, use llama-cpp-python or similar
        await asyncio.sleep(0.5)  # Simulate local inference
        return f"Local model says: {prompt[:40]}..."
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Local model chat."""
        await asyncio.sleep(0.5)
        return f"Local chat: {str(messages[-1])[:40]}..."


# Register default providers
ModelRegistry.register_provider("mock", MockAdapter)
ModelRegistry.register_provider("anthropic", AnthropicAdapter)
ModelRegistry.register_provider("openai", OpenAIAdapter)
ModelRegistry.register_provider("local", LocalAdapter)


# Helper functions

async def call_model(model_uri: str, prompt: str, **kwargs) -> str:
    """Simple helper to call a model."""
    adapter = ModelRegistry.get_adapter(model_uri)
    return await adapter.complete(prompt, **kwargs)


async def chat_with_model(model_uri: str, messages: List[Dict[str, Any]], **kwargs) -> str:
    """Simple helper for chat completion."""
    adapter = ModelRegistry.get_adapter(model_uri)
    return await adapter.chat(messages, **kwargs)