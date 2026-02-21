"""Work queue client for Hanzo infrastructure.

Provides async interface for distributed work queues,
built on top of Redis/Valkey for simplicity and reliability.
"""

from __future__ import annotations

import os
import json
import uuid
import asyncio
from enum import Enum
from typing import Any, Callable, Optional, Awaitable
from datetime import datetime, timedelta
from dataclasses import field, dataclass

from pydantic import Field, BaseModel


class QueuesConfig(BaseModel):
    """Configuration for work queue connection."""

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=1, description="Redis database number")
    url: Optional[str] = Field(default=None, description="Full Redis URL")
    prefix: str = Field(default="hanzo:queue", description="Key prefix for queues")
    default_timeout: int = Field(default=300, description="Default job timeout in seconds")
    default_ttl: int = Field(default=86400, description="Default result TTL in seconds")

    @classmethod
    def from_env(cls) -> QueuesConfig:
        """Create config from environment variables.

        Environment variables:
            QUEUE_REDIS_HOST: Server host (default: localhost)
            QUEUE_REDIS_PORT: Server port (default: 6379)
            QUEUE_REDIS_PASSWORD: Authentication password
            QUEUE_REDIS_DB: Database number (default: 1)
            QUEUE_REDIS_URL: Full URL (overrides host/port)
            QUEUE_PREFIX: Key prefix (default: hanzo:queue)
        """
        return cls(
            host=os.getenv("QUEUE_REDIS_HOST") or os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("QUEUE_REDIS_PORT") or os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("QUEUE_REDIS_PASSWORD") or os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("QUEUE_REDIS_DB", "1")),
            url=os.getenv("QUEUE_REDIS_URL") or os.getenv("REDIS_URL"),
            prefix=os.getenv("QUEUE_PREFIX", "hanzo:queue"),
        )


class JobStatus(str, Enum):
    """Status of a queued job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Job:
    """A work queue job."""

    id: str
    queue: str
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    timeout: int = 300  # seconds
    ttl: int = 86400  # result TTL in seconds
    priority: int = 0  # higher = more priority
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "queue": self.queue,
            "name": self.name,
            "args": self.args,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "timeout": self.timeout,
            "ttl": self.ttl,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            queue=data["queue"],
            name=data["name"],
            args=data.get("args", {}),
            status=JobStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            timeout=data.get("timeout", 300),
            ttl=data.get("ttl", 86400),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class QueueStats:
    """Statistics for a queue."""

    name: str
    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0


JobHandler = Callable[[Job], Awaitable[Any]]


class QueuesClient:
    """Async client for distributed work queues.

    Implements a simple but reliable work queue on top of Redis,
    with support for priorities, retries, and result storage.

    Example:
        ```python
        client = QueuesClient(QueuesConfig.from_env())
        await client.connect()

        # Enqueue jobs
        job_id = await client.enqueue(
            "emails",
            "send_welcome",
            args={"user_id": "123", "email": "user@example.com"},
            priority=10,
        )

        # Get job status
        job = await client.get_job(job_id)
        print(f"Status: {job.status}")


        # Process jobs (in a worker)
        async def handler(job: Job) -> str:
            # Do work...
            return "sent"


        await client.process("emails", handler)

        # Get result
        result = await client.get_result(job_id)
        ```
    """

    def __init__(self, config: Optional[QueuesConfig] = None) -> None:
        """Initialize queues client.

        Args:
            config: Queue configuration. If None, loads from environment.
        """
        self.config = config or QueuesConfig.from_env()
        self._redis: Any = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            import redis.asyncio as redis
        except ImportError as e:
            raise ImportError("redis is required for QueuesClient. Install with: pip install redis") from e

        if self.config.url:
            self._redis = redis.from_url(
                self.config.url,
                decode_responses=True,
            )
        else:
            self._redis = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                decode_responses=True,
            )

    async def close(self) -> None:
        """Close the connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def health_check(self) -> bool:
        """Check if Redis is healthy.

        Returns:
            True if Redis is responding.
        """
        if not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False

    def _key(self, *parts: str) -> str:
        """Build a Redis key with prefix."""
        return ":".join([self.config.prefix, *parts])

    # Job operations

    async def enqueue(
        self,
        queue: str,
        name: str,
        args: Optional[dict[str, Any]] = None,
        job_id: Optional[str] = None,
        priority: int = 0,
        delay: Optional[timedelta] = None,
        timeout: Optional[int] = None,
        max_attempts: int = 3,
        ttl: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Enqueue a job.

        Args:
            queue: Queue name.
            name: Job name/type.
            args: Job arguments.
            job_id: Custom job ID (auto-generated if not specified).
            priority: Job priority (higher = more priority).
            delay: Delay before job becomes available.
            timeout: Job timeout in seconds.
            max_attempts: Maximum retry attempts.
            ttl: Result TTL in seconds.
            metadata: Additional metadata.

        Returns:
            Job ID.
        """
        job = Job(
            id=job_id or f"{name}-{uuid.uuid4().hex[:12]}",
            queue=queue,
            name=name,
            args=args or {},
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            max_attempts=max_attempts,
            timeout=timeout or self.config.default_timeout,
            ttl=ttl or self.config.default_ttl,
            priority=priority,
            metadata=metadata or {},
        )

        # Store job data
        job_key = self._key("job", job.id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Add to queue
        queue_key = self._key("queue", queue)
        score = -priority  # Redis ZSET is ascending, we want descending priority

        if delay:
            # Delayed job - use scheduled set
            scheduled_key = self._key("scheduled", queue)
            execute_at = datetime.utcnow() + delay
            await self._redis.zadd(scheduled_key, {job.id: execute_at.timestamp()})
        else:
            # Immediate job
            await self._redis.zadd(queue_key, {job.id: score})

        return job.id

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.

        Args:
            job_id: Job ID.

        Returns:
            Job or None if not found.
        """
        job_key = self._key("job", job_id)
        data = await self._redis.get(job_key)
        if not data:
            return None
        return Job.from_dict(json.loads(data))

    async def get_result(self, job_id: str, timeout: float = 0) -> Any:
        """Get a job's result.

        Args:
            job_id: Job ID.
            timeout: Seconds to wait for result (0 = don't wait).

        Returns:
            Job result or None.
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        if job.status == JobStatus.COMPLETED:
            return job.result

        if timeout > 0 and job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            # Poll for completion
            end_time = datetime.utcnow() + timedelta(seconds=timeout)
            while datetime.utcnow() < end_time:
                await asyncio.sleep(0.5)
                job = await self.get_job(job_id)
                if job and job.status == JobStatus.COMPLETED:
                    return job.result
                if job and job.status == JobStatus.FAILED:
                    raise Exception(f"Job failed: {job.error}")

        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: Job ID.

        Returns:
            True if cancelled, False if job not found or already processed.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status not in (JobStatus.PENDING, JobStatus.RETRYING):
            return False

        # Remove from queue
        queue_key = self._key("queue", job.queue)
        await self._redis.zrem(queue_key, job_id)

        # Update status
        job.status = JobStatus.CANCELLED
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        return True

    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job.

        Args:
            job_id: Job ID.

        Returns:
            True if job was requeued.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status != JobStatus.FAILED:
            return False

        # Reset and requeue
        job.status = JobStatus.RETRYING
        job.error = None
        job.started_at = None
        job.completed_at = None

        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        queue_key = self._key("queue", job.queue)
        await self._redis.zadd(queue_key, {job_id: -job.priority})

        return True

    # Queue operations

    async def get_queue_stats(self, queue: str) -> QueueStats:
        """Get queue statistics.

        Args:
            queue: Queue name.

        Returns:
            Queue statistics.
        """
        queue_key = self._key("queue", queue)
        running_key = self._key("running", queue)

        pending = await self._redis.zcard(queue_key)
        running = await self._redis.scard(running_key)

        # Count completed/failed from recent jobs (expensive, use sparingly)
        completed = 0
        failed = 0

        return QueueStats(
            name=queue,
            pending=pending,
            running=running,
            completed=completed,
            failed=failed,
        )

    async def list_queues(self) -> list[str]:
        """List all queues.

        Returns:
            List of queue names.
        """
        pattern = self._key("queue", "*")
        keys = await self._redis.keys(pattern)
        prefix_len = len(self._key("queue", ""))
        return [k[prefix_len:] for k in keys]

    async def purge_queue(self, queue: str) -> int:
        """Remove all jobs from a queue.

        Args:
            queue: Queue name.

        Returns:
            Number of jobs removed.
        """
        queue_key = self._key("queue", queue)
        count = await self._redis.zcard(queue_key)
        await self._redis.delete(queue_key)
        return count

    # Worker operations

    async def dequeue(
        self,
        queue: str,
        timeout: float = 0,
    ) -> Optional[Job]:
        """Dequeue a job for processing.

        Args:
            queue: Queue name.
            timeout: Seconds to wait for a job (0 = don't wait).

        Returns:
            Job or None if queue is empty.
        """
        queue_key = self._key("queue", queue)
        running_key = self._key("running", queue)

        # Move scheduled jobs that are ready
        await self._move_scheduled_jobs(queue)

        # Try to get a job
        result = await self._redis.zpopmin(queue_key, 1)
        if not result:
            if timeout > 0:
                # Wait for job with blocking pop
                result = await self._redis.bzpopmin(queue_key, timeout)
                if result:
                    _, job_id, _ = result
                else:
                    return None
            else:
                return None
        else:
            job_id = result[0][0]

        # Get job data
        job = await self.get_job(job_id)
        if not job:
            return None

        # Mark as running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.attempts += 1

        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Add to running set
        await self._redis.sadd(running_key, job_id)

        return job

    async def _move_scheduled_jobs(self, queue: str) -> None:
        """Move scheduled jobs that are ready to the main queue."""
        scheduled_key = self._key("scheduled", queue)
        queue_key = self._key("queue", queue)

        now = datetime.utcnow().timestamp()

        # Get jobs that are ready
        ready = await self._redis.zrangebyscore(scheduled_key, "-inf", now)

        for job_id in ready:
            job = await self.get_job(job_id)
            if job:
                # Move to main queue
                await self._redis.zrem(scheduled_key, job_id)
                await self._redis.zadd(queue_key, {job_id: -job.priority})

    async def complete_job(
        self,
        job_id: str,
        result: Any = None,
    ) -> None:
        """Mark a job as completed.

        Args:
            job_id: Job ID.
            result: Job result.
        """
        job = await self.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.utcnow()

        # Update job
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))
        await self._redis.expire(job_key, job.ttl)

        # Remove from running
        running_key = self._key("running", job.queue)
        await self._redis.srem(running_key, job_id)

    async def fail_job(
        self,
        job_id: str,
        error: str,
    ) -> None:
        """Mark a job as failed.

        Args:
            job_id: Job ID.
            error: Error message.
        """
        job = await self.get_job(job_id)
        if not job:
            return

        # Check if should retry
        if job.attempts < job.max_attempts:
            job.status = JobStatus.RETRYING
            job.error = error

            # Requeue with backoff
            delay = min(60 * (2**job.attempts), 3600)  # Exponential backoff, max 1 hour
            queue_key = self._key("queue", job.queue)
            scheduled_key = self._key("scheduled", job.queue)
            execute_at = datetime.utcnow() + timedelta(seconds=delay)
            await self._redis.zadd(scheduled_key, {job_id: execute_at.timestamp()})
        else:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.utcnow()

        # Update job
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Remove from running
        running_key = self._key("running", job.queue)
        await self._redis.srem(running_key, job_id)

    async def process(
        self,
        queue: str,
        handler: JobHandler,
        batch_size: int = 1,
        poll_interval: float = 1.0,
    ) -> None:
        """Process jobs from a queue (blocking).

        Args:
            queue: Queue name.
            handler: Async job handler function.
            batch_size: Jobs to process before checking for more.
            poll_interval: Seconds between queue checks.
        """
        while True:
            for _ in range(batch_size):
                job = await self.dequeue(queue, timeout=poll_interval)
                if not job:
                    break

                try:
                    result = await asyncio.wait_for(
                        handler(job),
                        timeout=job.timeout,
                    )
                    await self.complete_job(job.id, result)
                except asyncio.TimeoutError:
                    await self.fail_job(job.id, "Job timed out")
                except Exception as e:
                    await self.fail_job(job.id, str(e))

    async def __aenter__(self) -> QueuesClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
