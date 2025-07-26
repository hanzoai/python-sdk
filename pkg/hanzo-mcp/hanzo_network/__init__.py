"""Hanzo Network - Agent network orchestration for AI workflows with local compute.

This package provides a powerful framework for creating and managing networks of AI agents,
inspired by Inngest Agent Kit but adapted for Python and integrated with Hanzo MCP.
Now includes local AI compute capabilities powered by hanzo.network.
"""

from hanzo_network.core.agent import Agent, create_agent
from hanzo_network.core.network import Network, create_network
from hanzo_network.core.router import Router, create_router, create_routing_agent
from hanzo_network.core.state import NetworkState
from hanzo_network.core.tool import Tool, create_tool

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
    # Factory functions
    "create_agent",
    "create_network",
    "create_router",
    "create_routing_agent",
    "create_tool",
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