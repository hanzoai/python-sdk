"""Memory types and data structures."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Type of memory entry."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    CONVERSATION = "conversation"
    FACT = "fact"
    PROCEDURE = "procedure"
    EPISODE = "episode"
    REFLECTION = "reflection"


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    type: MemoryType
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: Optional[float] = None
    agent_name: Optional[str] = None
    importance: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "agent_name": self.agent_name,
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryEntry:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=MemoryType(data["type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            timestamp=data.get("timestamp", time.time()),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            agent_name=data.get("agent_name"),
            importance=data.get("importance", 1.0)
        )