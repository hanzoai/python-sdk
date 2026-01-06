"""State store implementations for agent networks."""

from __future__ import annotations

import asyncio
import json
import os
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from ..logger import logger
from .namespace import StateNamespace
from .serializer import StateSerializer, JSONSerializer


T = TypeVar("T")


class StateStore(ABC):
    """Abstract base class for state stores."""
    
    def __init__(self, serializer: StateSerializer | None = None):
        self.serializer = serializer or JSONSerializer()
        self._locks: Dict[str, asyncio.Lock] = {}
        
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a key."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
        
    def _make_key(self, key: str, namespace: str | None = None) -> str:
        """Create a namespaced key."""
        if namespace:
            return f"{namespace}:{key}"
        return key
        
    @abstractmethod
    async def get(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from the store."""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in the store."""
        pass
        
    @abstractmethod
    async def delete(self, key: str, namespace: str | None = None) -> None:
        """Delete a value from the store."""
        pass
        
    @abstractmethod
    async def exists(self, key: str, namespace: str | None = None) -> bool:
        """Check if a key exists."""
        pass
        
    @abstractmethod
    async def keys(self, pattern: str | None = None, namespace: str | None = None) -> List[str]:
        """List keys matching a pattern."""
        pass
        
    async def update(
        self,
        key: str,
        updater: Callable[[Any], Any],
        namespace: str | None = None,
    ) -> Any:
        """Update a value atomically.
        
        Args:
            key: Key to update
            updater: Function that takes current value and returns new value
            namespace: Optional namespace
            
        Returns:
            The updated value
        """
        full_key = self._make_key(key, namespace)
        async with self._get_lock(full_key):
            current = await self.get(key, namespace)
            updated = updater(current)
            await self.set(key, updated, namespace)
            return updated
            
    async def increment(self, key: str, amount: int = 1, namespace: str | None = None) -> int:
        """Increment a numeric value."""
        def inc(val):
            return (val or 0) + amount
        return await self.update(key, inc, namespace)
        
    async def append(self, key: str, item: Any, namespace: str | None = None) -> List[Any]:
        """Append to a list value."""
        def app(val):
            if val is None:
                return [item]
            if not isinstance(val, list):
                raise ValueError(f"Value at key '{key}' is not a list")
            val.append(item)
            return val
        return await self.update(key, app, namespace)
        
    def namespace(self, name: str) -> StateNamespace:
        """Create a namespace view of the store."""
        return StateNamespace(self, name)


class InMemoryStateStore(StateStore):
    """In-memory state store for development and testing."""
    
    def __init__(self, serializer: StateSerializer | None = None):
        super().__init__(serializer)
        self._data: Dict[str, Any] = {}
        
    async def get(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from memory."""
        full_key = self._make_key(key, namespace)
        return self._data.get(full_key)
        
    async def set(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in memory."""
        full_key = self._make_key(key, namespace)
        self._data[full_key] = value
        logger.debug(f"Set state: {full_key} = {type(value).__name__}")
        
    async def delete(self, key: str, namespace: str | None = None) -> None:
        """Delete a value from memory."""
        full_key = self._make_key(key, namespace)
        self._data.pop(full_key, None)
        
    async def exists(self, key: str, namespace: str | None = None) -> bool:
        """Check if a key exists in memory."""
        full_key = self._make_key(key, namespace)
        return full_key in self._data
        
    async def keys(self, pattern: str | None = None, namespace: str | None = None) -> List[str]:
        """List keys in memory."""
        prefix = f"{namespace}:" if namespace else ""
        keys = []
        
        for key in self._data:
            if namespace and not key.startswith(prefix):
                continue
                
            # Remove namespace prefix from result
            clean_key = key[len(prefix):] if namespace else key
            
            if pattern is None or pattern in clean_key:
                keys.append(clean_key)
                
        return keys
        
    def clear(self) -> None:
        """Clear all data (for testing)."""
        self._data.clear()


class RedisStateStore(StateStore):
    """Redis-backed state store for production use."""
    
    def __init__(
        self,
        url: str = "redis://localhost:6379",
        serializer: StateSerializer | None = None,
        **redis_kwargs,
    ):
        super().__init__(serializer)
        self.url = url
        self.redis_kwargs = redis_kwargs
        self._redis = None
        
    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
            except ImportError:
                raise ImportError("Redis support requires 'redis' package. Install with: pip install redis")
                
            self._redis = await redis.from_url(self.url, **self.redis_kwargs)
        return self._redis
        
    async def get(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from Redis."""
        redis = await self._get_redis()
        full_key = self._make_key(key, namespace)
        
        data = await redis.get(full_key)
        if data is None:
            return None
            
        return self.serializer.deserialize(data)
        
    async def set(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in Redis."""
        redis = await self._get_redis()
        full_key = self._make_key(key, namespace)
        
        data = self.serializer.serialize(value)
        await redis.set(full_key, data)
        
    async def delete(self, key: str, namespace: str | None = None) -> None:
        """Delete a value from Redis."""
        redis = await self._get_redis()
        full_key = self._make_key(key, namespace)
        await redis.delete(full_key)
        
    async def exists(self, key: str, namespace: str | None = None) -> bool:
        """Check if a key exists in Redis."""
        redis = await self._get_redis()
        full_key = self._make_key(key, namespace)
        return await redis.exists(full_key) > 0
        
    async def keys(self, pattern: str | None = None, namespace: str | None = None) -> List[str]:
        """List keys in Redis."""
        redis = await self._get_redis()
        
        # Build search pattern
        prefix = f"{namespace}:" if namespace else ""
        search_pattern = f"{prefix}*{pattern}*" if pattern else f"{prefix}*"
        
        # Get matching keys
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = await redis.scan(cursor, match=search_pattern, count=100)
            
            for key in batch:
                key_str = key.decode() if isinstance(key, bytes) else key
                # Remove namespace prefix
                clean_key = key_str[len(prefix):] if namespace else key_str
                keys.append(clean_key)
                
            if cursor == 0:
                break
                
        return keys
        
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


class FileStateStore(StateStore):
    """File-based state store for persistence without external dependencies."""
    
    def __init__(
        self,
        directory: str | Path = ".agent_state",
        serializer: StateSerializer | None = None,
    ):
        super().__init__(serializer)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, key: str, namespace: str | None = None) -> Path:
        """Get file path for a key."""
        full_key = self._make_key(key, namespace)
        # Replace special characters for filesystem compatibility
        safe_key = full_key.replace(":", "_").replace("/", "_")
        return self.directory / f"{safe_key}.state"
        
    async def get(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from file."""
        file_path = self._get_file_path(key, namespace)
        
        if not file_path.exists():
            return None
            
        try:
            data = file_path.read_bytes()
            return self.serializer.deserialize(data)
        except Exception as e:
            logger.error(f"Error reading state file {file_path}: {e}")
            return None
            
    async def set(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in file."""
        file_path = self._get_file_path(key, namespace)
        
        try:
            data = self.serializer.serialize(value)
            file_path.write_bytes(data)
        except Exception as e:
            logger.error(f"Error writing state file {file_path}: {e}")
            raise
            
    async def delete(self, key: str, namespace: str | None = None) -> None:
        """Delete a file."""
        file_path = self._get_file_path(key, namespace)
        
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Error deleting state file {file_path}: {e}")
            
    async def exists(self, key: str, namespace: str | None = None) -> bool:
        """Check if a file exists."""
        file_path = self._get_file_path(key, namespace)
        return file_path.exists()
        
    async def keys(self, pattern: str | None = None, namespace: str | None = None) -> List[str]:
        """List keys from files."""
        keys = []
        prefix = f"{namespace}_" if namespace else ""
        
        for file_path in self.directory.glob("*.state"):
            filename = file_path.stem
            
            # Check namespace
            if namespace and not filename.startswith(prefix):
                continue
                
            # Extract key
            if namespace:
                key = filename[len(prefix):].replace("_", ":")
            else:
                key = filename.replace("_", ":")
                
            # Check pattern
            if pattern is None or pattern in key:
                keys.append(key)
                
        return keys