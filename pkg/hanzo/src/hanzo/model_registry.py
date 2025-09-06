"""Unified Model Registry - Single source of truth for all AI model mappings.

This module provides a centralized registry for AI model configurations,
eliminating duplication and ensuring consistency across the codebase.
"""

from __future__ import annotations

from enum import Enum
from typing import Set, Dict, List, Optional
from dataclasses import field, dataclass


class ModelProvider(Enum):
    """Enumeration of AI model providers."""
    
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    XAI = "xai"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    META = "meta"
    HANZO = "hanzo"


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a single AI model."""
    
    full_name: str
    provider: ModelProvider
    aliases: Set[str] = field(default_factory=set)
    default_params: Dict[str, any] = field(default_factory=dict)
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    context_window: int = 8192
    max_output: int = 4096
    api_key_env: Optional[str] = None
    cli_command: Optional[str] = None


class ModelRegistry:
    """Centralized registry for all AI models.
    
    This is the single source of truth for model configurations,
    ensuring no duplication across the codebase.
    """
    
    _instance: Optional[ModelRegistry] = None
    _models: Dict[str, ModelConfig] = {}
    
    def __new__(cls) -> ModelRegistry:
        """Singleton pattern to ensure single registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_models()
        return cls._instance
    
    def _initialize_models(self) -> None:
        """Initialize all model configurations."""
        # Claude models
        self._register(ModelConfig(
            full_name="claude-3-5-sonnet-20241022",
            provider=ModelProvider.ANTHROPIC,
            aliases={"claude", "cc", "claude-code", "sonnet", "sonnet-4.1"},
            supports_vision=True,
            supports_tools=True,
            context_window=200000,
            max_output=8192,
            api_key_env="ANTHROPIC_API_KEY",
            cli_command="claude",
        ))
        
        self._register(ModelConfig(
            full_name="claude-opus-4-1-20250805",
            provider=ModelProvider.ANTHROPIC,
            aliases={"opus", "opus-4.1", "claude-opus"},
            supports_vision=True,
            supports_tools=True,
            context_window=200000,
            max_output=8192,
            api_key_env="ANTHROPIC_API_KEY",
            cli_command="claude",
        ))
        
        self._register(ModelConfig(
            full_name="claude-3-haiku-20240307",
            provider=ModelProvider.ANTHROPIC,
            aliases={"haiku", "claude-haiku"},
            supports_vision=True,
            supports_tools=True,
            context_window=200000,
            max_output=4096,
            api_key_env="ANTHROPIC_API_KEY",
            cli_command="claude",
        ))
        
        # OpenAI models
        self._register(ModelConfig(
            full_name="gpt-4-turbo",
            provider=ModelProvider.OPENAI,
            aliases={"gpt4", "gpt-4", "codex"},
            supports_vision=True,
            supports_tools=True,
            context_window=128000,
            max_output=4096,
            api_key_env="OPENAI_API_KEY",
            cli_command="openai",
        ))
        
        self._register(ModelConfig(
            full_name="gpt-5-turbo",
            provider=ModelProvider.OPENAI,
            aliases={"gpt5", "gpt-5"},
            supports_vision=True,
            supports_tools=True,
            context_window=256000,
            max_output=16384,
            api_key_env="OPENAI_API_KEY",
            cli_command="openai",
        ))
        
        self._register(ModelConfig(
            full_name="o1-preview",
            provider=ModelProvider.OPENAI,
            aliases={"o1", "openai-o1"},
            supports_vision=False,
            supports_tools=False,
            context_window=128000,
            max_output=32768,
            api_key_env="OPENAI_API_KEY",
            cli_command="openai",
        ))
        
        # Google models
        self._register(ModelConfig(
            full_name="gemini-1.5-pro",
            provider=ModelProvider.GOOGLE,
            aliases={"gemini", "gemini-pro"},
            supports_vision=True,
            supports_tools=True,
            context_window=2000000,
            max_output=8192,
            api_key_env="GEMINI_API_KEY",
            cli_command="gemini",
        ))
        
        self._register(ModelConfig(
            full_name="gemini-1.5-flash",
            provider=ModelProvider.GOOGLE,
            aliases={"gemini-flash", "flash"},
            supports_vision=True,
            supports_tools=True,
            context_window=1000000,
            max_output=8192,
            api_key_env="GEMINI_API_KEY",
            cli_command="gemini",
        ))
        
        # xAI models
        self._register(ModelConfig(
            full_name="grok-2",
            provider=ModelProvider.XAI,
            aliases={"grok", "xai-grok"},
            supports_vision=False,
            supports_tools=True,
            context_window=128000,
            max_output=8192,
            api_key_env="XAI_API_KEY",
            cli_command="grok",
        ))
        
        # Ollama models
        self._register(ModelConfig(
            full_name="ollama/llama-3.2-3b",
            provider=ModelProvider.OLLAMA,
            aliases={"llama", "llama-3.2", "llama3"},
            supports_vision=False,
            supports_tools=False,
            context_window=128000,
            max_output=4096,
            api_key_env=None,  # Local model
            cli_command="ollama",
        ))
        
        self._register(ModelConfig(
            full_name="ollama/mistral:7b",
            provider=ModelProvider.MISTRAL,
            aliases={"mistral", "mistral-7b"},
            supports_vision=False,
            supports_tools=False,
            context_window=32000,
            max_output=4096,
            api_key_env=None,  # Local model
            cli_command="ollama",
        ))
        
        # DeepSeek models
        self._register(ModelConfig(
            full_name="deepseek-coder-v2",
            provider=ModelProvider.DEEPSEEK,
            aliases={"deepseek", "deepseek-coder"},
            supports_vision=False,
            supports_tools=True,
            context_window=128000,
            max_output=8192,
            api_key_env="DEEPSEEK_API_KEY",
            cli_command="deepseek",
        ))
    
    def _register(self, config: ModelConfig) -> None:
        """Register a model configuration.
        
        Args:
            config: Model configuration to register
        """
        # Register by full name
        self._models[config.full_name] = config
        
        # Register all aliases
        for alias in config.aliases:
            self._models[alias.lower()] = config
    
    def get(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration by name or alias.
        
        Args:
            model_name: Model name or alias
            
        Returns:
            Model configuration or None if not found
        """
        return self._models.get(model_name.lower())
    
    def resolve(self, model_name: str) -> str:
        """Resolve model name or alias to full model name.
        
        Args:
            model_name: Model name or alias
            
        Returns:
            Full model name, or original if not found
        """
        config = self.get(model_name)
        return config.full_name if config else model_name
    
    def get_by_provider(self, provider: ModelProvider) -> List[ModelConfig]:
        """Get all models for a specific provider.
        
        Args:
            provider: Model provider
            
        Returns:
            List of model configurations
        """
        seen = set()
        results = []
        for config in self._models.values():
            if config.provider == provider and config.full_name not in seen:
                seen.add(config.full_name)
                results.append(config)
        return results
    
    def get_models_supporting(
        self,
        vision: Optional[bool] = None,
        tools: Optional[bool] = None,
        streaming: Optional[bool] = None,
    ) -> List[ModelConfig]:
        """Get models supporting specific features.
        
        Args:
            vision: Filter by vision support
            tools: Filter by tool support
            streaming: Filter by streaming support
            
        Returns:
            List of matching model configurations
        """
        seen = set()
        results = []
        
        for config in self._models.values():
            if config.full_name in seen:
                continue
                
            if vision is not None and config.supports_vision != vision:
                continue
            if tools is not None and config.supports_tools != tools:
                continue
            if streaming is not None and config.supports_streaming != streaming:
                continue
            
            seen.add(config.full_name)
            results.append(config)
        
        return results
    
    def get_api_key_env(self, model_name: str) -> Optional[str]:
        """Get the API key environment variable for a model.
        
        Args:
            model_name: Model name or alias
            
        Returns:
            Environment variable name or None
        """
        config = self.get(model_name)
        return config.api_key_env if config else None
    
    def get_cli_command(self, model_name: str) -> Optional[str]:
        """Get the CLI command for a model.
        
        Args:
            model_name: Model name or alias
            
        Returns:
            CLI command or None
        """
        config = self.get(model_name)
        return config.cli_command if config else None
    
    def list_all_models(self) -> List[str]:
        """List all unique model full names.
        
        Returns:
            List of full model names
        """
        seen = set()
        for config in self._models.values():
            seen.add(config.full_name)
        return sorted(list(seen))
    
    def list_all_aliases(self) -> Dict[str, str]:
        """List all aliases and their full names.
        
        Returns:
            Dictionary mapping aliases to full names
        """
        result = {}
        for key, config in self._models.items():
            if key != config.full_name:
                result[key] = config.full_name
        return result


# Global singleton instance
registry = ModelRegistry()


# Convenience functions
def resolve_model(model_name: str) -> str:
    """Resolve model name or alias to full model name.
    
    Args:
        model_name: Model name or alias
        
    Returns:
        Full model name
    """
    return registry.resolve(model_name)


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get model configuration.
    
    Args:
        model_name: Model name or alias
        
    Returns:
        Model configuration or None
    """
    return registry.get(model_name)


def get_api_key_env(model_name: str) -> Optional[str]:
    """Get API key environment variable for model.
    
    Args:
        model_name: Model name or alias
        
    Returns:
        Environment variable name or None
    """
    return registry.get_api_key_env(model_name)


__all__ = [
    "ModelProvider",
    "ModelConfig",
    "ModelRegistry",
    "registry",
    "resolve_model",
    "get_model_config",
    "get_api_key_env",
]