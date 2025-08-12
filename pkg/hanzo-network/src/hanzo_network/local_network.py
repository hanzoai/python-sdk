"""Helper functions for creating local networks with local LLMs."""

from typing import List, Optional
from .core.agent import Agent, ModelConfig, ModelProvider, create_agent
from .core.tool import Tool
from .distributed_network import create_distributed_network, DistributedNetwork


def create_local_agent(
    name: str,
    description: str,
    system: Optional[str] = None,
    tools: Optional[List[Tool]] = None,
    local_model: str = "llama3.2",
    base_url: str = "http://localhost:11434",
    **metadata,
) -> Agent:
    """Create an agent configured to use a local LLM.

    Args:
        name: Agent name
        description: Agent description
        system: System prompt
        tools: List of tools
        local_model: Local model name (e.g., "llama3.2" for Ollama, "mlx-community/Llama-3.2-3B-Instruct-4bit" for MLX)
        base_url: Base URL for local LLM server (Ollama default)
        **metadata: Additional metadata

    Returns:
        Agent configured for local LLM
    """
    # Create model config for local provider
    model_config = ModelConfig(
        provider=ModelProvider.LOCAL, model=local_model, base_url=base_url
    )

    return create_agent(
        name=name,
        description=description,
        model=model_config,
        system=system,
        tools=tools,
        **metadata,
    )


def create_local_distributed_network(
    agents: List[Agent],
    name: Optional[str] = None,
    node_id: Optional[str] = None,
    listen_port: int = 5678,
    broadcast_port: int = 5678,
    local_model: str = "llama3.2",
    base_url: str = "http://localhost:11434",
    **kwargs,
) -> DistributedNetwork:
    """Create a distributed network configured for local execution.

    This is a convenience wrapper that creates a distributed network
    with sensible defaults for local testing with local LLMs.

    Args:
        agents: List of agents
        name: Network name
        node_id: Node identifier
        listen_port: Port to listen on
        broadcast_port: UDP broadcast port
        local_model: Local model for router
        base_url: Base URL for local LLM
        **kwargs: Additional arguments for create_distributed_network

    Returns:
        Configured DistributedNetwork
    """
    from .core.router import create_routing_agent

    # Create a local router if one isn't provided
    if "router" not in kwargs:
        router_config = ModelConfig(
            provider=ModelProvider.LOCAL, model=local_model, base_url=base_url
        )

        kwargs["router"] = create_routing_agent(
            name="local_router", description="Local routing agent", model=router_config
        )

    return create_distributed_network(
        agents=agents,
        name=name or "local-network",
        node_id=node_id,
        listen_port=listen_port,
        broadcast_port=broadcast_port,
        **kwargs,
    )


async def check_local_llm_status(provider: str = "hanzo") -> dict:
    """Check the status of local LLM providers.

    Args:
        provider: Provider to check ("hanzo", "mlx", "tinygrad", "dummy")

    Returns:
        Status information including availability and models
    """
    from .llm import HanzoNetProvider

    # Map old provider names to hanzo/net engines
    engine_map = {
        "ollama": "dummy",  # Ollama replaced with hanzo/net
        "mlx": "mlx",
        "tinygrad": "tinygrad",
        "dummy": "dummy",
        "hanzo": "dummy",  # Default hanzo/net
    }

    engine_type = engine_map.get(provider, "dummy")

    hanzo_provider = HanzoNetProvider(engine_type)
    is_available = await hanzo_provider.is_available()
    models = await hanzo_provider.list_models() if is_available else []

    # Provide helpful status info
    status = {
        "provider": f"hanzo/net ({engine_type})",
        "available": is_available,
        "engine": engine_type,
        "models": models,
    }

    # Add engine-specific info
    if engine_type == "mlx":
        import platform

        status["platform"] = (
            "Apple Silicon"
            if platform.machine() in ["arm64", "aarch64"]
            else platform.machine()
        )
        if not is_available:
            status["instructions"] = "MLX requires Apple Silicon (M1/M2/M3)"
    elif engine_type == "tinygrad":
        status["instructions"] = (
            "Tinygrad engine ready for distributed inference"
            if is_available
            else "Install tinygrad"
        )
    else:  # dummy
        status["instructions"] = "Using mock responses for testing"

    return status
