"""Backward-compatible batch tool implementation.

This module restores ``hanzo_mcp.tools.common.batch_tool.BatchTool`` for
existing callers and tests that still import it directly.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class _BatchResult:
    index: int
    tool_name: str
    output: str


class BatchTool:
    """Execute multiple tool invocations concurrently.

    The current server uses entry-point tools, but legacy code still imports
    this class directly. Keep behavior simple and deterministic:
    - preserves invocation order in output
    - executes in parallel with a concurrency cap
    - always returns a human-readable string
    """

    name = "batch"
    description = "Run multiple tools in parallel"

    def __init__(self, tools: dict[str, Any], max_concurrency: int = 8):
        self.tools = tools
        self.max_concurrency = max(1, max_concurrency)

    async def call(
        self,
        ctx: Any,
        description: str,
        invocations: list[dict[str, Any]],
        max_concurrency: int | None = None,
        **_: Any,
    ) -> str:
        if not invocations:
            return "Error: invocations cannot be empty"

        semaphore = asyncio.Semaphore(max_concurrency or self.max_concurrency)

        async def _run(index: int, invocation: dict[str, Any]) -> _BatchResult:
            tool_name = str(invocation.get("tool_name", "")).strip()
            payload = invocation.get("input", {})

            if not isinstance(payload, dict):
                payload = {} if payload is None else {"input": payload}

            if not tool_name:
                return _BatchResult(index, "<missing>", "Error: tool_name is required")

            tool = self.tools.get(tool_name)
            if tool is None:
                return _BatchResult(
                    index, tool_name, f"Error: Tool '{tool_name}' not found"
                )

            async with semaphore:
                try:
                    # Support both call(ctx, **kwargs) and call(ctx=ctx, **kwargs).
                    try:
                        result = await tool.call(ctx=ctx, **payload)
                    except TypeError:
                        result = await tool.call(ctx, **payload)
                except Exception as exc:  # noqa: BLE001 - tool errors should be captured
                    return _BatchResult(index, tool_name, f"Error: {exc}")

            return _BatchResult(index, tool_name, str(result))

        tasks = [
            _run(i, invocation) for i, invocation in enumerate(invocations, start=1)
        ]
        results = await asyncio.gather(*tasks)
        results.sort(key=lambda item: item.index)

        lines = [f"Batch: {description}", "results:"]
        for item in results:
            lines.append(f"Result {item.index}: {item.tool_name}")
            lines.append(item.output)

        return "\n".join(lines)
