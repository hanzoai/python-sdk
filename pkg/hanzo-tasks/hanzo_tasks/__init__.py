"""hanzo-tasks — durable activities on the native Hanzo Tasks engine.

The engine is Hanzo's own (`hanzoai/tasks`), reached over JSON at
``api.hanzo.ai/v1/tasks``. It speaks no protobuf and no gRPC, and this package
depends on no workflow runtime — dispatching work and running a worker are
both plain HTTP.

Dispatch a unit of work::

    from hanzo_tasks import Tasks

    async with Tasks.from_env() as tasks:
        activity = await tasks.dispatch("render", input={"scene": 3}, task_queue="gpu")

Run a worker that pulls it. The worker polls, so it needs no inbound address
and runs behind NAT::

    from hanzo_tasks import Tasks, Worker

    tasks = Tasks.from_env()
    worker = Worker(tasks, task_queue="gpu")

    @worker.handler("render")
    async def render(activity):
        return {"frames": 120}

    await worker.run()

The lease is held for you: the worker heartbeats while your handler runs, and
if it dies the engine returns the activity to the queue for somebody else.
"""

from .client import DEFAULT_NAMESPACE, DEFAULT_URL, Tasks
from .errors import Denied, NotFound, TasksError, Terminal
from .types import (
    CANCELED,
    COMPLETED,
    FAILED,
    SCHEDULED,
    STARTED,
    TERMINAL,
    Activity,
    Event,
    Page,
    RetryPolicy,
)
from .worker import Worker, default_identity

__version__ = "0.2.0"
__all__ = [
    # Client
    "Tasks",
    "DEFAULT_URL",
    "DEFAULT_NAMESPACE",
    # Worker
    "Worker",
    "default_identity",
    # Types
    "Activity",
    "Event",
    "Page",
    "RetryPolicy",
    # States
    "SCHEDULED",
    "STARTED",
    "COMPLETED",
    "FAILED",
    "CANCELED",
    "TERMINAL",
    # Errors
    "TasksError",
    "Denied",
    "NotFound",
    "Terminal",
]
