"""Hanzo Tasks worker — polls and executes activities."""

from __future__ import annotations

from typing import Any

from temporalio.worker import Worker as TemporalWorker


class Worker:
    """Hanzo Tasks worker that polls a queue and executes workflows/activities."""

    def __init__(
        self,
        client: Any,
        queue: str = "default",
        workflows: list[Any] | None = None,
        activities: list[Any] | None = None,
    ) -> None:
        self._client = client
        self._queue = queue
        self._workflows: list[Any] = workflows or []
        self._activities: list[Any] = activities or []
        self._worker: TemporalWorker | None = None

    def register_workflow(self, workflow_cls: Any) -> Any:
        """Register a workflow class. Can be used as a decorator."""
        self._workflows.append(workflow_cls)
        return workflow_cls

    def register_activity(self, activity_fn: Any) -> Any:
        """Register an activity function. Can be used as a decorator."""
        self._activities.append(activity_fn)
        return activity_fn

    async def run(self) -> None:
        """Start the worker. Blocks until shutdown."""
        temporal_client = (
            self._client.temporal
            if hasattr(self._client, "temporal")
            else self._client
        )
        self._worker = TemporalWorker(
            temporal_client,
            task_queue=self._queue,
            workflows=self._workflows,
            activities=self._activities,
        )
        await self._worker.run()

    async def shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        if self._worker:
            await self._worker.shutdown()
