"""Activity definitions for agent task execution."""

from __future__ import annotations

from typing import Any, Callable

from temporalio import activity

# Activity executor — pluggable. The playground sets this to call the ZAP sidecar.
_agent_executor: Callable[..., Any] | None = None


def set_agent_executor(fn: Callable[..., Any]) -> None:
    """Set the function that executes agent tasks (called by playground)."""
    global _agent_executor
    _agent_executor = fn


@activity.defn
async def execute_agent_task(input: Any) -> Any:
    """Execute an agent task. Delegates to the registered executor."""
    if _agent_executor is None:
        raise RuntimeError(
            "No agent executor registered. Call set_agent_executor() first."
        )
    return await _agent_executor(input)


@activity.defn
async def send_notification(input: dict[str, Any]) -> None:
    """Send a notification (webhook, SSE, etc)."""
    import httpx

    async with httpx.AsyncClient() as client:
        await client.post(input.get("url", ""), json=input)
