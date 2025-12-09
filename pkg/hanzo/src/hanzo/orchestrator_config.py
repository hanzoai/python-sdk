#!/usr/bin/env python3
"""
Orchestrator Configuration for Hanzo Dev

Supports multiple orchestration modes:
1. Router-based: Use hanzo-router to access any LLM
2. Direct model: Direct API access to specific models
3. Codex mode: Specialized code-focused orchestration
4. Hybrid: Combine router and direct access
"""

import os
import socket
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import field, dataclass


def check_local_node(host: str = "localhost", port: int = 4000, timeout: float = 0.5) -> bool:
    """Check if hanzo-node is running locally.

    Args:
        host: Host to check (default: localhost)
        port: Port to check (default: 4000)
        timeout: Connection timeout in seconds

    Returns:
        True if node is reachable, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_authenticated() -> bool:
    """Check if user is authenticated with Hanzo cloud."""
    api_key = os.getenv("HANZO_API_KEY")
    return api_key is not None and len(api_key) > 0


def get_auth_status() -> str:
    """Get authentication status message."""
    if is_authenticated():
        return "authenticated (cloud account)"
    return "free tier (no login)"


def get_default_router_endpoint() -> str:
    """Get default router endpoint with smart detection.

    Priority:
    1. HANZO_ROUTER_URL environment variable (explicit override)
    2. Gateway (gateway.hanzo.ai) - free tier by default

    Upgrade paths:
    - Login: `hanzo login` - Use cloud account with full features
    - Local: `hanzo node start` - Private AI on your machine

    Returns:
        Router endpoint URL
    """
    # Check environment variable first (explicit override)
    env_url = os.getenv("HANZO_ROUTER_URL")
    if env_url:
        return env_url

    # Default to free gateway - best UX for new users
    # Users can login or run local node for more features
    return "https://gateway.hanzo.ai"


class OrchestratorMode(Enum):
    """Orchestration modes."""

    ROUTER = "router"  # Via hanzo-router (unified gateway)
    DIRECT = "direct"  # Direct model API access
    CODEX = "codex"  # Codex-specific mode
    HYBRID = "hybrid"  # Router + direct combination
    LOCAL = "local"  # Local models only


class ModelProvider(Enum):
    """Model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    LOCAL = "local"
    ROUTER = "router"  # Via hanzo-router
    CODEX = "codex"  # OpenAI Codex


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    name: str  # Model name (e.g., "gpt-5", "gpt-4o")
    provider: ModelProvider  # Provider type
    endpoint: Optional[str] = None  # Custom endpoint
    api_key: Optional[str] = None  # API key (if not using env)
    context_window: int = 8192  # Context window size
    max_output: int = 4096  # Max output tokens
    temperature: float = 0.7  # Temperature setting
    capabilities: List[str] = field(default_factory=list)  # Model capabilities
    cost_per_1k_input: float = 0.01  # Cost per 1K input tokens
    cost_per_1k_output: float = 0.03  # Cost per 1K output tokens
    supports_tools: bool = True  # Supports function calling
    supports_vision: bool = False  # Supports image input
    supports_streaming: bool = True  # Supports streaming responses


@dataclass
class RouterConfig:
    """Configuration for hanzo-router.

    Automatically detects and prioritizes:
    1. HANZO_ROUTER_URL env var
    2. Local hanzo-node (localhost:4000)
    3. Gateway (gateway.hanzo.ai)
    """

    endpoint: Optional[str] = None  # Router endpoint (auto-detected if None)
    api_key: Optional[str] = None  # Router API key
    model_preferences: List[str] = field(default_factory=list)  # Preferred models
    fallback_models: List[str] = field(default_factory=list)  # Fallback models
    load_balancing: bool = True  # Enable load balancing
    cache_enabled: bool = True  # Enable response caching
    retry_on_failure: bool = True  # Retry failed requests
    max_retries: int = 3  # Max retry attempts

    def __post_init__(self):
        """Auto-detect endpoint if not provided."""
        if self.endpoint is None:
            self.endpoint = get_default_router_endpoint()


@dataclass
class CodexConfig:
    """Configuration for Codex mode."""

    model: str = "code-davinci-002"  # Codex model
    mode: str = "code-review"  # Mode: code-review, generation, completion
    languages: List[str] = field(default_factory=lambda: ["python", "typescript", "go"])
    max_tokens: int = 8000  # Max tokens for Codex
    stop_sequences: List[str] = field(default_factory=list)  # Stop sequences
    enable_comments: bool = True  # Generate with comments
    enable_docstrings: bool = True  # Generate docstrings
    enable_type_hints: bool = True  # Generate type hints


@dataclass
class OrchestratorConfig:
    """Complete orchestrator configuration."""

    mode: OrchestratorMode = OrchestratorMode.ROUTER
    primary_model: str = "gpt-5"  # Primary orchestrator model
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    router: Optional[RouterConfig] = None
    codex: Optional[CodexConfig] = None
    worker_models: List[str] = field(default_factory=list)  # Worker agent models
    critic_models: List[str] = field(default_factory=list)  # Critic agent models
    local_models: List[str] = field(default_factory=list)  # Local models
    enable_cost_optimization: bool = True  # Enable cost optimization
    cost_threshold: float = 0.10  # Cost threshold per request
    prefer_local: bool = True  # Prefer local models when possible
    enable_caching: bool = True  # Cache responses
    enable_monitoring: bool = True  # Monitor performance
    debug: bool = False  # Debug mode


# Predefined configurations
CONFIGS = {
    "gpt-5-pro-codex": OrchestratorConfig(
        mode=OrchestratorMode.HYBRID,
        primary_model="gpt-5-pro",
        models={
            "gpt-5-pro": ModelConfig(
                name="gpt-5-pro",
                provider=ModelProvider.OPENAI,
                context_window=200000,
                capabilities=["reasoning", "code", "analysis", "vision"],
                cost_per_1k_input=0.20,
                cost_per_1k_output=0.60,
                supports_vision=True,
            ),
            "codex": ModelConfig(
                name="code-davinci-002",
                provider=ModelProvider.CODEX,
                context_window=8000,
                capabilities=["code_generation", "completion", "review"],
                cost_per_1k_input=0.02,
                cost_per_1k_output=0.02,
            ),
        },
        codex=CodexConfig(
            model="code-davinci-002",
            mode="code-review",
            enable_comments=True,
            enable_docstrings=True,
            enable_type_hints=True,
        ),
        worker_models=["codex", "gpt-4o"],
        critic_models=["gpt-5-pro"],
        enable_cost_optimization=True,
    ),
    "router-based": OrchestratorConfig(
        mode=OrchestratorMode.ROUTER,
        primary_model="router:gpt-4o-mini",  # Free on gateway
        router=RouterConfig(
            # Auto-detect: local node → gateway (free models)
            model_preferences=["gpt-4o-mini", "gpt-3.5-turbo", "llama-3.1-8b"],
            fallback_models=["gpt-4o", "claude-3-5-sonnet"],
            load_balancing=True,
            cache_enabled=True,
        ),
        worker_models=["router:gpt-4o-mini", "router:llama-3.1-8b"],
        critic_models=["router:gpt-4o-mini"],
        enable_cost_optimization=True,
    ),
    "direct-gpt5": OrchestratorConfig(
        mode=OrchestratorMode.DIRECT,
        primary_model="gpt-5",
        models={
            "gpt-5": ModelConfig(
                name="gpt-5-latest",
                provider=ModelProvider.OPENAI,
                endpoint="https://api.openai.com/v1",
                context_window=128000,
                capabilities=["reasoning", "code", "analysis"],
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.45,
            ),
        },
        worker_models=["gpt-4o"],
        critic_models=["gpt-5"],
        enable_cost_optimization=False,  # Use GPT-5 for everything
    ),
    "codex-focused": OrchestratorConfig(
        mode=OrchestratorMode.CODEX,
        primary_model="codex",
        codex=CodexConfig(
            model="code-davinci-002",
            mode="code-generation",
            languages=["python", "typescript", "rust", "go"],
            max_tokens=8000,
            enable_comments=True,
        ),
        worker_models=["codex"],
        critic_models=["gpt-4o"],  # Use GPT-4o for code review
        enable_cost_optimization=True,
    ),
    "cost-optimized": OrchestratorConfig(
        mode=OrchestratorMode.HYBRID,
        primary_model="local:llama3.2",
        models={
            "local:llama3.2": ModelConfig(
                name="llama-3.2-3b",
                provider=ModelProvider.LOCAL,
                context_window=8192,
                capabilities=["basic_reasoning", "simple_tasks"],
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
            ),
        },
        router=RouterConfig(
            # Auto-detect: local node → gateway (free models)
            model_preferences=["gpt-4o-mini", "llama-3.1-8b"],
            fallback_models=["gpt-3.5-turbo"],
        ),
        worker_models=["local:llama3.2", "local:qwen2.5"],
        critic_models=["router:gpt-4o-mini"],  # Use free model for review
        local_models=["llama3.2", "qwen2.5", "mistral"],
        enable_cost_optimization=True,
        prefer_local=True,
    ),
}


def get_orchestrator_config(name: str) -> OrchestratorConfig:
    """Get a predefined orchestrator configuration.

    Args:
        name: Configuration name or model spec

    Returns:
        OrchestratorConfig instance
    """
    # Check predefined configs
    if name in CONFIGS:
        return CONFIGS[name]

    # Parse model spec (e.g., "router:gpt-5", "direct:gpt-4o", "codex")
    if ":" in name:
        mode, model = name.split(":", 1)
        if mode == "router":
            return OrchestratorConfig(
                mode=OrchestratorMode.ROUTER,
                primary_model=f"router:{model}",
                router=RouterConfig(
                    model_preferences=[model],
                ),
            )
        elif mode == "direct":
            return OrchestratorConfig(
                mode=OrchestratorMode.DIRECT,
                primary_model=model,
            )
        elif mode == "local":
            return OrchestratorConfig(
                mode=OrchestratorMode.LOCAL,
                primary_model=f"local:{model}",
                local_models=[model],
                enable_cost_optimization=True,
                prefer_local=True,
            )

    # Default to router mode with specified model
    return OrchestratorConfig(
        mode=OrchestratorMode.ROUTER,
        primary_model=name,
        router=RouterConfig(
            model_preferences=[name],
        ),
    )


def list_available_configs() -> List[str]:
    """List available orchestrator configurations."""
    return list(CONFIGS.keys()) + [
        "router:<model>",
        "direct:<model>",
        "local:<model>",
        "codex",
    ]


# Export configuration builder
def build_custom_config(
    mode: str = "router",
    primary_model: str = "gpt-5",
    use_router: bool = True,
    use_codex: bool = False,
    worker_models: Optional[List[str]] = None,
    critic_models: Optional[List[str]] = None,
    enable_cost_optimization: bool = True,
    router_endpoint: Optional[str] = None,
) -> OrchestratorConfig:
    """Build a custom orchestrator configuration.

    Args:
        mode: Orchestration mode (router, direct, codex, hybrid, local)
        primary_model: Primary orchestrator model
        use_router: Use hanzo-router for model access
        use_codex: Enable Codex for code tasks
        worker_models: Worker agent models
        critic_models: Critic agent models
        enable_cost_optimization: Enable cost optimization
        router_endpoint: Custom router endpoint (None for auto-detect)

    Returns:
        Custom OrchestratorConfig
    """
    config = OrchestratorConfig(
        mode=OrchestratorMode(mode),
        primary_model=primary_model,
        worker_models=worker_models or ["gpt-4o", "claude-3-5"],
        critic_models=critic_models or ["gpt-5"],
        enable_cost_optimization=enable_cost_optimization,
    )

    if use_router:
        config.router = RouterConfig(
            endpoint=router_endpoint,  # None triggers auto-detection in __post_init__
            model_preferences=[primary_model],
        )

    if use_codex:
        config.codex = CodexConfig(
            model="code-davinci-002",
            mode="code-review",
        )

    return config
