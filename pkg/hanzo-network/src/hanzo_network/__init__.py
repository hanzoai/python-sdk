"""Hanzo Network - Agent network orchestration for AI workflows with local and distributed compute.

This package provides a powerful framework for creating and managing networks of AI agents,
inspired by Inngest Agent Kit but adapted for Python and integrated with Hanzo MCP.
Now includes both local AI compute and distributed networking capabilities powered by hanzo.network.
"""

from hanzo_network.core.agent import Agent, create_agent
from hanzo_network.core.network import Network, create_network
from hanzo_network.core.router import Router, create_router, create_routing_agent
from hanzo_network.core.state import NetworkState
from hanzo_network.core.tool import Tool, create_tool
from hanzo_network.distributed_network import DistributedNetwork, DistributedNetworkConfig, create_distributed_network
from hanzo_network.local_network import create_local_agent, create_local_distributed_network, check_local_llm_status

# Local compute capabilities
try:
    from hanzo_network.local_compute import (
        LocalComputeNode,
        LocalComputeOrchestrator,
        InferenceRequest,
        InferenceResult as LocalInferenceResult,
        ModelConfig,
        ModelProvider,
        orchestrator
    )
    LOCAL_COMPUTE_AVAILABLE = True
except ImportError:
    LOCAL_COMPUTE_AVAILABLE = False
    LocalComputeNode = None
    LocalComputeOrchestrator = None
    InferenceRequest = None
    LocalInferenceResult = None
    ModelConfig = None
    ModelProvider = None
    orchestrator = None

__all__ = [
    # Core classes
    "Agent",
    "Network",
    "Router",
    "NetworkState",
    "Tool",
    # Distributed classes
    "DistributedNetwork",
    "DistributedNetworkConfig",
    # Factory functions
    "create_agent",
    "create_network",
    "create_distributed_network",
    "create_router",
    "create_routing_agent",
    "create_tool",
    # Local network helpers
    "create_local_agent",
    "create_local_distributed_network",
    "check_local_llm_status",
    # Local compute (if available)
    "LOCAL_COMPUTE_AVAILABLE",
    "LocalComputeNode",
    "LocalComputeOrchestrator",
    "InferenceRequest",
    "LocalInferenceResult",
    "ModelConfig",
    "ModelProvider",
    "orchestrator",
]

__version__ = "0.2.0"