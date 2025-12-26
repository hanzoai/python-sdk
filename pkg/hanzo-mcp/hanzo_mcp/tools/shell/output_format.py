"""Shell output formatting for Claude Code display.

Returns structured JSON with markdown-ready fields that Claude knows how to render.
"""

import os
import json
from typing import Optional


def format_shell_result(
    command: str,
    stdout: str,
    stderr: str = "",
    exit_code: int = 0,
    cwd: Optional[str] = None,
    was_backgrounded: bool = False,
    process_id: Optional[str] = None,
) -> str:
    """Format shell command result as structured JSON with markdown-ready fields.

    Args:
        command: The command that was executed
        stdout: Standard output from the command
        stderr: Standard error from the command
        exit_code: Exit code (0 = success)
        cwd: Working directory where command ran
        was_backgrounded: Whether the command was auto-backgrounded
        process_id: Process ID if backgrounded

    Returns:
        JSON string with summary, stdout_markdown, stderr_markdown, etc.
    """
    # Determine status
    if was_backgrounded:
        status = "backgrounded"
        summary = f"Command `{_truncate_cmd(command)}` backgrounded (process: {process_id})"
    elif exit_code == 0:
        status = "success"
        summary = _generate_summary(command, stdout, cwd)
    else:
        status = "error"
        summary = f"Command `{_truncate_cmd(command)}` failed with exit code {exit_code}"

    # Build result
    result = {
        "summary": summary,
        "stdout_markdown": _format_output_markdown(stdout) if stdout.strip() else "",
        "stderr_markdown": _format_output_markdown(stderr, is_stderr=True) if stderr.strip() else "",
        "status": status,
        "exit_code": exit_code,
        "command": command,
    }

    if cwd:
        result["cwd"] = cwd

    if was_backgrounded and process_id:
        result["process_id"] = process_id
        result["hint"] = f"Use `ps --logs {process_id}` to view output, `ps --kill {process_id}` to stop"

    return json.dumps(result, indent=2)


def _truncate_cmd(command: str, max_len: int = 50) -> str:
    """Truncate command for display."""
    if len(command) <= max_len:
        return command
    return command[: max_len - 3] + "..."


def _generate_summary(command: str, stdout: str, cwd: Optional[str] = None) -> str:
    """Generate a brief summary of command execution."""
    lines = stdout.strip().split("\n") if stdout.strip() else []
    line_count = len(lines)

    # Get first word of command for context
    cmd_name = command.split()[0] if command else "command"

    # Smart summaries based on command type
    if cmd_name in ("ls", "find", "tree"):
        return f"Listed {line_count} items" + (f" in {cwd}" if cwd else "")
    elif cmd_name == "git":
        subcmd = command.split()[1] if len(command.split()) > 1 else ""
        if subcmd == "status":
            return f"Git status: {line_count} lines of output"
        elif subcmd == "log":
            return f"Git log: {line_count} lines"
        elif subcmd in ("commit", "push", "pull"):
            return f"Git {subcmd} completed"
        return f"Git command completed ({line_count} lines)"
    elif cmd_name in ("npm", "pnpm", "yarn"):
        return f"Package manager completed ({line_count} lines)"
    elif cmd_name in ("make", "cargo", "go"):
        return f"Build command completed ({line_count} lines)"
    elif cmd_name == "cat":
        return f"File contents ({line_count} lines)"
    elif cmd_name == "echo":
        return f"Output: {stdout.strip()[:100]}"

    # Default summary
    if line_count == 0:
        return f"Command `{_truncate_cmd(cmd_name)}` completed (no output)"
    elif line_count == 1:
        return f"Output: {stdout.strip()[:100]}"
    else:
        return f"Command completed with {line_count} lines of output"


def _format_output_markdown(output: str, is_stderr: bool = False) -> str:
    """Format output as markdown code block."""
    if not output.strip():
        return ""

    # Detect language hint based on content
    lang = ""
    stripped = output.strip()

    # Common output patterns
    if stripped.startswith("{") or stripped.startswith("["):
        lang = "json"
    elif "error:" in stripped.lower() or "warning:" in stripped.lower():
        lang = "text"
    elif stripped.startswith("diff ") or stripped.startswith("---"):
        lang = "diff"

    prefix = "[stderr]\n" if is_stderr else ""
    return f"{prefix}```{lang}\n{output.rstrip()}\n```"


def format_plain_output(stdout: str, stderr: str = "", exit_code: int = 0) -> str:
    """Format output as plain text (for backward compatibility).

    Args:
        stdout: Standard output
        stderr: Standard error
        exit_code: Exit code

    Returns:
        Plain text output
    """
    parts = []

    if stdout.strip():
        parts.append(stdout.rstrip())

    if stderr.strip():
        parts.append(f"[stderr]\n{stderr.rstrip()}")

    if exit_code != 0:
        parts.append(f"\n[exit code: {exit_code}]")

    return "\n".join(parts) if parts else "(no output)"
