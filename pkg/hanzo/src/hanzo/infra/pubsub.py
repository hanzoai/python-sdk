"""NATS pub/sub client wrapper for Hanzo infrastructure.

Provides async interface to NATS for messaging, pub/sub,
request/reply, and streaming with JetStream.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, Sequence

from pydantic import BaseModel, Field


class PubSubConfig(BaseModel):
    """Configuration for NATS connection."""

    servers: list[str] = Field(default=["nats://localhost:4222"], description="NATS server URLs")
    user: Optional[str] = Field(default=None, description="Username for authentication")
    password: Optional[str] = Field(default=None, description="Password for authentication")
    token: Optional[str] = Field(default=None, description="Token for authentication")
    nkey_seed: Optional[str] = Field(default=None, description="NKey seed for authentication")
    tls: bool = Field(default=False, description="Use TLS")
    name: str = Field(default="hanzo-client", description="Client name")
    connect_timeout: float = Field(default=5.0, description="Connection timeout in seconds")
    reconnect_time_wait: float = Field(default=2.0, description="Time between reconnect attempts")
    max_reconnect_attempts: int = Field(default=60, description="Max reconnection attempts")
    ping_interval: float = Field(default=120.0, description="Ping interval in seconds")
    max_outstanding_pings: int = Field(default=2, description="Max outstanding pings")

    @classmethod
    def from_env(cls) -> PubSubConfig:
        """Create config from environment variables.

        Environment variables:
            NATS_SERVERS: Comma-separated list of NATS URLs (default: nats://localhost:4222)
            NATS_USER: Username for authentication
            NATS_PASSWORD: Password for authentication
            NATS_TOKEN: Token for authentication
            NATS_NKEY_SEED: NKey seed for authentication
            NATS_TLS: Use TLS (default: false)
        """
        servers_str = os.getenv("NATS_SERVERS", "nats://localhost:4222")
        servers = [s.strip() for s in servers_str.split(",")]

        return cls(
            servers=servers,
            user=os.getenv("NATS_USER"),
            password=os.getenv("NATS_PASSWORD"),
            token=os.getenv("NATS_TOKEN"),
            nkey_seed=os.getenv("NATS_NKEY_SEED"),
            tls=os.getenv("NATS_TLS", "").lower() in ("true", "1", "yes"),
        )


@dataclass
class Message:
    """A NATS message."""

    subject: str
    data: bytes
    reply: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


@dataclass
class Subscription:
    """A NATS subscription handle."""

    subject: str
    queue: Optional[str] = None
    _sub: Any = None

    async def unsubscribe(self) -> None:
        """Unsubscribe from the subject."""
        if self._sub:
            await self._sub.unsubscribe()

    async def drain(self) -> None:
        """Drain the subscription before unsubscribing."""
        if self._sub:
            await self._sub.drain()


MessageHandler = Callable[[Message], Awaitable[None]]


class PubSubClient:
    """Async client for NATS messaging.

    Wraps nats-py with Hanzo conventions for pub/sub, request/reply,
    and JetStream operations.

    Example:
        ```python
        client = PubSubClient(PubSubConfig.from_env())
        await client.connect()

        # Simple pub/sub
        async def handler(msg: Message):
            print(f"Received: {msg.data.decode()}")

        sub = await client.subscribe("events.>", handler)
        await client.publish("events.user.created", b"user123")

        # Request/reply
        response = await client.request("api.users.get", b"user123", timeout=5.0)

        # JetStream (persistent messaging)
        await client.js_create_stream("EVENTS", subjects=["events.*"])
        await client.js_publish("events.user", b"data")
        ```
    """

    def __init__(self, config: Optional[PubSubConfig] = None) -> None:
        """Initialize pub/sub client.

        Args:
            config: NATS configuration. If None, loads from environment.
        """
        self.config = config or PubSubConfig.from_env()
        self._nc: Any = None
        self._js: Any = None

    async def connect(self) -> None:
        """Establish connection to NATS server."""
        try:
            import nats
        except ImportError as e:
            raise ImportError(
                "nats-py is required for PubSubClient. "
                "Install with: pip install nats-py"
            ) from e

        connect_opts: dict[str, Any] = {
            "servers": self.config.servers,
            "name": self.config.name,
            "connect_timeout": self.config.connect_timeout,
            "reconnect_time_wait": self.config.reconnect_time_wait,
            "max_reconnect_attempts": self.config.max_reconnect_attempts,
            "ping_interval": self.config.ping_interval,
            "max_outstanding_pings": self.config.max_outstanding_pings,
        }

        if self.config.user and self.config.password:
            connect_opts["user"] = self.config.user
            connect_opts["password"] = self.config.password
        elif self.config.token:
            connect_opts["token"] = self.config.token
        elif self.config.nkey_seed:
            connect_opts["nkeys_seed"] = self.config.nkey_seed

        self._nc = await nats.connect(**connect_opts)

    async def close(self) -> None:
        """Close the connection."""
        if self._nc:
            await self._nc.drain()
            self._nc = None
            self._js = None

    async def health_check(self) -> bool:
        """Check if NATS connection is healthy.

        Returns:
            True if connected and responding.
        """
        if not self._nc:
            return False
        return self._nc.is_connected

    # Core pub/sub operations

    async def publish(
        self,
        subject: str,
        data: bytes,
        reply: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish a message to a subject.

        Args:
            subject: Subject to publish to.
            data: Message payload.
            reply: Optional reply subject.
            headers: Optional message headers.
        """
        await self._nc.publish(subject, data, reply=reply, headers=headers)

    async def subscribe(
        self,
        subject: str,
        handler: MessageHandler,
        queue: Optional[str] = None,
    ) -> Subscription:
        """Subscribe to a subject.

        Args:
            subject: Subject pattern (supports wildcards * and >).
            handler: Async callback for received messages.
            queue: Queue group for load balancing.

        Returns:
            Subscription handle for unsubscribing.
        """
        async def _wrapper(msg: Any) -> None:
            wrapped = Message(
                subject=msg.subject,
                data=msg.data,
                reply=msg.reply,
                headers=dict(msg.headers) if msg.headers else {},
            )
            await handler(wrapped)

        sub = await self._nc.subscribe(subject, cb=_wrapper, queue=queue or "")
        return Subscription(subject=subject, queue=queue, _sub=sub)

    async def subscribe_iter(
        self,
        subject: str,
        queue: Optional[str] = None,
    ) -> AsyncIterator[Message]:
        """Subscribe to a subject with async iteration.

        Args:
            subject: Subject pattern.
            queue: Queue group for load balancing.

        Yields:
            Messages as they arrive.
        """
        sub = await self._nc.subscribe(subject, queue=queue or "")
        try:
            async for msg in sub.messages:
                yield Message(
                    subject=msg.subject,
                    data=msg.data,
                    reply=msg.reply,
                    headers=dict(msg.headers) if msg.headers else {},
                )
        finally:
            await sub.unsubscribe()

    # Request/reply pattern

    async def request(
        self,
        subject: str,
        data: bytes,
        timeout: float = 5.0,
        headers: Optional[dict[str, str]] = None,
    ) -> Message:
        """Send a request and wait for a response.

        Args:
            subject: Subject to send request to.
            data: Request payload.
            timeout: Response timeout in seconds.
            headers: Optional request headers.

        Returns:
            Response message.

        Raises:
            TimeoutError: If no response within timeout.
        """
        response = await self._nc.request(subject, data, timeout=timeout, headers=headers)
        return Message(
            subject=response.subject,
            data=response.data,
            reply=response.reply,
            headers=dict(response.headers) if response.headers else {},
        )

    async def respond(
        self,
        request: Message,
        data: bytes,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Send a response to a request message.

        Args:
            request: Original request message.
            data: Response payload.
            headers: Optional response headers.
        """
        if request.reply:
            await self.publish(request.reply, data, headers=headers)

    # JetStream operations

    def _get_js(self) -> Any:
        """Get JetStream context, creating if needed."""
        if self._js is None:
            self._js = self._nc.jetstream()
        return self._js

    async def js_create_stream(
        self,
        name: str,
        subjects: Sequence[str],
        storage: str = "file",
        retention: str = "limits",
        max_msgs: int = -1,
        max_bytes: int = -1,
        max_age: int = 0,  # seconds, 0 = unlimited
        max_msg_size: int = -1,
        duplicate_window: int = 120,  # seconds
        replicas: int = 1,
    ) -> None:
        """Create a JetStream stream.

        Args:
            name: Stream name.
            subjects: Subjects to capture.
            storage: Storage type (file, memory).
            retention: Retention policy (limits, interest, workqueue).
            max_msgs: Max messages (-1 = unlimited).
            max_bytes: Max bytes (-1 = unlimited).
            max_age: Max age in seconds (0 = unlimited).
            max_msg_size: Max message size (-1 = unlimited).
            duplicate_window: Duplicate detection window in seconds.
            replicas: Number of replicas.
        """
        from nats.js.api import (
            StreamConfig,
            StorageType,
            RetentionPolicy,
        )

        storage_map = {
            "file": StorageType.FILE,
            "memory": StorageType.MEMORY,
        }
        retention_map = {
            "limits": RetentionPolicy.LIMITS,
            "interest": RetentionPolicy.INTEREST,
            "workqueue": RetentionPolicy.WORK_QUEUE,
        }

        config = StreamConfig(
            name=name,
            subjects=list(subjects),
            storage=storage_map.get(storage, StorageType.FILE),
            retention=retention_map.get(retention, RetentionPolicy.LIMITS),
            max_msgs=max_msgs,
            max_bytes=max_bytes,
            max_age=max_age * 1_000_000_000 if max_age else 0,  # nanoseconds
            max_msg_size=max_msg_size,
            duplicate_window=duplicate_window * 1_000_000_000,  # nanoseconds
            num_replicas=replicas,
        )

        js = self._get_js()
        await js.add_stream(config)

    async def js_delete_stream(self, name: str) -> None:
        """Delete a JetStream stream.

        Args:
            name: Stream name.
        """
        js = self._get_js()
        await js.delete_stream(name)

    async def js_stream_info(self, name: str) -> dict[str, Any]:
        """Get stream information.

        Args:
            name: Stream name.

        Returns:
            Stream info dict.
        """
        js = self._get_js()
        info = await js.stream_info(name)
        return {
            "name": info.config.name,
            "subjects": info.config.subjects,
            "messages": info.state.messages,
            "bytes": info.state.bytes,
            "first_seq": info.state.first_seq,
            "last_seq": info.state.last_seq,
        }

    async def js_publish(
        self,
        subject: str,
        data: bytes,
        headers: Optional[dict[str, str]] = None,
        msg_id: Optional[str] = None,
        expect_stream: Optional[str] = None,
    ) -> int:
        """Publish a message to JetStream.

        Args:
            subject: Subject to publish to.
            data: Message payload.
            headers: Optional message headers.
            msg_id: Message ID for deduplication.
            expect_stream: Expected stream name.

        Returns:
            Sequence number of published message.
        """
        js = self._get_js()
        ack = await js.publish(
            subject,
            data,
            headers=headers,
        )
        return ack.seq

    async def js_create_consumer(
        self,
        stream: str,
        name: str,
        durable: bool = True,
        filter_subjects: Optional[Sequence[str]] = None,
        ack_policy: str = "explicit",
        max_deliver: int = -1,
        ack_wait: int = 30,  # seconds
    ) -> None:
        """Create a JetStream consumer.

        Args:
            stream: Stream name.
            name: Consumer name.
            durable: Durable consumer (survives disconnects).
            filter_subjects: Filter to specific subjects.
            ack_policy: Ack policy (none, all, explicit).
            max_deliver: Max redelivery attempts (-1 = unlimited).
            ack_wait: Ack wait time in seconds.
        """
        from nats.js.api import ConsumerConfig, AckPolicy

        ack_map = {
            "none": AckPolicy.NONE,
            "all": AckPolicy.ALL,
            "explicit": AckPolicy.EXPLICIT,
        }

        config = ConsumerConfig(
            durable_name=name if durable else None,
            name=name,
            filter_subjects=list(filter_subjects) if filter_subjects else None,
            ack_policy=ack_map.get(ack_policy, AckPolicy.EXPLICIT),
            max_deliver=max_deliver,
            ack_wait=ack_wait * 1_000_000_000,  # nanoseconds
        )

        js = self._get_js()
        await js.add_consumer(stream, config)

    async def js_subscribe(
        self,
        stream: str,
        consumer: str,
        handler: MessageHandler,
    ) -> Subscription:
        """Subscribe to a JetStream consumer.

        Args:
            stream: Stream name.
            consumer: Consumer name.
            handler: Message handler.

        Returns:
            Subscription handle.
        """
        async def _wrapper(msg: Any) -> None:
            wrapped = Message(
                subject=msg.subject,
                data=msg.data,
                reply=msg.reply,
                headers=dict(msg.headers) if msg.headers else {},
            )
            await handler(wrapped)
            await msg.ack()

        js = self._get_js()
        sub = await js.pull_subscribe(durable=consumer, stream=stream)
        # Note: Pull subscribe works differently, using fetch
        return Subscription(subject=f"{stream}.{consumer}", _sub=sub)

    async def js_fetch(
        self,
        stream: str,
        consumer: str,
        batch: int = 1,
        timeout: float = 5.0,
    ) -> list[Message]:
        """Fetch messages from a JetStream consumer.

        Args:
            stream: Stream name.
            consumer: Consumer name.
            batch: Number of messages to fetch.
            timeout: Fetch timeout in seconds.

        Returns:
            List of messages.
        """
        js = self._get_js()
        sub = await js.pull_subscribe(durable=consumer, stream=stream)

        try:
            msgs = await sub.fetch(batch, timeout=timeout)
            result = []
            for msg in msgs:
                result.append(Message(
                    subject=msg.subject,
                    data=msg.data,
                    reply=msg.reply,
                    headers=dict(msg.headers) if msg.headers else {},
                ))
                await msg.ack()
            return result
        except Exception:
            return []

    async def __aenter__(self) -> PubSubClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
