"""State management for agent networks."""

from typing import TypeVar, Generic, Any, Dict, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
import json
from datetime import datetime


class State:
    """Base class for network state.
    
    State should be:
    - Strongly typed (dataclass or Pydantic)
    - JSON serializable
    - Validated on every write
    
    Example:
        @dataclass
        class ProjectState(State):
            repo: str
            plan: Optional[Plan] = None
            tests_passed: bool = False
            done: bool = False
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        if isinstance(self, BaseModel):
            return self.model_dump()
        elif hasattr(self, "__dataclass_fields__"):
            return {
                k: v for k, v in self.__dict__.items()
                if not k.startswith("_")
            }
        else:
            return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "State":
        """Create state from dictionary."""
        if issubclass(cls, BaseModel):
            return cls.model_validate(data)
        else:
            return cls(**data)
    
    def validate(self) -> None:
        """Validate state integrity."""
        if isinstance(self, BaseModel):
            # Pydantic models self-validate
            pass
        else:
            # Override in subclasses for custom validation
            pass
    
    def checkpoint(self) -> Dict[str, Any]:
        """Create checkpoint data."""
        return {
            "state": self.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
            "type": self.__class__.__name__
        }
    
    @classmethod
    def restore(cls, checkpoint: Dict[str, Any]) -> "State":
        """Restore from checkpoint."""
        return cls.from_dict(checkpoint["state"])


# Type variable for generic state
S = TypeVar("S", bound=State)


@dataclass
class BaseState(State):
    """Common base state with standard fields."""
    done: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateGuard:
    """Guards state mutations for safety."""
    
    def __init__(self, state: State):
        self._state = state
        self._original = state.to_dict()
    
    def __enter__(self):
        return self._state
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Rollback on exception
            for k, v in self._original.items():
                setattr(self._state, k, v)
        else:
            # Validate on success
            self._state.validate()


class StateHistory:
    """Track state changes over time."""
    
    def __init__(self):
        self._history: list[Dict[str, Any]] = []
    
    def record(self, state: State, event: str = "update"):
        """Record state snapshot."""
        self._history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "state": state.to_dict()
        })
    
    def get_history(self) -> list[Dict[str, Any]]:
        """Get full history."""
        return self._history.copy()
    
    def diff(self, index1: int, index2: int) -> Dict[str, Any]:
        """Compare two state snapshots."""
        if index1 >= len(self._history) or index2 >= len(self._history):
            raise IndexError("Invalid history indices")
        
        state1 = self._history[index1]["state"]
        state2 = self._history[index2]["state"]
        
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find changes
        for k, v in state2.items():
            if k not in state1:
                diff["added"][k] = v
            elif state1[k] != v:
                diff["changed"][k] = {"from": state1[k], "to": v}
        
        for k in state1:
            if k not in state2:
                diff["removed"][k] = state1[k]
        
        return diff