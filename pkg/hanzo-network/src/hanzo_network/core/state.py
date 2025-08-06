"""Network state management for agent networks."""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime


T = TypeVar('T')


@dataclass
class Message:
    """A message in the network conversation."""
    role: str  # 'user', 'assistant', 'system', 'agent'
    content: str
    agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class NetworkState(Generic[T]):
    """Shared state between agents in a network.
    
    This class manages:
    - Message history across all agents
    - Key-value store for sharing data
    - Agent execution tracking
    """
    
    def __init__(self, initial_data: Optional[T] = None):
        """Initialize network state.
        
        Args:
            initial_data: Initial data for the state
        """
        self.messages: List[Message] = []
        self.data: T = initial_data if initial_data is not None else {}
        self.agent_results: Dict[str, Any] = {}
        self.execution_count: int = 0
        self.metadata: Dict[str, Any] = {}
    
    def add_message(
        self,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: Message role (user, assistant, system, agent)
            content: Message content
            agent_id: ID of the agent that generated this message
            **metadata: Additional metadata for the message
        """
        self.messages.append(Message(
            role=role,
            content=content,
            agent_id=agent_id,
            metadata=metadata
        ))
    
    def get_messages(
        self,
        agent_id: Optional[str] = None,
        role: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages from the history.
        
        Args:
            agent_id: Filter by agent ID
            role: Filter by role
            limit: Limit number of messages returned
            
        Returns:
            List of messages matching the filters
        """
        messages = self.messages
        
        if agent_id is not None:
            messages = [m for m in messages if m.agent_id == agent_id]
        
        if role is not None:
            messages = [m for m in messages if m.role == role]
        
        if limit is not None:
            messages = messages[-limit:]
        
        return messages
    
    def set_agent_result(self, agent_id: str, result: Any) -> None:
        """Store the result from an agent execution.
        
        Args:
            agent_id: ID of the agent
            result: Result from the agent
        """
        self.agent_results[agent_id] = result
    
    def get_agent_result(self, agent_id: str) -> Optional[Any]:
        """Get the result from a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent result if available
        """
        return self.agent_results.get(agent_id)
    
    def increment_execution_count(self) -> int:
        """Increment and return the execution count."""
        self.execution_count += 1
        return self.execution_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "agent_id": m.agent_id,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in self.messages
            ],
            "data": self.data,
            "agent_results": self.agent_results,
            "execution_count": self.execution_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkState":
        """Create state from dictionary."""
        state = cls(initial_data=data.get("data", {}))
        
        # Restore messages
        for msg_data in data.get("messages", []):
            state.messages.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                agent_id=msg_data.get("agent_id"),
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {})
            ))
        
        state.agent_results = data.get("agent_results", {})
        state.execution_count = data.get("execution_count", 0)
        state.metadata = data.get("metadata", {})
        
        return state