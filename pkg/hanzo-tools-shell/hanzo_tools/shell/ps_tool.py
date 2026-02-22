"""Process management tool (ps).

List, monitor, and control background processes system-wide.
"""

import sys
import signal
from typing import Any, Dict, List, Literal, Optional, Annotated, override
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

import psutil
from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout


@dataclass
class ProcessInfo:
    """Process information."""

    pid: int
    name: str
    username: str
    status: str
    cpu_percent: float
    memory_mb: float
    cmdline: str
    create_time: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pid": self.pid,
            "name": self.name,
            "username": self.username,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "cmdline": self.cmdline,
            "create_time": self.create_time.isoformat(),
        }


class PsTool(BaseTool):
    """Process management - list, kill, and monitor system processes.

    USAGE:

    ps(action="list")                     # List all processes (top by CPU)
    ps(action="list", sort_by="memory")   # List all processes (top by RAM)
    ps(action="list", user="root")        # List processes for user
    ps(action="kill", pid=1234)           # Kill process 1234 (SIGTERM)
    ps(action="kill", pid=1234, sig=9)    # Kill with SIGKILL
    ps(action="get", pid=1234)            # Get info for specific PID
    """

    name = "ps"

    @property
    @override
    def description(self) -> str:
        return """Process management - list, kill, and monitor system processes.

USAGE:
  ps(action="list")                     # List top processes by CPU
  ps(action="list", sort_by="memory")   # List top processes by Memory
  ps(action="list", limit=20)           # List top 20 processes
  ps(action="get", pid=1234)            # Get info for process 1234
  ps(action="kill", pid=1234)           # Kill process 1234 (SIGTERM)
"""

    def _get_process_info(self, proc: psutil.Process) -> Optional[ProcessInfo]:
        """Get process info safely."""
        try:
            with proc.oneshot():
                return ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    username=proc.username(),
                    status=proc.status(),
                    cpu_percent=proc.cpu_percent(),
                    memory_mb=proc.memory_info().rss / 1024 / 1024,
                    cmdline=" ".join(proc.cmdline()),
                    create_time=datetime.fromtimestamp(proc.create_time()),
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def _list_processes(
        self,
        sort_by: Literal["cpu", "memory", "pid", "name"] = "cpu",
        limit: int = 50,
        user: Optional[str] = None,
    ) -> List[ProcessInfo]:
        """List system processes."""
        processes = []
        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "username",
                "status",
                "cpu_percent",
                "memory_info",
                "cmdline",
                "create_time",
            ]
        ):
            try:
                # Filter by user if requested
                if user and proc.info["username"] != user:
                    continue

                info = ProcessInfo(
                    pid=proc.info["pid"],
                    name=proc.info["name"] or "",
                    username=proc.info["username"] or "",
                    status=proc.info["status"] or "",
                    cpu_percent=proc.info["cpu_percent"] or 0.0,
                    memory_mb=(
                        (proc.info["memory_info"].rss / 1024 / 1024)
                        if proc.info["memory_info"]
                        else 0.0
                    ),
                    cmdline=" ".join(proc.info["cmdline"] or []),
                    create_time=datetime.fromtimestamp(proc.info["create_time"]),
                )
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort
        if sort_by == "cpu":
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x.memory_mb, reverse=True)
        elif sort_by == "pid":
            processes.sort(key=lambda x: x.pid)
        elif sort_by == "name":
            processes.sort(key=lambda x: x.name.lower())

        return processes[:limit]

    def _kill_process(self, pid: int, sig: int = signal.SIGTERM) -> str:
        """Kill a process."""
        try:
            process = psutil.Process(pid)
            process.send_signal(sig)

            try:
                sig_name = signal.Signals(sig).name
            except Exception:
                sig_name = str(sig)

            return f"Sent signal {sig_name} to PID {pid} ({process.name()})"
        except psutil.NoSuchProcess:
            return f"Process with PID {pid} not found"
        except psutil.AccessDenied:
            return f"Access denied to kill PID {pid}"
        except Exception as e:
            return f"Error killing PID {pid}: {e}"

    def _format_list(self, processes: List[ProcessInfo]) -> str:
        """Format process list for display."""
        if not processes:
            return "No processes found"

        # Headers
        header = f"{'PID':<8} {'USER':<15} {'%CPU':<6} {'MEM(MB)':<10} {'STATUS':<10} {'COMMAND'}"
        lines = [header, "-" * len(header)]

        for p in processes:
            cmd = p.cmdline
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."

            line = f"{p.pid:<8} {p.username[:14]:<15} {p.cpu_percent:<6.1f} {p.memory_mb:<10.1f} {p.status[:9]:<10} {cmd}"
            lines.append(line)

        return "\n".join(lines)

    @override
    @auto_timeout("ps")
    async def call(
        self,
        ctx: MCPContext,
        action: Literal["list", "kill", "get"] = "list",
        pid: Optional[int] = None,
        sig: int = 15,
        sort_by: Literal["cpu", "memory", "pid", "name"] = "cpu",
        limit: int = 50,
        user: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Process management.

        Args:
            ctx: MCP context
            action: Action to perform (list, kill, get)
            pid: Process ID for kill/get
            sig: Signal number for kill (default: 15/SIGTERM)
            sort_by: Sort field for list (cpu, memory, pid, name)
            limit: Limit number of results for list (default: 50)
            user: Filter by username
        """
        if action == "kill":
            if pid is None:
                return "Error: pid is required for kill action"
            return self._kill_process(pid, sig)

        elif action == "get":
            if pid is None:
                return "Error: pid is required for get action"
            try:
                proc = psutil.Process(pid)
                info = self._get_process_info(proc)
                if not info:
                    return f"Process {pid} not found or access denied"

                return (
                    f"PID: {info.pid}\n"
                    f"Name: {info.name}\n"
                    f"User: {info.username}\n"
                    f"Status: {info.status}\n"
                    f"CPU: {info.cpu_percent}%\n"
                    f"Memory: {info.memory_mb:.1f} MB\n"
                    f"Created: {info.create_time}\n"
                    f"Command: {info.cmdline}"
                )
            except psutil.NoSuchProcess:
                return f"Process {pid} not found"

        else:  # list
            processes = self._list_processes(sort_by, limit, user)
            return self._format_list(processes)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register ps tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def ps(
            action: Annotated[
                Literal["list", "kill", "get"],
                Field(description="Action to perform", default="list"),
            ] = "list",
            pid: Annotated[
                Optional[int],
                Field(description="Process ID for kill/get", default=None),
            ] = None,
            sig: Annotated[
                int,
                Field(description="Signal for kill (default: 15/SIGTERM)", default=15),
            ] = 15,
            sort_by: Annotated[
                Literal["cpu", "memory", "pid", "name"],
                Field(description="Sort field for list", default="cpu"),
            ] = "cpu",
            limit: Annotated[
                int, Field(description="Number of processes to list", default=50)
            ] = 50,
            user: Annotated[
                Optional[str], Field(description="Filter by username", default=None)
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                pid=pid,
                sig=sig,
                sort_by=sort_by,
                limit=limit,
                user=user,
            )


# Singleton instance
ps_tool = PsTool()
