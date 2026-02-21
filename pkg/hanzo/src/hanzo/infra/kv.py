"""Redis/Valkey key-value store client wrapper for Hanzo infrastructure.

Provides async interface to Redis/Valkey for caching, sessions,
and general key-value storage.
"""

from __future__ import annotations

import os
import json
from typing import Any, Union, Optional
from datetime import timedelta
from dataclasses import dataclass

from pydantic import Field, BaseModel


class KVConfig(BaseModel):
    """Configuration for Redis/Valkey connection."""

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    url: Optional[str] = Field(default=None, description="Full Redis URL (overrides host/port)")
    ssl: bool = Field(default=False, description="Use SSL/TLS")
    socket_timeout: float = Field(default=5.0, description="Socket timeout in seconds")
    socket_connect_timeout: float = Field(default=5.0, description="Connection timeout")
    max_connections: int = Field(default=10, description="Max pool connections")
    decode_responses: bool = Field(default=True, description="Decode responses as strings")

    @classmethod
    def from_env(cls) -> KVConfig:
        """Create config from environment variables.

        Environment variables:
            REDIS_HOST: Server host (default: localhost)
            REDIS_PORT: Server port (default: 6379)
            REDIS_PASSWORD: Authentication password
            REDIS_DB: Database number (default: 0)
            REDIS_URL: Full URL (overrides host/port)
            REDIS_SSL: Use SSL (default: false)
        """
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            url=os.getenv("REDIS_URL"),
            ssl=os.getenv("REDIS_SSL", "").lower() in ("true", "1", "yes"),
        )


@dataclass
class KVResult:
    """Result of a KV operation with metadata."""

    key: str
    value: Any
    ttl: Optional[int] = None  # TTL in seconds, None if no expiry


class KVClient:
    """Async client for Redis/Valkey key-value store.

    Wraps redis-py with async methods and Hanzo conventions.
    Supports both Redis and Valkey (Redis-compatible).

    Example:
        ```python
        client = KVClient(KVConfig.from_env())
        await client.connect()

        # Basic operations
        await client.set("key", "value", ttl=3600)
        value = await client.get("key")

        # JSON operations
        await client.set_json("config", {"theme": "dark"})
        config = await client.get_json("config")

        # Hash operations
        await client.hset("user:1", {"name": "Alice", "email": "alice@example.com"})
        user = await client.hgetall("user:1")
        ```
    """

    def __init__(self, config: Optional[KVConfig] = None) -> None:
        """Initialize KV client.

        Args:
            config: Redis configuration. If None, loads from environment.
        """
        self.config = config or KVConfig.from_env()
        self._client: Any = None

    async def connect(self) -> None:
        """Establish connection to Redis server."""
        try:
            import redis.asyncio as redis
        except ImportError as e:
            raise ImportError("redis is required for KVClient. Install with: pip install redis") from e

        if self.config.url:
            self._client = redis.from_url(
                self.config.url,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                max_connections=self.config.max_connections,
            )
        else:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                ssl=self.config.ssl,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                max_connections=self.config.max_connections,
            )

    async def close(self) -> None:
        """Close the connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if Redis server is healthy.

        Returns:
            True if server is reachable and responding.
        """
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    # Basic string operations

    async def get(self, key: str) -> Optional[str]:
        """Get a string value.

        Args:
            key: Key to retrieve.

        Returns:
            Value or None if not found.
        """
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[Union[int, timedelta]] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set a string value.

        Args:
            key: Key to set.
            value: Value to store.
            ttl: Time to live in seconds or timedelta.
            nx: Only set if key does not exist.
            xx: Only set if key already exists.

        Returns:
            True if successful.
        """
        ex = ttl if isinstance(ttl, int) else None
        px = int(ttl.total_seconds() * 1000) if isinstance(ttl, timedelta) else None

        result = await self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        return result is not None

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys.

        Args:
            keys: Keys to delete.

        Returns:
            Number of keys deleted.
        """
        return await self._client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist.

        Args:
            keys: Keys to check.

        Returns:
            Number of keys that exist.
        """
        return await self._client.exists(*keys)

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration on a key.

        Args:
            key: Key to expire.
            ttl: Time to live in seconds or timedelta.

        Returns:
            True if expiration was set.
        """
        seconds = ttl if isinstance(ttl, int) else int(ttl.total_seconds())
        return await self._client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get time to live for a key.

        Args:
            key: Key to check.

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist.
        """
        return await self._client.ttl(key)

    # JSON operations

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value.

        Args:
            key: Key to retrieve.

        Returns:
            Parsed JSON value or None if not found.
        """
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Set a JSON value.

        Args:
            key: Key to set.
            value: Value to serialize as JSON.
            ttl: Time to live.

        Returns:
            True if successful.
        """
        return await self.set(key, json.dumps(value), ttl=ttl)

    # Hash operations

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a hash field value.

        Args:
            name: Hash name.
            key: Field key.

        Returns:
            Field value or None.
        """
        return await self._client.hget(name, key)

    async def hset(self, name: str, mapping: dict[str, Any]) -> int:
        """Set hash fields.

        Args:
            name: Hash name.
            mapping: Field-value pairs.

        Returns:
            Number of fields added.
        """
        return await self._client.hset(name, mapping=mapping)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields.

        Args:
            name: Hash name.

        Returns:
            Dictionary of field-value pairs.
        """
        return await self._client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields.

        Args:
            name: Hash name.
            keys: Fields to delete.

        Returns:
            Number of fields deleted.
        """
        return await self._client.hdel(name, *keys)

    # List operations

    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the head of a list.

        Args:
            key: List key.
            values: Values to push.

        Returns:
            Length of list after push.
        """
        return await self._client.lpush(key, *values)

    async def rpush(self, key: str, *values: str) -> int:
        """Push values to the tail of a list.

        Args:
            key: List key.
            values: Values to push.

        Returns:
            Length of list after push.
        """
        return await self._client.rpush(key, *values)

    async def lpop(self, key: str, count: Optional[int] = None) -> Optional[Union[str, list[str]]]:
        """Pop values from the head of a list.

        Args:
            key: List key.
            count: Number of values to pop.

        Returns:
            Popped value(s) or None.
        """
        return await self._client.lpop(key, count)

    async def rpop(self, key: str, count: Optional[int] = None) -> Optional[Union[str, list[str]]]:
        """Pop values from the tail of a list.

        Args:
            key: List key.
            count: Number of values to pop.

        Returns:
            Popped value(s) or None.
        """
        return await self._client.rpop(key, count)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """Get a range of list elements.

        Args:
            key: List key.
            start: Start index.
            end: End index (-1 for last).

        Returns:
            List of elements.
        """
        return await self._client.lrange(key, start, end)

    async def llen(self, key: str) -> int:
        """Get list length.

        Args:
            key: List key.

        Returns:
            Length of list.
        """
        return await self._client.llen(key)

    # Set operations

    async def sadd(self, key: str, *members: str) -> int:
        """Add members to a set.

        Args:
            key: Set key.
            members: Members to add.

        Returns:
            Number of members added.
        """
        return await self._client.sadd(key, *members)

    async def srem(self, key: str, *members: str) -> int:
        """Remove members from a set.

        Args:
            key: Set key.
            members: Members to remove.

        Returns:
            Number of members removed.
        """
        return await self._client.srem(key, *members)

    async def smembers(self, key: str) -> set[str]:
        """Get all members of a set.

        Args:
            key: Set key.

        Returns:
            Set of members.
        """
        return await self._client.smembers(key)

    async def sismember(self, key: str, member: str) -> bool:
        """Check if value is a set member.

        Args:
            key: Set key.
            member: Member to check.

        Returns:
            True if member exists.
        """
        return await self._client.sismember(key, member)

    # Atomic operations

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a value.

        Args:
            key: Key to increment.
            amount: Amount to increment by.

        Returns:
            New value.
        """
        return await self._client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a value.

        Args:
            key: Key to decrement.
            amount: Amount to decrement by.

        Returns:
            New value.
        """
        return await self._client.decrby(key, amount)

    # Pub/Sub (basic - for full pub/sub use PubSubClient)

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel.

        Args:
            channel: Channel name.
            message: Message to publish.

        Returns:
            Number of subscribers that received the message.
        """
        return await self._client.publish(channel, message)

    # Keys operations

    async def keys(self, pattern: str = "*") -> list[str]:
        """Find keys matching a pattern.

        Args:
            pattern: Glob-style pattern.

        Returns:
            List of matching keys.
        """
        return await self._client.keys(pattern)

    async def scan(
        self,
        cursor: int = 0,
        match: Optional[str] = None,
        count: int = 100,
    ) -> tuple[int, list[str]]:
        """Incrementally iterate keys.

        Args:
            cursor: Cursor position.
            match: Pattern to match.
            count: Approximate number per iteration.

        Returns:
            Tuple of (next_cursor, keys).
        """
        return await self._client.scan(cursor, match=match, count=count)

    async def flushdb(self) -> bool:
        """Flush the current database.

        Returns:
            True if successful.
        """
        await self._client.flushdb()
        return True

    async def __aenter__(self) -> KVClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
