"""Hanzo Tasks client — wraps Temporal client with Hanzo conventions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from temporalio.client import Client as TemporalClient


@dataclass
class TasksConfig:
    """Configuration for connecting to Temporal."""

    address: str = "localhost:7233"
    namespace: str = "hanzo"
    tls: bool = False


class WorkflowHandle:
    """Handle to a running workflow."""

    def __init__(self, handle: Any) -> None:
        self._handle = handle

    @property
    def id(self) -> str:
        return self._handle.id

    @property
    def run_id(self) -> str:
        return self._handle.result_run_id

    async def result(self, result_type: type | None = None) -> Any:
        return await self._handle.result(result_type=result_type)

    async def cancel(self) -> None:
        await self._handle.cancel()

    async def signal(self, name: str, data: Any = None) -> None:
        await self._handle.signal(name, data)


class Client:
    """Hanzo Tasks client for submitting and managing workflows."""

    def __init__(self, temporal: TemporalClient) -> None:
        self._temporal = temporal

    @classmethod
    async def connect(cls, config: TasksConfig | None = None) -> Client:
        """Connect to Temporal server."""
        cfg = config or TasksConfig()
        temporal = await TemporalClient.connect(cfg.address, namespace=cfg.namespace)
        return cls(temporal)

    async def submit(
        self,
        workflow: Any,
        input: Any,
        *,
        id: str | None = None,
        queue: str = "default",
        **kwargs: Any,
    ) -> WorkflowHandle:
        """Submit a workflow for execution."""
        handle = await self._temporal.start_workflow(
            workflow,
            input,
            id=id or str(uuid4()),
            task_queue=queue,
            **kwargs,
        )
        return WorkflowHandle(handle)

    async def get_result(self, workflow_id: str, result_type: type | None = None) -> Any:
        """Get the result of a completed workflow."""
        handle = self._temporal.get_workflow_handle(workflow_id)
        return await handle.result(result_type=result_type)

    async def cancel(self, workflow_id: str) -> None:
        """Cancel a running workflow."""
        handle = self._temporal.get_workflow_handle(workflow_id)
        await handle.cancel()

    async def signal(self, workflow_id: str, signal_name: str, data: Any = None) -> None:
        """Send a signal to a running workflow."""
        handle = self._temporal.get_workflow_handle(workflow_id)
        await handle.signal(signal_name, data)

    async def query(self, workflow_id: str, query_name: str) -> Any:
        """Query a running workflow."""
        handle = self._temporal.get_workflow_handle(workflow_id)
        return await handle.query(query_name)

    @property
    def temporal(self) -> TemporalClient:
        """Access the underlying Temporal client."""
        return self._temporal
