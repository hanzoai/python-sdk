"""Hanzo Agents SDK - Production-grade AI agent runtime with Web3 and TEE support."""

from hanzo_agents.core.tool import Tool, ToolRegistry
from hanzo_agents.core.agent import Agent, ToolCall, InferenceResult
from hanzo_agents.core.model import ModelRegistry, BaseModelAdapter
from hanzo_agents.core.state import State
from hanzo_agents.core.memory import (
    MemoryKV,
    MemoryVector,
    create_memory_kv,
    create_memory_vector,
)
from hanzo_agents.core.router import (
    Router,
    RouterFn,
    LLMRouter,
    HybridRouter,
    DeterministicRouter,
    sequential_router,
    conditional_router,
    state_based_router,
)
from hanzo_agents.core.history import History
from hanzo_agents.core.network import Network

# Web3 integration
try:
    from hanzo_agents.core.wallet import (
        AgentWallet,
        Transaction,
        WalletConfig,
        create_wallet_tool,
        derive_agent_wallet,
        generate_shared_mnemonic,
    )

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    WalletConfig = None
    AgentWallet = None
    Transaction = None
    generate_shared_mnemonic = None
    derive_agent_wallet = None
    create_wallet_tool = None

# TEE support
from hanzo_agents.core.tee import (
    TEEConfig,
    TEEProvider,
    ComputeOffer,
    ComputeRequest,
    AttestationReport,
    ConfidentialAgent,
    ComputeMarketplace,
    create_attestation_verifier_tool,
)

__version__ = "0.2.0"

__all__ = [
    # Core classes
    "Agent",
    "Tool",
    "State",
    "Network",
    "Router",
    "History",
    "MemoryKV",
    "MemoryVector",
    "BaseModelAdapter",
    # Results
    "InferenceResult",
    # Types
    "RouterFn",
    "ToolCall",
    # Routers
    "DeterministicRouter",
    "LLMRouter",
    "HybridRouter",
    "sequential_router",
    "conditional_router",
    "state_based_router",
    # Memory functions
    "create_memory_kv",
    "create_memory_vector",
    # Registries
    "ToolRegistry",
    "ModelRegistry",
    # Web3 (if available)
    "WalletConfig",
    "AgentWallet",
    "Transaction",
    "generate_shared_mnemonic",
    "derive_agent_wallet",
    "create_wallet_tool",
    "WEB3_AVAILABLE",
    # TEE
    "TEEProvider",
    "TEEConfig",
    "AttestationReport",
    "ConfidentialAgent",
    "ComputeMarketplace",
    "ComputeOffer",
    "ComputeRequest",
    "create_attestation_verifier_tool",
]
