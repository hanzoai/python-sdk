"""History tracking for agent interactions."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

from hanzo_agents.core.agent import InferenceResult, ToolCall


class HistoryEntry:
    """Single entry in conversation history."""
    
    def __init__(self, 
                 role: str,  # "user", "assistant", "system", "tool"
                 content: Any,
                 agent: Optional[str] = None,
                 tool_call: Optional[ToolCall] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.agent = agent
        self.tool_call = tool_call
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
        if self.agent:
            data["agent"] = self.agent
        if self.tool_call:
            data["tool_call"] = self.tool_call.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary."""
        tool_call = None
        if "tool_call" in data:
            tc = data["tool_call"]
            tool_call = ToolCall(
                tool=tc["tool"],
                arguments=tc["arguments"],
                id=tc.get("id")
            )
        
        return cls(
            role=data["role"],
            content=data["content"],
            agent=data.get("agent"),
            tool_call=tool_call,
            metadata=data.get("metadata", {})
        )


class History(List[HistoryEntry]):
    """Chronological log of agent interactions.
    
    Extends list for easy iteration while adding helper methods.
    """
    
    def add(self, role: str, content: Any, **kwargs):
        """Add entry to history."""
        entry = HistoryEntry(role, content, **kwargs)
        self.append(entry)
        return entry
    
    def add_inference(self, result: InferenceResult):
        """Add inference result to history."""
        # Add main response
        if result.content:
            self.add(
                role="assistant",
                content=result.content,
                agent=result.agent,
                metadata=result.metadata
            )
        
        # Add tool calls
        for tool_call in result.tool_calls:
            self.add(
                role="assistant",
                content=f"Calling tool: {tool_call.tool}",
                agent=result.agent,
                tool_call=tool_call
            )
    
    def add_tool_result(self, tool: str, result: Any, agent: str = None):
        """Add tool execution result."""
        self.add(
            role="tool",
            content=result,
            agent=agent,
            metadata={"tool": tool}
        )
    
    def last_message(self) -> Optional[str]:
        """Get last message content."""
        for entry in reversed(self):
            if entry.role in ["user", "assistant"] and entry.content:
                return str(entry.content)
        return None
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages in chat format."""
        messages = []
        for entry in self:
            if entry.role in ["user", "assistant", "system"]:
                msg = {
                    "role": entry.role,
                    "content": entry.content
                }
                if entry.agent:
                    msg["name"] = entry.agent
                messages.append(msg)
        return messages
    
    def diff_since(self, checkpoint: int) -> List[HistoryEntry]:
        """Get entries since checkpoint index."""
        if checkpoint < 0 or checkpoint >= len(self):
            return []
        return list(self[checkpoint:])
    
    def filter_by_agent(self, agent: str) -> List[HistoryEntry]:
        """Get entries from specific agent."""
        return [e for e in self if e.agent == agent]
    
    def filter_by_role(self, role: str) -> List[HistoryEntry]:
        """Get entries with specific role."""
        return [e for e in self if e.role == role]
    
    def to_json(self, indent: int = 2) -> str:
        """Export to JSON."""
        data = [entry.to_dict() for entry in self]
        return json.dumps(data, indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> "History":
        """Import from JSON."""
        data = json.loads(json_str)
        history = cls()
        for item in data:
            history.append(HistoryEntry.from_dict(item))
        return history
    
    def replay(self, until: Optional[int] = None) -> "History":
        """Create a copy up to a certain point."""
        if until is None:
            until = len(self)
        new_history = History()
        for i, entry in enumerate(self):
            if i >= until:
                break
            new_history.append(entry)
        return new_history
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_entries": len(self),
            "by_role": {
                role: len(self.filter_by_role(role))
                for role in ["user", "assistant", "system", "tool"]
            },
            "agents": list(set(e.agent for e in self if e.agent)),
            "tool_calls": len([e for e in self if e.tool_call]),
            "duration": (
                self[-1].timestamp - self[0].timestamp
                if len(self) >= 2 else None
            )
        }