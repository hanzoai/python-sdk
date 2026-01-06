"""Namespace support for state stores."""

from __future__ import annotations

from typing import Any, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .store import StateStore


class StateNamespace:
    """A namespaced view of a state store.
    
    This allows you to work with a subset of the state store
    without worrying about key collisions.
    """
    
    def __init__(self, store: StateStore, namespace: str):
        self.store = store
        self.namespace = namespace
        
    async def get(self, key: str) -> Any:
        """Get a value from this namespace."""
        return await self.store.get(key, self.namespace)
        
    async def set(self, key: str, value: Any) -> None:
        """Set a value in this namespace."""
        await self.store.set(key, value, self.namespace)
        
    async def delete(self, key: str) -> None:
        """Delete a value from this namespace."""
        await self.store.delete(key, self.namespace)
        
    async def exists(self, key: str) -> bool:
        """Check if a key exists in this namespace."""
        return await self.store.exists(key, self.namespace)
        
    async def keys(self, pattern: str | None = None) -> List[str]:
        """List keys in this namespace."""
        return await self.store.keys(pattern, self.namespace)
        
    async def update(self, key: str, updater: Callable[[Any], Any]) -> Any:
        """Update a value atomically in this namespace."""
        return await self.store.update(key, updater, self.namespace)
        
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in this namespace."""
        return await self.store.increment(key, amount, self.namespace)
        
    async def append(self, key: str, item: Any) -> List[Any]:
        """Append to a list value in this namespace."""
        return await self.store.append(key, item, self.namespace)
        
    def sub_namespace(self, name: str) -> StateNamespace:
        """Create a sub-namespace."""
        return StateNamespace(self.store, f"{self.namespace}:{name}")
        
    async def clear(self) -> None:
        """Clear all keys in this namespace."""
        keys = await self.keys()
        for key in keys:
            await self.delete(key)