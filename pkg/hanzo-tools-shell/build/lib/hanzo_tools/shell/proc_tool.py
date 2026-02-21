"""Unified process tool for HIP-0300 architecture.

This module provides a single unified 'proc' tool that handles all process operations:
- exec: Execute commands (the ONE execution primitive)
- ps: List processes
- kill: Kill processes
- logs: Get process logs

Following Unix philosophy: one tool for the Execution axis.
All command execution goes through proc.exec.
"""

import os
import json
import signal
import asyncio
from typing import Any, Dict, ClassVar, Optional
from pathlib import Path
from datetime import datetime

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    Paging,
    BaseTool,
    ToolError,
    NotFoundError,
    InvalidParamsError,
)
from hanzo_tools.shell.base_process import (
    AUTO_BACKGROUND_TIMEOUT,
    ProcessManager,
    get_shell_executor,
)


class ProcTool(BaseTool):
    """Unified process execution tool (HIP-0300).

    Handles all process operations on a single axis:
    - exec: Execute commands
    - ps: List processes
    - kill: Kill processes
    - logs: Get process logs

    CRITICAL: exec is the ONE execution primitive.
    All command execution goes through proc.exec.
    """

    name: ClassVar[str] = "proc"
    VERSION: ClassVar[str] = "0.12.0"

    def __init__(self, tools: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.tools = tools or {}
        self.process_manager = ProcessManager()
        self._shell = self._resolve_shell()
        self._register_proc_actions()

    def _resolve_shell(self) -> str:
        """Resolve shell - prefer zsh, fallback to bash/sh."""
        import shutil

        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        for shell in ["zsh", "bash", "fish", "dash", "sh"]:
            for prefix in ["/opt/homebrew/bin", "/usr/local/bin", "/bin", "/usr/bin"]:
                full_path = f"{prefix}/{shell}"
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
            found = shutil.which(shell)
            if found:
                return found

        return "sh"

    @property
    def description(self) -> str:
        shell_name = os.path.basename(self._shell)
        return f"""Unified process execution tool (HIP-0300).

Actions:
- exec: Execute command (shell: {shell_name})
- ps: List processes
- kill: Kill process
- logs: Get process logs

Returns: {{proc_id, exit_code, stdout_ref, stderr_ref}}
Auto-backgrounds commands after {AUTO_BACKGROUND_TIMEOUT}s.
"""

    def _register_proc_actions(self):
        """Register all process actions."""

        @self.action("exec", "Execute command")
        async def exec_cmd(
            ctx: MCPContext,
            command: str,
            cwd: str | None = None,
            env: dict | None = None,
            timeout: int | None = None,
            shell: str | None = None,
        ) -> dict:
            """Execute a command.

            This is the ONE execution primitive per HIP-0300.

            Args:
                command: Command to execute
                cwd: Working directory
                env: Environment variables
                timeout: Timeout in seconds (default: auto-background at 45s)
                shell: Shell to use (default: detected shell)

            Returns:
                proc_id, exit_code, stdout_ref, stderr_ref
            """
            if not command:
                raise InvalidParamsError("Command is required", param="command")

            # Resolve shell
            shell_path = shell or self._shell

            # Build environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            # Get shell executor
            executor = get_shell_executor()

            try:
                # Execute with auto-background support
                result = await executor.execute(
                    command,
                    shell=shell_path,
                    cwd=cwd,
                    env=process_env,
                    timeout=timeout or AUTO_BACKGROUND_TIMEOUT,
                )

                # Check if backgrounded
                if result.get("backgrounded"):
                    proc_id = result.get("proc_id", "unknown")
                    return {
                        "proc_id": proc_id,
                        "exit_code": None,
                        "stdout_ref": f"proc:{proc_id}:stdout",
                        "stderr_ref": f"proc:{proc_id}:stderr",
                        "status": "running",
                        "message": f"Command backgrounded after {timeout or AUTO_BACKGROUND_TIMEOUT}s. Use proc(action='logs', proc_id='{proc_id}') to view output.",
                    }

                # Command completed
                exit_code = result.get("return_code", result.get("exit_code", 0))
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")

                return {
                    "proc_id": result.get("proc_id"),
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_ms": result.get("duration_ms"),
                    "status": "success" if exit_code == 0 else "failed",
                }

            except asyncio.TimeoutError:
                raise ToolError(
                    code="TIMEOUT",
                    message=f"Command timed out after {timeout}s",
                )
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Execution failed: {e}",
                )

        @self.action("ps", "List processes")
        async def ps(
            ctx: MCPContext,
            proc_id: str | None = None,
            filter: str | None = None,
        ) -> dict:
            """List tracked processes.

            Args:
                proc_id: Get specific process
                filter: Filter by command pattern

            Returns:
                List of processes with status
            """
            processes = []

            for pid, info in self.process_manager.list_processes().items():
                # Filter by proc_id
                if proc_id and pid != proc_id:
                    continue

                # Filter by command pattern
                cmd = info.get("cmd", "")
                if filter and filter.lower() not in cmd.lower():
                    continue

                processes.append(
                    {
                        "proc_id": pid,
                        "pid": info.get("pid"),
                        "command": cmd,
                        "running": info.get("running", False),
                        "exit_code": info.get("return_code"),
                        "started": info.get("started"),
                        "log_file": info.get("log_file"),
                    }
                )

            if proc_id and not processes:
                raise NotFoundError(f"Process not found: {proc_id}")

            return {
                "processes": processes,
                "total": len(processes),
            }

        @self.action("kill", "Kill process")
        async def kill(
            ctx: MCPContext,
            proc_id: str,
            signal: str | int = "TERM",
        ) -> dict:
            """Kill a process.

            Args:
                proc_id: Process ID to kill
                signal: Signal to send (default: TERM)

            Returns:
                Success status
            """
            if not proc_id:
                raise InvalidParamsError("proc_id is required", param="proc_id")

            # Find process
            procs = self.process_manager.list_processes()
            if proc_id not in procs:
                raise NotFoundError(f"Process not found: {proc_id}")

            info = procs[proc_id]
            pid = info.get("pid")

            if not pid:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message="Process has no PID",
                )

            # Resolve signal
            if isinstance(signal, str):
                signal_map = {
                    "TERM": 15,
                    "KILL": 9,
                    "INT": 2,
                    "HUP": 1,
                    "QUIT": 3,
                }
                sig_num = signal_map.get(signal.upper(), 15)
            else:
                sig_num = signal

            try:
                os.kill(pid, sig_num)
                return {
                    "proc_id": proc_id,
                    "pid": pid,
                    "signal": sig_num,
                    "killed": True,
                }
            except ProcessLookupError:
                return {
                    "proc_id": proc_id,
                    "pid": pid,
                    "signal": sig_num,
                    "killed": False,
                    "message": "Process already terminated",
                }
            except PermissionError:
                raise ToolError(
                    code="PERMISSION_DENIED",
                    message=f"Cannot kill process {pid}: permission denied",
                )

        @self.action("logs", "Get process logs")
        async def logs(
            ctx: MCPContext,
            proc_id: str,
            tail: int = 100,
            since: str | None = None,
        ) -> dict:
            """Get process stdout/stderr.

            Args:
                proc_id: Process ID
                tail: Number of lines (default: 100)
                since: ISO timestamp to filter from

            Returns:
                stdout and stderr content
            """
            if not proc_id:
                raise InvalidParamsError("proc_id is required", param="proc_id")

            procs = self.process_manager.list_processes()
            if proc_id not in procs:
                raise NotFoundError(f"Process not found: {proc_id}")

            info = procs[proc_id]
            log_file = info.get("log_file")

            if not log_file or not Path(log_file).exists():
                return {
                    "proc_id": proc_id,
                    "stdout": "",
                    "stderr": "",
                    "message": "No log file available",
                }

            try:
                from hanzo_async import read_file

                content = await read_file(log_file, encoding="utf-8", errors="replace")

                # Apply tail
                lines = content.splitlines()
                if tail and len(lines) > tail:
                    lines = lines[-tail:]

                return {
                    "proc_id": proc_id,
                    "output": "\n".join(lines),
                    "running": info.get("running", False),
                    "exit_code": info.get("return_code"),
                    "total_lines": len(content.splitlines()),
                }
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Failed to read logs: {e}",
                )

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'proc' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Backward compatibility
proc_tool = ProcTool
