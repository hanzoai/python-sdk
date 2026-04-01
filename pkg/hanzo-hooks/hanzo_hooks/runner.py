"""HookRunner: execute shell commands around tool invocations."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from .types import HookConfig, HookEvent, HookRunResult


class HookRunner:
    __slots__ = ("_config",)

    def __init__(self, config: HookConfig) -> None:
        self._config = config

    @classmethod
    def from_settings(cls, path: str) -> HookRunner:
        return cls(HookConfig.from_json(path))

    def run_pre_tool_use(self, tool_name: str, tool_input: str) -> HookRunResult:
        return self._run_commands(
            HookEvent.PreToolUse, self._config.pre_tool_use, tool_name, tool_input,
        )

    def run_post_tool_use(
        self, tool_name: str, tool_input: str, tool_output: str, is_error: bool = False,
    ) -> HookRunResult:
        return self._run_commands(
            HookEvent.PostToolUse, self._config.post_tool_use,
            tool_name, tool_input, tool_output=tool_output, is_error=is_error,
        )

    def _run_commands(
        self, event: HookEvent, commands: list[str], tool_name: str, tool_input: str,
        tool_output: str | None = None, is_error: bool = False,
    ) -> HookRunResult:
        if not commands:
            return HookRunResult.allow()

        try:
            parsed_input = json.loads(tool_input)
        except (json.JSONDecodeError, TypeError):
            parsed_input = {"raw": tool_input}

        payload = json.dumps({
            "hook_event_name": event.value, "tool_name": tool_name,
            "tool_input": parsed_input, "tool_input_json": tool_input,
            "tool_output": tool_output, "tool_result_is_error": is_error,
        })
        env = {
            "HOOK_EVENT": event.value, "HOOK_TOOL_NAME": tool_name,
            "HOOK_TOOL_INPUT": tool_input, "HOOK_TOOL_IS_ERROR": "1" if is_error else "0",
        }
        if tool_output is not None:
            env["HOOK_TOOL_OUTPUT"] = tool_output

        messages: list[str] = []
        for command in commands:
            kind, msg = _run_one(command, event, tool_name, env, payload)
            if kind == "allow":
                if msg:
                    messages.append(msg)
            elif kind == "deny":
                messages.append(msg or f"{event.value} hook denied tool `{tool_name}`")
                return HookRunResult(denied=True, messages=messages)
            else:
                messages.append(msg)
        return HookRunResult.allow(messages)


def _run_one(
    command: str, event: HookEvent, tool_name: str,
    env: dict[str, str], payload: str,
) -> tuple[str, str]:
    """Returns (outcome_type, message). outcome_type: allow/deny/warn."""
    args = ["cmd", "/C", command] if sys.platform == "win32" else ["sh", "-lc", command]
    try:
        proc = subprocess.run(
            args, input=payload, capture_output=True, text=True,
            env={**os.environ, **env},
        )
    except OSError as exc:
        return ("warn", f"{event.value} hook `{command}` failed to start for `{tool_name}`: {exc}")

    stdout, stderr = proc.stdout.strip(), proc.stderr.strip()
    if proc.returncode == 0:
        return ("allow", stdout)
    if proc.returncode == 2:
        return ("deny", stdout)
    msg = f"Hook `{command}` exited with status {proc.returncode}; allowing tool execution to continue"
    if stdout:
        msg += f": {stdout}"
    elif stderr:
        msg += f": {stderr}"
    return ("warn", msg)
