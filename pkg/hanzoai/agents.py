"""Hanzo AI Agents module.

This module provides access to the hanzo-agents SDK for building
sophisticated AI agent systems with local and distributed execution.
"""

try:
    # Try to import hanzo-agents if installed
    from hanzo_agents import (
        Tool,
        Agent,
        State,
        History,
        Network,
        ToolCall,
        # Core agent types
        BaseAgent,
        GrokAgent,
        LocalAgent,
        # Utilities
        AgentConfig,
        GeminiAgent,
        # Network features
        PeerNetwork,
        RemoteAgent,
        SwarmNetwork,
        ModelRegistry,
        NetworkConfig,
        # CLI agents
        ClaudeCodeAgent,
        InferenceResult,
        OpenAICodexAgent,
        create_memory_kv,
        sequential_router,
        state_based_router,
        create_memory_vector,
    )

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

    # Provide a helpful error message
    def _agents_not_installed(*args, **kwargs):
        raise ImportError("hanzo-agents is not installed. Install it with: pip install hanzo-agents")

    # Create placeholder classes/functions
    Agent = State = Network = Tool = History = _agents_not_installed
    ModelRegistry = InferenceResult = ToolCall = _agents_not_installed
    create_memory_kv = create_memory_vector = _agents_not_installed
    sequential_router = state_based_router = _agents_not_installed
    BaseAgent = LocalAgent = RemoteAgent = _agents_not_installed
    ClaudeCodeAgent = OpenAICodexAgent = _agents_not_installed
    GeminiAgent = GrokAgent = _agents_not_installed
    PeerNetwork = SwarmNetwork = _agents_not_installed
    AgentConfig = NetworkConfig = _agents_not_installed


def create_agent(name: str, model: str = "anthropic/claude-3-5-sonnet-20241022", **kwargs):
    """Create a new AI agent.

    Args:
        name: Name of the agent
        model: Model to use (default: Claude Sonnet)
        **kwargs: Additional configuration options

    Returns:
        Agent instance
    """
    if not AGENTS_AVAILABLE:
        raise ImportError("hanzo-agents is not installed. Install it with: pip install hanzo-agents")

    config = AgentConfig(name=name, model=model, **kwargs)
    return LocalAgent(config)


def create_network(agents: list, router=None, **kwargs):
    """Create an agent network.

    Args:
        agents: List of agents to include in the network
        router: Router to use (default: sequential)
        **kwargs: Additional configuration options

    Returns:
        Network instance
    """
    if not AGENTS_AVAILABLE:
        raise ImportError("hanzo-agents is not installed. Install it with: pip install hanzo-agents")

    if router is None:
        router = sequential_router()

    config = NetworkConfig(agents=agents, router=router, **kwargs)
    return Network(config)


__all__ = [
    # Core classes
    "Agent",
    "State",
    "Network",
    "Tool",
    "History",
    "ModelRegistry",
    "InferenceResult",
    "ToolCall",
    # Memory functions
    "create_memory_kv",
    "create_memory_vector",
    # Routers
    "sequential_router",
    "state_based_router",
    # Agent types
    "BaseAgent",
    "LocalAgent",
    "RemoteAgent",
    "ClaudeCodeAgent",
    "OpenAICodexAgent",
    "GeminiAgent",
    "GrokAgent",
    # Network types
    "PeerNetwork",
    "SwarmNetwork",
    # Configs
    "AgentConfig",
    "NetworkConfig",
    # Convenience functions
    "create_agent",
    "create_network",
    # Status flag
    "AGENTS_AVAILABLE",
]
