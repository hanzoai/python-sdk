"""Metastable consensus protocol.

Two-phase finality for multi-agent agreement.

Reference: https://github.com/luxfi/consensus
"""

from .mcp_mesh import MCPMesh, MCPAgent, create_mesh, run_mcp_consensus
from .consensus import State, Result, Consensus, run

__all__ = [
    # Core
    "Consensus",
    "State",
    "Result",
    "run",
    # MCP Mesh
    "MCPMesh",
    "MCPAgent",
    "run_mcp_consensus",
    "create_mesh",
]
__version__ = "0.1.0"
