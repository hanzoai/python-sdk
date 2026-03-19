"""Pre-built workflows for agent task orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@dataclass
class AgentTaskInput:
    """Input for a single agent task."""

    space_id: str
    agent_id: str
    task_title: str
    task_prompt: str
    timeout_seconds: int = 3600
    max_retries: int = 3


@dataclass
class AgentTaskOutput:
    """Output from an agent task execution."""

    result: str = ""
    error: str = ""
    elapsed_seconds: float = 0.0


@workflow.defn
class AgentTaskWorkflow:
    """Execute a single agent task with retries and timeout."""

    @workflow.run
    async def run(self, input: AgentTaskInput) -> AgentTaskOutput:
        return await workflow.execute_activity(
            "execute_agent_task",
            input,
            start_to_close_timeout=timedelta(seconds=input.timeout_seconds),
            retry_policy=RetryPolicy(maximum_attempts=input.max_retries),
        )


@workflow.defn
class PipelineWorkflow:
    """Run agent tasks sequentially (pipeline)."""

    @workflow.run
    async def run(self, tasks: list[AgentTaskInput]) -> list[AgentTaskOutput]:
        results: list[AgentTaskOutput] = []
        for task in tasks:
            result = await workflow.execute_activity(
                "execute_agent_task",
                task,
                start_to_close_timeout=timedelta(seconds=task.timeout_seconds),
                retry_policy=RetryPolicy(maximum_attempts=task.max_retries),
            )
            results.append(result)
        return results


@workflow.defn
class FanOutWorkflow:
    """Run agent tasks in parallel (fan-out/fan-in)."""

    @workflow.run
    async def run(self, tasks: list[AgentTaskInput]) -> list[AgentTaskOutput]:
        handles = []
        for task in tasks:
            handle = workflow.start_activity(
                "execute_agent_task",
                task,
                start_to_close_timeout=timedelta(seconds=task.timeout_seconds),
                retry_policy=RetryPolicy(maximum_attempts=task.max_retries),
            )
            handles.append(handle)
        return [await h for h in handles]
