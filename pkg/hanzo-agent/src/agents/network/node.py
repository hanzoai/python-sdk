"""Network node representation for agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..agent import Agent
from ..run_context import TContext


class NodeStatus(Enum):
    """Status of a node in the network."""
    
    PENDING = "pending"
    """Node has not been executed yet."""
    
    RUNNING = "running"
    """Node is currently executing."""
    
    COMPLETED = "completed"
    """Node has completed successfully."""
    
    FAILED = "failed"
    """Node execution failed."""
    
    SKIPPED = "skipped"
    """Node was skipped (e.g., due to dependencies)."""


@dataclass
class NetworkNode:
    """A node in the agent network."""
    
    agent: Agent[TContext]
    """The agent associated with this node."""
    
    capabilities: List[str] = field(default_factory=list)
    """List of capabilities this agent provides."""
    
    dependencies: List[str] = field(default_factory=list)
    """List of agent names this node depends on."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata for routing and orchestration."""
    
    status: NodeStatus = NodeStatus.PENDING
    """Current status of the node."""
    
    error: Exception | None = None
    """Error if the node failed."""
    
    execution_count: int = 0
    """Number of times this node has been executed."""
    
    last_execution_time: float | None = None
    """Timestamp of last execution."""
    
    average_execution_time: float | None = None
    """Average execution time in seconds."""
    
    def can_execute(self, completed_nodes: List[str]) -> bool:
        """Check if this node can execute based on dependencies."""
        return all(dep in completed_nodes for dep in self.dependencies)
        
    def get_info(self) -> Dict[str, Any]:
        """Get information about this node."""
        return {
            "name": self.agent.name,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "average_execution_time": self.average_execution_time,
            "metadata": self.metadata,
        }