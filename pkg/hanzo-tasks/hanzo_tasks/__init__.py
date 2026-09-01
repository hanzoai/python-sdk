"""hanzo-tasks — the Hanzo Tasks client.

Durable workflows in Hanzo Cloud run on hanzoai/tasks, embedded in the cloud
process and served under `/v1/tasks`. From Python you start, signal, query,
cancel, terminate and reset them, and manage schedules; a workflow's body runs
in a worker written with the Go (`tasks/pkg/sdk`) or TypeScript
(`@hanzoai/tasks`) SDK.

    >>> from hanzo_tasks import Client, TasksConfig
    >>> with Client(TasksConfig(token=TOKEN, namespace="acme")) as tasks:
    ...     wf = tasks.start("agent.review", task_queue="agents", input={"repo": "acme/widgets"})
    ...     tasks.signal(wf.workflow_id, "approve", {"by": "z"})
"""

from .client import DEFAULT_HOST, Client, TasksConfig, TasksError, Workflow

__version__ = "0.2.0"
__all__ = ["Client", "TasksConfig", "TasksError", "Workflow", "DEFAULT_HOST"]
