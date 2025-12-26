"""Process management tool (ps).

List, monitor, and control background processes.
Clean UNIX-style API.
"""

import signal
import asyncio
from typing import Optional, List, Dict, Any, Annotated, override
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiofiles
from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.shell.base_process import ProcessManager
from hanzo_mcp.tools.common.auto_timeout import auto_timeout


@dataclass
class ProcessInfo:
    """Process information."""
    id: str
    pid: int
    cmd: str
    running: bool
    exit_code: Optional[int] = None
    started: Optional[datetime] = None
    log_file: Optional[Path] = None


class PsTool(BaseTool):
    """Process management - list, kill, logs.
    
    USAGE:
    
    ps()                  # List all processes
    ps(id="abc123")       # Get specific process info
    ps(kill="abc123")     # Kill process (SIGTERM)
    ps(kill="abc123", signal="KILL")  # Kill with SIGKILL
    ps(logs="abc123")     # Get process logs
    ps(logs="abc123", n=50)  # Last 50 lines
    """
    
    _instance: Optional["PsTool"] = None
    _process_manager: Optional[ProcessManager] = None
    
    def __new__(cls):
        """Singleton - share process manager across instances."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._process_manager = ProcessManager()
        return cls._instance
    
    def __init__(self):
        super().__init__()
        self.process_manager = self._process_manager

    @property
    @override
    def name(self) -> str:
        return "ps"

    @property
    @override
    def description(self) -> str:
        return """Process management - list, kill, and read logs.

USAGE:
  ps                    List all background processes
  ps --id ID            Get specific process info
  ps --kill ID          Kill process (SIGTERM)
  ps --kill ID --sig 9  Kill with specific signal
  ps --logs ID          Get process stdout/stderr
  ps --logs ID --n 50   Last N lines of logs"""

    def _list_processes(self) -> List[ProcessInfo]:
        """Get all tracked processes."""
        processes = []
        for proc_id, info in self.process_manager.list_processes().items():
            processes.append(ProcessInfo(
                id=proc_id,
                pid=info.get("pid", 0),
                cmd=info.get("cmd", ""),
                running=info.get("running", False),
                exit_code=info.get("return_code"),
                log_file=Path(info["log_file"]) if info.get("log_file") else None,
            ))
        return processes

    def _get_process(self, proc_id: str) -> Optional[ProcessInfo]:
        """Get specific process info."""
        for p in self._list_processes():
            if p.id == proc_id or str(p.pid) == proc_id:
                return p
        return None

    async def _kill_process(self, proc_id: str, sig: int = signal.SIGTERM) -> str:
        """Kill a process."""
        process = self.process_manager.get_process(proc_id)
        if not process:
            return f"Process not found: {proc_id}"
        
        try:
            process.send_signal(sig)
            sig_name = signal.Signals(sig).name
            return f"Sent {sig_name} to {proc_id} (PID {process.pid})"
        except ProcessLookupError:
            return f"Process {proc_id} already terminated"
        except Exception as e:
            return f"Failed to kill {proc_id}: {e}"

    async def _get_logs(self, proc_id: str, n: int = 100) -> str:
        """Get process logs."""
        log_file = self.process_manager.get_log_file(proc_id)
        if not log_file or not log_file.exists():
            return f"No logs for process: {proc_id}"
        
        try:
            async with aiofiles.open(log_file, "r") as f:
                content = await f.read()
                lines = content.splitlines()
                
            if len(lines) > n:
                lines = lines[-n:]
            
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading logs: {e}"

    def _format_list(self, processes: List[ProcessInfo]) -> str:
        """Format process list for display."""
        if not processes:
            return "No background processes"
        
        lines = ["PID     ID              STATUS    CMD"]
        lines.append("-" * 60)
        
        for p in processes:
            status = "running" if p.running else f"exit({p.exit_code})"
            cmd = p.cmd[:30] + "..." if len(p.cmd) > 30 else p.cmd
            lines.append(f"{p.pid:<7} {p.id:<15} {status:<9} {cmd}")
        
        return "\n".join(lines)

    @override
    @auto_timeout("ps")
    async def call(
        self,
        ctx: MCPContext,
        id: Optional[str] = None,
        kill: Optional[str] = None,
        logs: Optional[str] = None,
        sig: int = 15,  # SIGTERM
        n: int = 100,
        **kwargs,
    ) -> str:
        """Process management.
        
        Args:
            ctx: MCP context
            id: Get specific process info
            kill: Kill process by ID
            logs: Get logs for process
            sig: Signal number for kill (default: 15/SIGTERM)
            n: Number of log lines to show
            
        Returns:
            Process information or action result
        """
        # Kill action
        if kill:
            return await self._kill_process(kill, sig)
        
        # Logs action
        if logs:
            return await self._get_logs(logs, n)
        
        # Get specific process
        if id:
            proc = self._get_process(id)
            if not proc:
                return f"Process not found: {id}"
            status = "running" if proc.running else f"exited ({proc.exit_code})"
            return f"ID: {proc.id}\nPID: {proc.pid}\nStatus: {status}\nCommand: {proc.cmd}"
        
        # Default: list all
        return self._format_list(self._list_processes())

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register ps tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def ps_handler(
            id: Annotated[
                Optional[str],
                Field(description="Get specific process by ID", default=None)
            ] = None,
            kill: Annotated[
                Optional[str],
                Field(description="Kill process by ID", default=None)
            ] = None,
            logs: Annotated[
                Optional[str],
                Field(description="Get logs for process ID", default=None)
            ] = None,
            sig: Annotated[
                int,
                Field(description="Signal for kill (default: 15/SIGTERM)", default=15)
            ] = 15,
            n: Annotated[
                int,
                Field(description="Number of log lines", default=100)
            ] = 100,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(ctx, id=id, kill=kill, logs=logs, sig=sig, n=n)


# Singleton instance
ps_tool = PsTool()
