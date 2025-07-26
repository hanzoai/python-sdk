"""Hanzo Agents SDK - Production-grade AI agent runtime with Web3 and TEE support."""

from hanzo_agents.core.agent import Agent, InferenceResult, ToolCall
from hanzo_agents.core.tool import Tool, ToolRegistry
from hanzo_agents.core.state import State
from hanzo_agents.core.router import RouterFn, Router
from hanzo_agents.core.network import Network
from hanzo_agents.core.history import History
from hanzo_agents.core.memory import MemoryKV, MemoryVector
from hanzo_agents.core.model import BaseModelAdapter, ModelRegistry

# Web3 integration
try:
    from hanzo_agents.core.wallet import (
        WalletConfig, AgentWallet, Transaction,
        generate_shared_mnemonic, derive_agent_wallet,
        create_wallet_tool
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
    TEEProvider, TEEConfig, AttestationReport,
    ConfidentialAgent, ComputeMarketplace,
    ComputeOffer, ComputeRequest,
    create_attestation_verifier_tool
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