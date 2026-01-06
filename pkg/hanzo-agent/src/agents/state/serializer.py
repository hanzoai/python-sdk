"""Serializers for state storage."""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from typing import Any


class StateSerializer(ABC):
    """Abstract base class for state serializers."""
    
    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """Serialize an object to bytes."""
        pass
        
    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to an object."""
        pass


class JSONSerializer(StateSerializer):
    """JSON serializer for state storage.
    
    This is the default serializer. It's human-readable but
    limited to JSON-serializable types.
    """
    
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding
        
    def serialize(self, obj: Any) -> bytes:
        """Serialize to JSON bytes."""
        return json.dumps(obj).encode(self.encoding)
        
    def deserialize(self, data: bytes) -> Any:
        """Deserialize from JSON bytes."""
        return json.loads(data.decode(self.encoding))


class PickleSerializer(StateSerializer):
    """Pickle serializer for state storage.
    
    This can handle any Python object but is not human-readable
    and has security implications (don't unpickle untrusted data).
    """
    
    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        self.protocol = protocol
        
    def serialize(self, obj: Any) -> bytes:
        """Serialize to pickle bytes."""
        return pickle.dumps(obj, protocol=self.protocol)
        
    def deserialize(self, data: bytes) -> Any:
        """Deserialize from pickle bytes."""
        return pickle.loads(data)