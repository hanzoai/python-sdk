"""LLM client for interacting with various AI providers."""

import os
from typing import Any, Dict, List, Optional, Set

import litellm
from litellm import completion, acompletion


class LLMClient:
    """Client for interacting with LLM providers."""
    
    # Provider to API key environment variables mapping
    PROVIDER_ENV_VARS = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "mistral": ["MISTRAL_API_KEY"],
        "perplexity": ["PERPLEXITY_API_KEY", "PERPLEXITYAI_API_KEY"],
        "together": ["TOGETHER_API_KEY", "TOGETHERAI_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "replicate": ["REPLICATE_API_KEY"],
        "huggingface": ["HUGGINGFACE_API_KEY", "HF_TOKEN"],
        "deepinfra": ["DEEPINFRA_API_KEY"],
        "ai21": ["AI21_API_KEY"],
        "voyage": ["VOYAGE_API_KEY"],
        "anyscale": ["ANYSCALE_API_KEY"],
        "palm": ["PALM_API_KEY"],
        "nlpcloud": ["NLPCLOUD_API_KEY"],
        "aleph_alpha": ["ALEPH_ALPHA_API_KEY"],
        "petals": ["PETALS_API_KEY"],
        "baseten": ["BASETEN_API_KEY"],
        "vllm": ["VLLM_API_KEY"],
        "ollama": [],  # No API key needed for local Ollama
        "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "vertex_ai": ["GOOGLE_APPLICATION_CREDENTIALS"],
        "sagemaker": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    }
    
    # Default models for each provider
    DEFAULT_MODELS = {
        "openai": "gpt-4-turbo-preview",
        "anthropic": "claude-3-opus-20240229",
        "google": "gemini-pro",
        "groq": "mixtral-8x7b-32768",
        "mistral": "mistral-medium",
        "perplexity": "pplx-70b-online",
        "together": "mixtral-8x7b-32768",
        "cohere": "command-r-plus",
        "ollama": "llama2",
    }
    
    def __init__(self):
        self.available_providers = self._detect_providers()
        self.current_provider = None
        self.current_model = None
        
        # Set default provider and model
        if self.available_providers:
            # Prefer certain providers in order
            preferred_order = ["anthropic", "openai", "groq", "google", "ollama"]
            for provider in preferred_order:
                if provider in self.available_providers:
                    self.current_provider = provider
                    self.current_model = self.DEFAULT_MODELS.get(provider, "gpt-3.5-turbo")
                    break
            
            # If no preferred provider, use the first available
            if not self.current_provider:
                self.current_provider = list(self.available_providers)[0]
                self.current_model = self.DEFAULT_MODELS.get(self.current_provider, "gpt-3.5-turbo")
    
    def _detect_providers(self) -> Set[str]:
        """Detect which LLM providers have API keys configured."""
        available = set()
        
        for provider, env_vars in self.PROVIDER_ENV_VARS.items():
            if not env_vars:  # No API key needed (e.g., Ollama)
                # Check if the provider is accessible
                if provider == "ollama":
                    # TODO: Check if Ollama is running
                    if os.path.exists(os.path.expanduser("~/.ollama")):
                        available.add(provider)
                continue
            
            # Check if any of the environment variables are set
            for env_var in env_vars:
                if os.getenv(env_var):
                    available.add(provider)
                    break
        
        return available
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return sorted(list(self.available_providers))
    
    def get_available_models(self) -> List[str]:
        """Get list of available models across all providers."""
        models = []
        
        # Add some common models for each available provider
        model_map = {
            "openai": [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
            ],
            "anthropic": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-instant-1.2",
            ],
            "google": [
                "gemini-pro",
                "gemini-pro-vision",
                "palm-2",
            ],
            "groq": [
                "mixtral-8x7b-32768",
                "llama2-70b-4096",
                "gemma-7b-it",
            ],
            "mistral": [
                "mistral-large-latest",
                "mistral-medium",
                "mistral-small",
                "mistral-tiny",
            ],
            "ollama": [
                "llama2",
                "mistral",
                "codellama",
                "phi",
                "neural-chat",
            ],
        }
        
        for provider in self.available_providers:
            if provider in model_map:
                models.extend(model_map[provider])
        
        return models
    
    def set_model(self, model: str):
        """Set the current model to use."""
        # Try to determine provider from model name
        provider_prefixes = {
            "gpt": "openai",
            "claude": "anthropic",
            "gemini": "google",
            "palm": "google",
            "mixtral": "groq",
            "llama": "groq",
            "mistral": "mistral",
        }
        
        # Check if model is in format provider/model
        if "/" in model:
            provider, model_name = model.split("/", 1)
            if provider in self.available_providers:
                self.current_provider = provider
                self.current_model = model
                return
        
        # Try to infer provider from model name
        for prefix, provider in provider_prefixes.items():
            if model.lower().startswith(prefix) and provider in self.available_providers:
                self.current_provider = provider
                self.current_model = model
                return
        
        # If can't determine provider, try with current provider
        if self.current_provider:
            self.current_model = model
        else:
            raise ValueError(f"Cannot determine provider for model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send a chat completion request."""
        try:
            # Prepare request
            request_params = {
                "model": self.current_model,
                "messages": messages,
                **kwargs
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                if tool_choice:
                    request_params["tool_choice"] = tool_choice
            
            # Make async request
            response = await acompletion(**request_params)
            
            return response
            
        except Exception as e:
            # Fallback to sync if async fails
            try:
                response = completion(**request_params)
                return response
            except Exception as e2:
                raise Exception(f"LLM request failed: {e2}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.current_provider,
            "model": self.current_model,
            "available_providers": self.get_available_providers(),
        }