"""Scheduled jobs (cron) client for Hanzo infrastructure.

Provides async interface for scheduled/recurring jobs,
built on top of Redis for distributed scheduling.
"""

from __future__ import annotations

import os
import json
import asyncio
import hashlib
from typing import Any, Callable, Optional, Awaitable
from datetime import datetime, timedelta
from dataclasses import field, dataclass

from pydantic import Field, BaseModel


class CronConfig(BaseModel):
    """Configuration for cron scheduler connection."""

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=2, description="Redis database number")
    url: Optional[str] = Field(default=None, description="Full Redis URL")
    prefix: str = Field(default="hanzo:cron", description="Key prefix for cron")
    lock_timeout: int = Field(default=60, description="Lock timeout in seconds")
    timezone: str = Field(default="UTC", description="Default timezone")

    @classmethod
    def from_env(cls) -> CronConfig:
        """Create config from environment variables.

        Environment variables:
            CRON_REDIS_HOST: Server host (default: localhost)
            CRON_REDIS_PORT: Server port (default: 6379)
            CRON_REDIS_PASSWORD: Authentication password
            CRON_REDIS_DB: Database number (default: 2)
            CRON_REDIS_URL: Full URL (overrides host/port)
            CRON_PREFIX: Key prefix (default: hanzo:cron)
            CRON_TIMEZONE: Default timezone (default: UTC)
        """
        return cls(
            host=os.getenv("CRON_REDIS_HOST") or os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("CRON_REDIS_PORT") or os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("CRON_REDIS_PASSWORD") or os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("CRON_REDIS_DB", "2")),
            url=os.getenv("CRON_REDIS_URL") or os.getenv("REDIS_URL"),
            prefix=os.getenv("CRON_PREFIX", "hanzo:cron"),
            timezone=os.getenv("CRON_TIMEZONE", "UTC"),
        )


@dataclass
class CronJob:
    """A scheduled job definition."""

    id: str
    name: str
    schedule: str  # Cron expression or interval
    handler: str  # Handler name/identifier
    args: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    timezone: str = "UTC"
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "handler": self.handler,
            "args": self.args,
            "enabled": self.enabled,
            "timezone": self.timezone,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CronJob:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            schedule=data["schedule"],
            handler=data["handler"],
            args=data.get("args", {}),
            enabled=data.get("enabled", True),
            timezone=data.get("timezone", "UTC"),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            run_count=data.get("run_count", 0),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CronExecution:
    """Record of a job execution."""

    job_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


CronHandler = Callable[[CronJob], Awaitable[Any]]


class CronClient:
    """Async client for scheduled job management.

    Implements distributed cron scheduling on top of Redis,
    with support for cron expressions, intervals, and distributed locking.

    Example:
        ```python
        client = CronClient(CronConfig.from_env())
        await client.connect()

        # Register a job
        await client.register(
            "cleanup",
            "daily-cleanup",
            schedule="0 2 * * *",  # 2 AM daily
            handler="cleanup_old_files",
            args={"days": 30},
        )

        # Or with interval
        await client.register(
            "heartbeat",
            "service-heartbeat",
            schedule="@every 5m",  # Every 5 minutes
            handler="send_heartbeat",
        )

        # Run the scheduler (in a worker)
        handlers = {
            "cleanup_old_files": cleanup_handler,
            "send_heartbeat": heartbeat_handler,
        }
        await client.run_scheduler(handlers)

        # Manually trigger a job
        await client.trigger("cleanup")

        # List jobs
        jobs = await client.list_jobs()
        for job in jobs:
            print(f"{job.name}: next run at {job.next_run}")
        ```
    """

    def __init__(self, config: Optional[CronConfig] = None) -> None:
        """Initialize cron client.

        Args:
            config: Cron configuration. If None, loads from environment.
        """
        self.config = config or CronConfig.from_env()
        self._redis: Any = None
        self._running = False

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            import redis.asyncio as redis
        except ImportError as e:
            raise ImportError("redis is required for CronClient. Install with: pip install redis") from e

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
        self._running = False
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

    def _parse_schedule(self, schedule: str) -> datetime:
        """Parse a schedule and return the next run time.

        Supports:
        - Cron expressions: "* * * * *" (min hour day month weekday)
        - Intervals: "@every 5m", "@every 1h", "@every 30s"
        - Named schedules: "@hourly", "@daily", "@weekly", "@monthly"
        """
        now = datetime.utcnow()

        # Handle interval syntax
        if schedule.startswith("@every "):
            interval_str = schedule[7:]
            return now + self._parse_interval(interval_str)

        # Handle named schedules
        named = {
            "@hourly": "0 * * * *",
            "@daily": "0 0 * * *",
            "@weekly": "0 0 * * 0",
            "@monthly": "0 0 1 * *",
            "@yearly": "0 0 1 1 *",
            "@annually": "0 0 1 1 *",
        }
        if schedule in named:
            schedule = named[schedule]

        # Parse cron expression
        try:
            from croniter import croniter
        except ImportError:
            # Fallback: simple interval-based scheduling
            # Default to hourly if croniter not available
            return now + timedelta(hours=1)

        cron = croniter(schedule, now)
        return cron.get_next(datetime)

    def _parse_interval(self, interval: str) -> timedelta:
        """Parse an interval string like '5m', '1h', '30s'."""
        units = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
        }

        if not interval:
            return timedelta(hours=1)

        unit = interval[-1].lower()
        if unit not in units:
            raise ValueError(f"Unknown interval unit: {unit}")

        try:
            value = int(interval[:-1])
        except ValueError:
            raise ValueError(f"Invalid interval value: {interval[:-1]}")

        return timedelta(seconds=value * units[unit])

    # Job management

    async def register(
        self,
        job_id: str,
        name: str,
        schedule: str,
        handler: str,
        args: Optional[dict[str, Any]] = None,
        timezone: Optional[str] = None,
        enabled: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CronJob:
        """Register a scheduled job.

        Args:
            job_id: Unique job identifier.
            name: Human-readable job name.
            schedule: Cron expression or interval.
            handler: Handler name/identifier.
            args: Arguments to pass to handler.
            timezone: Job timezone.
            enabled: Whether job is enabled.
            metadata: Additional metadata.

        Returns:
            Created CronJob.
        """
        next_run = self._parse_schedule(schedule) if enabled else None

        job = CronJob(
            id=job_id,
            name=name,
            schedule=schedule,
            handler=handler,
            args=args or {},
            enabled=enabled,
            timezone=timezone or self.config.timezone,
            next_run=next_run,
            metadata=metadata or {},
        )

        # Store job
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Add to jobs set
        jobs_key = self._key("jobs")
        await self._redis.sadd(jobs_key, job_id)

        # Add to schedule
        if enabled and next_run:
            schedule_key = self._key("schedule")
            await self._redis.zadd(schedule_key, {job_id: next_run.timestamp()})

        return job

    async def unregister(self, job_id: str) -> bool:
        """Unregister a job.

        Args:
            job_id: Job ID to remove.

        Returns:
            True if job was removed.
        """
        job_key = self._key("job", job_id)
        jobs_key = self._key("jobs")
        schedule_key = self._key("schedule")

        existed = await self._redis.delete(job_key)
        await self._redis.srem(jobs_key, job_id)
        await self._redis.zrem(schedule_key, job_id)

        return existed > 0

    async def get_job(self, job_id: str) -> Optional[CronJob]:
        """Get a job by ID.

        Args:
            job_id: Job ID.

        Returns:
            CronJob or None.
        """
        job_key = self._key("job", job_id)
        data = await self._redis.get(job_key)
        if not data:
            return None
        return CronJob.from_dict(json.loads(data))

    async def list_jobs(self) -> list[CronJob]:
        """List all registered jobs.

        Returns:
            List of CronJob objects.
        """
        jobs_key = self._key("jobs")
        job_ids = await self._redis.smembers(jobs_key)

        jobs = []
        for job_id in job_ids:
            job = await self.get_job(job_id)
            if job:
                jobs.append(job)

        return sorted(jobs, key=lambda j: j.name)

    async def enable_job(self, job_id: str) -> bool:
        """Enable a job.

        Args:
            job_id: Job ID.

        Returns:
            True if job was enabled.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        job.enabled = True
        job.next_run = self._parse_schedule(job.schedule)

        # Update job
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Add to schedule
        schedule_key = self._key("schedule")
        await self._redis.zadd(schedule_key, {job_id: job.next_run.timestamp()})

        return True

    async def disable_job(self, job_id: str) -> bool:
        """Disable a job.

        Args:
            job_id: Job ID.

        Returns:
            True if job was disabled.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        job.enabled = False
        job.next_run = None

        # Update job
        job_key = self._key("job", job_id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Remove from schedule
        schedule_key = self._key("schedule")
        await self._redis.zrem(schedule_key, job_id)

        return True

    async def trigger(self, job_id: str) -> Optional[CronExecution]:
        """Manually trigger a job execution.

        Args:
            job_id: Job ID to trigger.

        Returns:
            Execution result or None if job not found.
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        # Schedule for immediate execution
        schedule_key = self._key("schedule")
        await self._redis.zadd(schedule_key, {job_id: datetime.utcnow().timestamp()})

        return CronExecution(
            job_id=job_id,
            started_at=datetime.utcnow(),
        )

    # Scheduler

    async def _acquire_lock(self, job_id: str) -> bool:
        """Acquire a distributed lock for a job."""
        lock_key = self._key("lock", job_id)
        lock_value = hashlib.md5(f"{os.getpid()}-{datetime.utcnow().isoformat()}".encode()).hexdigest()

        acquired = await self._redis.set(
            lock_key,
            lock_value,
            ex=self.config.lock_timeout,
            nx=True,
        )
        return acquired is not None

    async def _release_lock(self, job_id: str) -> None:
        """Release a distributed lock."""
        lock_key = self._key("lock", job_id)
        await self._redis.delete(lock_key)

    async def _execute_job(
        self,
        job: CronJob,
        handlers: dict[str, CronHandler],
    ) -> CronExecution:
        """Execute a job."""
        execution = CronExecution(
            job_id=job.id,
            started_at=datetime.utcnow(),
        )

        handler = handlers.get(job.handler)
        if not handler:
            execution.error = f"Handler not found: {job.handler}"
            return execution

        try:
            result = await handler(job)
            execution.success = True
            execution.result = result
        except Exception as e:
            execution.success = False
            execution.error = str(e)

        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

        # Update job stats
        job.last_run = execution.started_at
        job.run_count += 1
        if not execution.success:
            job.error_count += 1
            job.last_error = execution.error

        # Schedule next run
        job.next_run = self._parse_schedule(job.schedule)

        # Save job
        job_key = self._key("job", job.id)
        await self._redis.set(job_key, json.dumps(job.to_dict()))

        # Update schedule
        schedule_key = self._key("schedule")
        await self._redis.zadd(schedule_key, {job.id: job.next_run.timestamp()})

        return execution

    async def run_scheduler(
        self,
        handlers: dict[str, CronHandler],
        poll_interval: float = 1.0,
    ) -> None:
        """Run the cron scheduler (blocking).

        Args:
            handlers: Map of handler names to functions.
            poll_interval: Seconds between schedule checks.
        """
        self._running = True
        schedule_key = self._key("schedule")

        while self._running:
            try:
                now = datetime.utcnow().timestamp()

                # Get jobs due to run
                due_jobs = await self._redis.zrangebyscore(schedule_key, "-inf", now)

                for job_id in due_jobs:
                    # Try to acquire lock
                    if not await self._acquire_lock(job_id):
                        continue  # Another worker has this job

                    try:
                        job = await self.get_job(job_id)
                        if job and job.enabled:
                            await self._execute_job(job, handlers)
                    finally:
                        await self._release_lock(job_id)

                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but keep running
                await asyncio.sleep(poll_interval)

    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self._running = False

    # History (optional - for debugging)

    async def get_recent_executions(
        self,
        job_id: str,
        limit: int = 10,
    ) -> list[CronExecution]:
        """Get recent executions for a job.

        Args:
            job_id: Job ID.
            limit: Maximum executions to return.

        Returns:
            List of recent executions (most recent first).
        """
        history_key = self._key("history", job_id)
        entries = await self._redis.lrange(history_key, 0, limit - 1)

        executions = []
        for entry in entries:
            data = json.loads(entry)
            executions.append(
                CronExecution(
                    job_id=data["job_id"],
                    started_at=datetime.fromisoformat(data["started_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                    success=data.get("success", False),
                    result=data.get("result"),
                    error=data.get("error"),
                    duration_ms=data.get("duration_ms", 0),
                )
            )

        return executions

    async def __aenter__(self) -> CronClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
