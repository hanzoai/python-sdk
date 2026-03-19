"""
hanzo-tasks — Durable workflow execution for AI agents.

Wraps the Temporal Python SDK with Hanzo conventions for agent task
orchestration, including pre-built workflows for pipelines and fan-out.

Example:
    >>> from hanzo_tasks import Client, TasksConfig
    >>> client = await Client.connect(TasksConfig(namespace="hanzo"))
    >>> handle = await client.submit(AgentTaskWorkflow.run, task_input, queue="agents")
    >>> result = await handle.result()
"""

from .activities import execute_agent_task, send_notification, set_agent_executor
from .client import Client, TasksConfig, WorkflowHandle
from .worker import Worker
from .workflows import (
    AgentTaskInput,
    AgentTaskOutput,
    AgentTaskWorkflow,
    FanOutWorkflow,
    PipelineWorkflow,
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "Client",
    "TasksConfig",
    "WorkflowHandle",
    # Worker
    "Worker",
    # Workflows
    "AgentTaskWorkflow",
    "PipelineWorkflow",
    "FanOutWorkflow",
    "AgentTaskInput",
    "AgentTaskOutput",
    # Activities
    "execute_agent_task",
    "send_notification",
    "set_agent_executor",
]
