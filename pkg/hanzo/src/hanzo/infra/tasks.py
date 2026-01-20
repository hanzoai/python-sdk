"""Temporal workflow client wrapper for Hanzo infrastructure.

Provides async interface to Temporal for durable workflows,
activities, and task orchestration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class TasksConfig(BaseModel):
    """Configuration for Temporal connection."""

    host: str = Field(default="localhost", description="Temporal server host")
    port: int = Field(default=7233, description="Temporal server port")
    namespace: str = Field(default="default", description="Temporal namespace")
    target: Optional[str] = Field(default=None, description="Full target address (overrides host/port)")
    tls: bool = Field(default=False, description="Use TLS")
    tls_cert_path: Optional[str] = Field(default=None, description="Path to TLS certificate")
    tls_key_path: Optional[str] = Field(default=None, description="Path to TLS key")
    api_key: Optional[str] = Field(default=None, description="API key for Temporal Cloud")
    identity: str = Field(default="hanzo-client", description="Client identity")
    data_converter: Optional[str] = Field(default=None, description="Custom data converter class")

    @classmethod
    def from_env(cls) -> TasksConfig:
        """Create config from environment variables.

        Environment variables:
            TEMPORAL_HOST: Server host (default: localhost)
            TEMPORAL_PORT: Server port (default: 7233)
            TEMPORAL_NAMESPACE: Namespace (default: default)
            TEMPORAL_TARGET: Full target address (overrides host/port)
            TEMPORAL_TLS: Use TLS (default: false)
            TEMPORAL_TLS_CERT: Path to TLS certificate
            TEMPORAL_TLS_KEY: Path to TLS key
            TEMPORAL_API_KEY: API key for Temporal Cloud
        """
        return cls(
            host=os.getenv("TEMPORAL_HOST", "localhost"),
            port=int(os.getenv("TEMPORAL_PORT", "7233")),
            namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
            target=os.getenv("TEMPORAL_TARGET"),
            tls=os.getenv("TEMPORAL_TLS", "").lower() in ("true", "1", "yes"),
            tls_cert_path=os.getenv("TEMPORAL_TLS_CERT"),
            tls_key_path=os.getenv("TEMPORAL_TLS_KEY"),
            api_key=os.getenv("TEMPORAL_API_KEY"),
        )

    @property
    def effective_target(self) -> str:
        """Get the effective target address."""
        return self.target or f"{self.host}:{self.port}"


@dataclass
class WorkflowExecution:
    """Information about a workflow execution."""

    workflow_id: str
    run_id: str
    workflow_type: str
    status: str
    start_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    history_length: int = 0
    memo: dict[str, Any] = field(default_factory=dict)
    search_attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowHandle:
    """Handle to a running workflow."""

    workflow_id: str
    run_id: Optional[str] = None
    _handle: Any = None

    async def result(self) -> Any:
        """Wait for and return the workflow result."""
        if self._handle:
            return await self._handle.result()
        return None

    async def cancel(self) -> None:
        """Request cancellation of the workflow."""
        if self._handle:
            await self._handle.cancel()

    async def terminate(self, reason: str = "") -> None:
        """Terminate the workflow."""
        if self._handle:
            await self._handle.terminate(reason)

    async def signal(self, name: str, *args: Any) -> None:
        """Send a signal to the workflow."""
        if self._handle:
            await self._handle.signal(name, *args)

    async def query(self, name: str, *args: Any) -> Any:
        """Query the workflow state."""
        if self._handle:
            return await self._handle.query(name, *args)
        return None

    async def describe(self) -> WorkflowExecution:
        """Get workflow execution details."""
        if self._handle:
            desc = await self._handle.describe()
            return WorkflowExecution(
                workflow_id=desc.id,
                run_id=desc.run_id,
                workflow_type=desc.workflow_type,
                status=str(desc.status),
                start_time=desc.start_time,
                close_time=desc.close_time,
            )
        return WorkflowExecution(
            workflow_id=self.workflow_id,
            run_id=self.run_id or "",
            workflow_type="",
            status="UNKNOWN",
        )


class TasksClient:
    """Async client for Temporal workflow orchestration.

    Wraps temporalio SDK with Hanzo conventions for workflow
    execution, activities, and task management.

    Example:
        ```python
        client = TasksClient(TasksConfig.from_env())
        await client.connect()

        # Start a workflow
        handle = await client.start_workflow(
            "ProcessOrder",
            args={"order_id": "123"},
            id="order-123",
            task_queue="orders",
        )

        # Wait for result
        result = await handle.result()

        # Query workflow state
        state = await handle.query("get_status")

        # Send signal
        await handle.signal("approve", {"user": "admin"})

        # List workflows
        async for wf in client.list_workflows("WorkflowType = 'ProcessOrder'"):
            print(wf.workflow_id, wf.status)
        ```
    """

    def __init__(self, config: Optional[TasksConfig] = None) -> None:
        """Initialize tasks client.

        Args:
            config: Temporal configuration. If None, loads from environment.
        """
        self.config = config or TasksConfig.from_env()
        self._client: Any = None

    async def connect(self) -> None:
        """Establish connection to Temporal server."""
        try:
            from temporalio.client import Client, TLSConfig
        except ImportError as e:
            raise ImportError(
                "temporalio is required for TasksClient. "
                "Install with: pip install temporalio"
            ) from e

        connect_kwargs: dict[str, Any] = {
            "target_host": self.config.effective_target,
            "namespace": self.config.namespace,
            "identity": self.config.identity,
        }

        if self.config.tls:
            tls_config = TLSConfig()
            if self.config.tls_cert_path and self.config.tls_key_path:
                with open(self.config.tls_cert_path, "rb") as f:
                    cert = f.read()
                with open(self.config.tls_key_path, "rb") as f:
                    key = f.read()
                tls_config = TLSConfig(client_cert=cert, client_private_key=key)
            connect_kwargs["tls"] = tls_config

        if self.config.api_key:
            connect_kwargs["api_key"] = self.config.api_key

        self._client = await Client.connect(**connect_kwargs)

    async def close(self) -> None:
        """Close the connection."""
        # Temporal client doesn't require explicit close
        self._client = None

    async def health_check(self) -> bool:
        """Check if Temporal server is healthy.

        Returns:
            True if server is reachable.
        """
        if not self._client:
            return False
        try:
            # Try to get system info
            await self._client.service_client.check_health()
            return True
        except Exception:
            # Fallback: try listing workflows with limit 1
            try:
                async for _ in self._client.list_workflows(query="", page_size=1):
                    break
                return True
            except Exception:
                return False

    # Workflow operations

    async def start_workflow(
        self,
        workflow: str,
        args: Any = None,
        id: Optional[str] = None,
        task_queue: str = "default",
        execution_timeout: Optional[timedelta] = None,
        run_timeout: Optional[timedelta] = None,
        task_timeout: Optional[timedelta] = None,
        id_reuse_policy: str = "allow_duplicate",
        retry_policy: Optional[dict[str, Any]] = None,
        cron_schedule: Optional[str] = None,
        memo: Optional[dict[str, Any]] = None,
        search_attributes: Optional[dict[str, Any]] = None,
    ) -> WorkflowHandle:
        """Start a workflow execution.

        Args:
            workflow: Workflow type name.
            args: Workflow arguments.
            id: Workflow ID (auto-generated if not specified).
            task_queue: Task queue for the workflow.
            execution_timeout: Max workflow execution time.
            run_timeout: Max single run time.
            task_timeout: Max workflow task time.
            id_reuse_policy: ID reuse policy (allow_duplicate, allow_duplicate_failed_only, reject_duplicate, terminate_if_running).
            retry_policy: Retry configuration.
            cron_schedule: Cron schedule expression.
            memo: Workflow memo fields.
            search_attributes: Custom search attributes.

        Returns:
            Handle to the started workflow.
        """
        from temporalio.client import WorkflowIDReusePolicy
        from temporalio.common import RetryPolicy
        import uuid

        policy_map = {
            "allow_duplicate": WorkflowIDReusePolicy.ALLOW_DUPLICATE,
            "allow_duplicate_failed_only": WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
            "reject_duplicate": WorkflowIDReusePolicy.REJECT_DUPLICATE,
            "terminate_if_running": WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
        }

        start_kwargs: dict[str, Any] = {
            "workflow": workflow,
            "arg": args,
            "id": id or f"{workflow}-{uuid.uuid4().hex[:8]}",
            "task_queue": task_queue,
            "id_reuse_policy": policy_map.get(id_reuse_policy, WorkflowIDReusePolicy.ALLOW_DUPLICATE),
        }

        if execution_timeout:
            start_kwargs["execution_timeout"] = execution_timeout
        if run_timeout:
            start_kwargs["run_timeout"] = run_timeout
        if task_timeout:
            start_kwargs["task_timeout"] = task_timeout
        if cron_schedule:
            start_kwargs["cron_schedule"] = cron_schedule
        if memo:
            start_kwargs["memo"] = memo
        if search_attributes:
            start_kwargs["search_attributes"] = search_attributes

        if retry_policy:
            start_kwargs["retry_policy"] = RetryPolicy(
                initial_interval=timedelta(seconds=retry_policy.get("initial_interval", 1)),
                maximum_interval=timedelta(seconds=retry_policy.get("maximum_interval", 100)),
                backoff_coefficient=retry_policy.get("backoff_coefficient", 2.0),
                maximum_attempts=retry_policy.get("maximum_attempts", 0),
            )

        handle = await self._client.start_workflow(**start_kwargs)
        return WorkflowHandle(
            workflow_id=handle.id,
            run_id=handle.result_run_id,
            _handle=handle,
        )

    async def execute_workflow(
        self,
        workflow: str,
        args: Any = None,
        id: Optional[str] = None,
        task_queue: str = "default",
        **kwargs: Any,
    ) -> Any:
        """Start a workflow and wait for its result.

        Args:
            workflow: Workflow type name.
            args: Workflow arguments.
            id: Workflow ID.
            task_queue: Task queue.
            **kwargs: Additional start_workflow arguments.

        Returns:
            Workflow result.
        """
        handle = await self.start_workflow(workflow, args, id, task_queue, **kwargs)
        return await handle.result()

    async def get_workflow_handle(
        self,
        workflow_id: str,
        run_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """Get a handle to an existing workflow.

        Args:
            workflow_id: Workflow ID.
            run_id: Optional specific run ID.

        Returns:
            Workflow handle.
        """
        handle = self._client.get_workflow_handle(workflow_id, run_id=run_id)
        return WorkflowHandle(
            workflow_id=workflow_id,
            run_id=run_id,
            _handle=handle,
        )

    async def list_workflows(
        self,
        query: str = "",
        page_size: int = 100,
    ):
        """List workflow executions.

        Args:
            query: Temporal list filter query.
            page_size: Results per page.

        Yields:
            WorkflowExecution for each matching workflow.
        """
        async for wf in self._client.list_workflows(query=query, page_size=page_size):
            yield WorkflowExecution(
                workflow_id=wf.id,
                run_id=wf.run_id,
                workflow_type=wf.workflow_type,
                status=str(wf.status),
                start_time=wf.start_time,
                close_time=wf.close_time,
                memo=dict(wf.memo) if wf.memo else {},
                search_attributes=dict(wf.search_attributes) if wf.search_attributes else {},
            )

    async def count_workflows(self, query: str = "") -> int:
        """Count workflow executions matching a query.

        Args:
            query: Temporal list filter query.

        Returns:
            Number of matching workflows.
        """
        count = 0
        async for _ in self._client.list_workflows(query=query):
            count += 1
        return count

    # Schedule operations

    async def create_schedule(
        self,
        schedule_id: str,
        workflow: str,
        args: Any = None,
        task_queue: str = "default",
        cron: Optional[str] = None,
        interval: Optional[timedelta] = None,
        calendar: Optional[dict[str, Any]] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        jitter: Optional[timedelta] = None,
        memo: Optional[dict[str, Any]] = None,
    ) -> None:
        """Create a workflow schedule.

        Args:
            schedule_id: Unique schedule ID.
            workflow: Workflow type name.
            args: Workflow arguments.
            task_queue: Task queue.
            cron: Cron expression (e.g., "0 * * * *").
            interval: Interval between runs.
            calendar: Calendar-based schedule spec.
            start_at: Schedule start time.
            end_at: Schedule end time.
            jitter: Random jitter to add to scheduled times.
            memo: Schedule memo fields.
        """
        from temporalio.client import (
            Schedule,
            ScheduleSpec,
            ScheduleActionStartWorkflow,
            ScheduleIntervalSpec,
            ScheduleCalendarSpec,
        )

        specs = []
        if cron:
            specs.append(ScheduleSpec(cron_expressions=[cron]))
        if interval:
            specs.append(ScheduleSpec(intervals=[ScheduleIntervalSpec(every=interval)]))
        if calendar:
            specs.append(ScheduleSpec(calendars=[ScheduleCalendarSpec(**calendar)]))

        if not specs:
            raise ValueError("At least one of cron, interval, or calendar must be specified")

        schedule_spec = specs[0] if len(specs) == 1 else ScheduleSpec(
            cron_expressions=[cron] if cron else None,
            intervals=[ScheduleIntervalSpec(every=interval)] if interval else None,
            calendars=[ScheduleCalendarSpec(**calendar)] if calendar else None,
            start_at=start_at,
            end_at=end_at,
            jitter=jitter,
        )

        await self._client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow,
                    arg=args,
                    task_queue=task_queue,
                ),
                spec=schedule_spec,
            ),
            memo=memo,
        )

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule.

        Args:
            schedule_id: Schedule ID to delete.
        """
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.delete()

    async def pause_schedule(self, schedule_id: str, note: str = "") -> None:
        """Pause a schedule.

        Args:
            schedule_id: Schedule ID to pause.
            note: Optional note about why paused.
        """
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.pause(note=note)

    async def unpause_schedule(self, schedule_id: str, note: str = "") -> None:
        """Unpause a schedule.

        Args:
            schedule_id: Schedule ID to unpause.
            note: Optional note.
        """
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.unpause(note=note)

    async def trigger_schedule(self, schedule_id: str) -> None:
        """Trigger a schedule immediately.

        Args:
            schedule_id: Schedule ID to trigger.
        """
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.trigger()

    async def __aenter__(self) -> TasksClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
