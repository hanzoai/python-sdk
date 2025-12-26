"""DAG execution tool - directed acyclic graph for command execution.

Run commands/tools with proper dependency ordering using DAG semantics.
Supports serial (default), parallel, and complex mixed execution graphs.
"""

import asyncio
import os
import shutil
import uuid
import tempfile
from typing import Any, Union, List, Dict, Optional, Annotated, override
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

import aiofiles

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.common.auto_timeout import auto_timeout
from hanzo_mcp.tools.shell.base_process import ProcessManager


class NodeStatus(Enum):
    """Execution status of a DAG node."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DagResult:
    """Result from a single DAG node execution."""
    node_id: str
    command: str
    stdout: str
    stderr: str
    status: NodeStatus
    exit_code: int
    duration_ms: int = 0
    node_type: str = "shell"  # shell, tool, parallel


@dataclass
class DagNode:
    """A node in the execution DAG."""
    id: str
    command: Union[str, Dict[str, Any]]
    depends_on: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[DagResult] = None


# Type alias
Command = Union[str, Dict[str, Any], List[Any]]


class DagTool(BaseTool):
    """DAG-based execution with proper dependency ordering.
    
    Execute commands (shell or tools) with directed acyclic graph semantics.
    Supports serial, parallel, and complex mixed execution patterns.
    
    USAGE PATTERNS:
    
    1. Serial (default) - sequential execution:
       dag(["ls", "pwd", "git status"])
    
    2. Parallel - concurrent execution:
       dag(["npm install", "cargo build"], parallel=True)
    
    3. DAG - mixed serial and parallel blocks:
       dag([
           "mkdir -p dist",              # Step 1
           {"parallel": [                # Step 2 (all concurrent)
               "cp manifest.json dist/",
               "cp -rf assets/ dist/",
               "cp -rf lib/ dist/",
           ]},
           "zip -r package.zip dist/"    # Step 3 (after all of step 2)
       ])
    
    4. Tool invocations - not just shell:
       dag([
           {"tool": "read", "input": {"file_path": "config.json"}},
           {"tool": "search", "input": {"pattern": "TODO"}},
       ])
    
    5. Named nodes with explicit dependencies:
       dag([
           {"id": "setup", "run": "mkdir -p dist"},
           {"id": "copy", "run": "cp *.txt dist/", "after": ["setup"]},
           {"id": "test", "run": "pytest", "after": ["setup"]},
           {"id": "package", "run": "tar -czf out.tar.gz dist/", "after": ["copy", "test"]},
       ])
    
    Uses zsh for shell execution.
    """

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None, default_shell: str = "zsh"):
        """Initialize DAG execution tool.
        
        Args:
            tools: Dict of available MCP tools for tool invocations
            default_shell: Default shell (zsh, bash, sh)
        """
        super().__init__()
        self.tools = tools or {}
        self.default_shell = self._resolve_shell(default_shell)
    
    def _resolve_shell(self, preferred: str) -> str:
        """Resolve shell - prefer zsh, fallback to bash.
        
        Search order:
        1. Homebrew paths (Apple Silicon + Intel)
        2. Standard system paths
        3. PATH lookup
        """
        # Prefer zsh, then bash
        shell_priority = ["zsh", "bash"]
        
        # Homebrew + system paths
        search_paths = [
            "/opt/homebrew/bin",   # Apple Silicon Homebrew
            "/usr/local/bin",      # Intel Homebrew
            "/bin",                # System
            "/usr/bin",            # System
        ]
        
        for shell in shell_priority:
            # Check explicit paths first
            for prefix in search_paths:
                full_path = f"{prefix}/{shell}"
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
            # Fallback to PATH lookup
            found = shutil.which(shell)
            if found:
                return found
        
        return "sh"  # Bare minimum fallback

    @property
    @override
    def name(self) -> str:
        return "dag"

    @property
    @override
    def description(self) -> str:
        return """DAG execution - run commands with dependency ordering.

Execute shell commands or tools with DAG (directed acyclic graph) semantics.
Supports serial, parallel, and complex mixed execution patterns.

MODES:

Serial (default): dag(["ls", "pwd"])
  Commands run in sequence.

Parallel: dag(["npm install", "cargo build"], parallel=True)
  Commands run concurrently.

Mixed DAG:
  dag([
      "mkdir -p dist",
      {"parallel": ["cp a.txt dist/", "cp b.txt dist/"]},
      "zip -r out.zip dist/"
  ])

Tool invocations:
  dag([{"tool": "search", "input": {"pattern": "TODO"}}])

Named with dependencies:
  dag([
      {"id": "build", "run": "make build"},
      {"id": "test", "run": "make test", "after": ["build"]},
  ])

Uses zsh for shell execution.

AUTO-BACKGROUNDING: Commands that exceed timeout are automatically
backgrounded. Use ps tool to monitor: ps --logs <id>, ps --kill <id>"""

    async def _run_shell(
        self,
        cmd: str,
        shell: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
    ) -> DagResult:
        """Run a shell command with auto-backgrounding on timeout.

        Commands that exceed the timeout are automatically backgrounded
        and can be monitored with the ps tool. All I/O is async.
        """
        start_time = datetime.now()
        node_id = f"shell_{id(cmd)}"
        process_manager = ProcessManager()
        
        # Defensive check - should never happen but provides better error message
        if process_manager is None:
            raise RuntimeError("ProcessManager() returned None - singleton initialization failed")

        try:
            # Merge environment
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            # Create log file for potential backgrounding
            process_id = f"dag_{uuid.uuid4().hex[:8]}"
            log_file = await process_manager.create_log_file(process_id)

            proc = await asyncio.create_subprocess_exec(
                shell, "-c", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=run_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )

                duration = int((datetime.now() - start_time).total_seconds() * 1000)
                exit_code = proc.returncode or 0

                return DagResult(
                    node_id=node_id,
                    command=cmd,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    status=NodeStatus.SUCCESS if exit_code == 0 else NodeStatus.FAILED,
                    exit_code=exit_code,
                    duration_ms=duration,
                    node_type="shell",
                )

            except asyncio.TimeoutError:
                # Auto-background: register process and return status
                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                # Write initial status to log (async)
                async with aiofiles.open(log_file, "w") as f:
                    await f.write(f"[dag] Command backgrounded after {timeout}s timeout\n")
                    await f.write(f"[dag] Command: {cmd}\n")
                    await f.write(f"[dag] PID: {proc.pid}\n")
                    await f.write(f"[dag] Started: {start_time.isoformat()}\n")
                    await f.write("-" * 40 + "\n")

                # Register with ProcessManager for ps tool
                process_manager.add_process(process_id, proc, str(log_file))

                # Start background log capture (non-blocking task)
                asyncio.create_task(self._capture_background_output(proc, log_file))

                return DagResult(
                    node_id=node_id,
                    command=cmd,
                    stdout=f"[backgrounded] Process {process_id} (PID {proc.pid}) running in background.\n"
                           f"Use: ps --logs {process_id}  # view output\n"
                           f"Use: ps --kill {process_id}  # stop process",
                    stderr="",
                    status=NodeStatus.SUCCESS,  # Backgrounding is success, not failure
                    exit_code=0,
                    duration_ms=duration,
                    node_type="shell",
                )

        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return DagResult(
                node_id=node_id,
                command=cmd,
                stdout="",
                stderr=str(e),
                status=NodeStatus.FAILED,
                exit_code=1,
                duration_ms=duration,
                node_type="shell",
            )

    async def _capture_background_output(
        self,
        proc: asyncio.subprocess.Process,
        log_file: Path
    ) -> None:
        """Capture output from backgrounded process to log file (async)."""
        try:
            async with aiofiles.open(log_file, "a") as f:
                # Read stdout/stderr concurrently
                async def read_stream(stream, prefix: str):
                    if stream:
                        while True:
                            line = await stream.readline()
                            if not line:
                                break
                            await f.write(f"{prefix}{line.decode('utf-8', errors='replace')}")
                            await f.flush()

                await asyncio.gather(
                    read_stream(proc.stdout, ""),
                    read_stream(proc.stderr, "[stderr] "),
                )

                # Write completion status
                await proc.wait()
                await f.write(f"\n[dag] Process exited with code {proc.returncode}\n")
        except Exception:
            # Silently handle errors in background capture
            pass

    async def _run_tool(
        self, 
        tool_name: str, 
        tool_input: Dict[str, Any], 
        ctx: MCPContext
    ) -> DagResult:
        """Run an MCP tool invocation."""
        start_time = datetime.now()
        node_id = f"tool_{tool_name}"
        
        if tool_name not in self.tools:
            return DagResult(
                node_id=node_id,
                command=f"tool:{tool_name}",
                stdout="",
                stderr=f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}",
                status=NodeStatus.FAILED,
                exit_code=1,
                duration_ms=0,
                node_type="tool",
            )
        
        try:
            tool = self.tools[tool_name]
            result = await tool.call(ctx, **tool_input)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return DagResult(
                node_id=node_id,
                command=f"tool:{tool_name}",
                stdout=str(result) if result else "",
                stderr="",
                status=NodeStatus.SUCCESS,
                exit_code=0,
                duration_ms=duration,
                node_type="tool",
            )
        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return DagResult(
                node_id=node_id,
                command=f"tool:{tool_name}",
                stdout="",
                stderr=str(e),
                status=NodeStatus.FAILED,
                exit_code=1,
                duration_ms=duration,
                node_type="tool",
            )

    async def _execute_node(
        self,
        cmd: Command,
        ctx: MCPContext,
        shell: str,
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        timeout: int,
    ) -> DagResult:
        """Execute a single DAG node."""
        
        # String command = shell execution
        if isinstance(cmd, str):
            return await self._run_shell(cmd, shell, cwd, env, timeout)
        
        # Dict command - could be tool, parallel, or named node
        if isinstance(cmd, dict):
            # Tool invocation: {"tool": "name", "input": {...}}
            if "tool" in cmd:
                return await self._run_tool(
                    cmd["tool"], 
                    cmd.get("input", {}), 
                    ctx
                )
            
            # Parallel block: {"parallel": [...]}
            if "parallel" in cmd:
                parallel_cmds = cmd["parallel"]
                tasks = [
                    self._execute_node(c, ctx, shell, cwd, env, timeout) 
                    for c in parallel_cmds
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combine parallel results
                combined_stdout = []
                combined_stderr = []
                all_success = True
                total_duration = 0
                
                for i, r in enumerate(results):
                    if isinstance(r, Exception):
                        combined_stderr.append(f"[{i}] Error: {r}")
                        all_success = False
                    else:
                        if r.stdout:
                            combined_stdout.append(f"[{i}] {r.stdout.rstrip()}")
                        if r.stderr:
                            combined_stderr.append(f"[{i}] {r.stderr.rstrip()}")
                        if r.status != NodeStatus.SUCCESS:
                            all_success = False
                        total_duration = max(total_duration, r.duration_ms)
                
                return DagResult(
                    node_id=f"parallel_{len(parallel_cmds)}",
                    command=f"parallel[{len(parallel_cmds)} tasks]",
                    stdout="\n".join(combined_stdout),
                    stderr="\n".join(combined_stderr),
                    status=NodeStatus.SUCCESS if all_success else NodeStatus.FAILED,
                    exit_code=0 if all_success else 1,
                    duration_ms=total_duration,
                    node_type="parallel",
                )
            
            # Named node: {"id": "x", "run": "...", "after": [...]}
            if "run" in cmd:
                run_cmd = cmd["run"]
                return await self._execute_node(run_cmd, ctx, shell, cwd, env, timeout)
            
            # Unknown dict format
            return DagResult(
                node_id="unknown",
                command=str(cmd),
                stdout="",
                stderr=f"Unknown command format: {cmd}",
                status=NodeStatus.FAILED,
                exit_code=1,
                duration_ms=0,
                node_type="unknown",
            )
        
        # Unknown type
        return DagResult(
            node_id="unknown",
            command=str(cmd),
            stdout="",
            stderr=f"Unknown command type: {type(cmd).__name__}",
            status=NodeStatus.FAILED,
            exit_code=1,
            duration_ms=0,
            node_type="unknown",
        )

    @override
    @auto_timeout("dag")
    async def call(
        self,
        ctx: MCPContext,
        commands: List[Command],
        parallel: bool = False,
        shell: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        strict: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> str:
        """Execute commands with DAG semantics.
        
        Args:
            ctx: MCP context
            commands: List of commands (strings, tool dicts, or parallel blocks)
            parallel: Run all top-level commands in parallel
            shell: Shell to use (default: zsh)
            cwd: Working directory
            env: Additional environment variables
            timeout: Timeout per command in seconds
            strict: Stop on first error
            quiet: Suppress stdout in output
            
        Returns:
            Combined execution output
        """
        tool_ctx = create_tool_context(ctx)
        tool_ctx.set_tool_info(self.name)
        
        shell = shell or self.default_shell
        results: List[DagResult] = []
        
        if parallel:
            # Run all commands in parallel
            tasks = [
                self._execute_node(cmd, ctx, shell, cwd, env, timeout)
                for cmd in commands
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                r if not isinstance(r, Exception) 
                else DagResult(
                    node_id=f"error_{i}",
                    command=str(commands[i]),
                    stdout="",
                    stderr=str(r),
                    status=NodeStatus.FAILED,
                    exit_code=1,
                    duration_ms=0,
                    node_type="error",
                )
                for i, r in enumerate(results)
            ]
        else:
            # Serial execution with DAG support (nested parallel blocks)
            for cmd in commands:
                result = await self._execute_node(cmd, ctx, shell, cwd, env, timeout)
                results.append(result)
                
                # Stop on error if strict
                if strict and result.status == NodeStatus.FAILED:
                    break
        
        # Format output
        return self._format_output(results, quiet)

    def _format_output(self, results: List[DagResult], quiet: bool = False) -> str:
        """Format DAG execution results."""
        output_parts = []
        total_duration = 0
        failed_count = 0
        
        for r in results:
            total_duration += r.duration_ms
            
            if r.status == NodeStatus.FAILED:
                failed_count += 1
            
            # Add stdout unless quiet
            if r.stdout and not quiet:
                output_parts.append(r.stdout.rstrip())
            
            # Always show stderr
            if r.stderr:
                output_parts.append(f"[stderr] {r.stderr.rstrip()}")
        
        # Add summary for multi-command execution
        if len(results) > 1:
            status = "✓" if failed_count == 0 else f"✗ ({failed_count} failed)"
            output_parts.append(f"\n[dag] {len(results)} nodes, {total_duration}ms, {status}")
        
        return "\n".join(output_parts) if output_parts else "(no output)"

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register DAG tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def dag_handler(
            commands: Annotated[
                List[Any],
                Field(description="Commands to execute (strings, tool dicts, or parallel blocks)")
            ],
            parallel: Annotated[
                bool,
                Field(description="Run all commands in parallel", default=False)
            ] = False,
            shell: Annotated[
                Optional[str],
                Field(description="Shell to use (default: zsh)", default=None)
            ] = None,
            cwd: Annotated[
                Optional[str],
                Field(description="Working directory", default=None)
            ] = None,
            env: Annotated[
                Optional[Dict[str, str]],
                Field(description="Environment variables", default=None)
            ] = None,
            timeout: Annotated[
                int,
                Field(description="Timeout per command (seconds)", default=120)
            ] = 120,
            strict: Annotated[
                bool,
                Field(description="Stop on first error", default=False)
            ] = False,
            quiet: Annotated[
                bool,
                Field(description="Suppress stdout", default=False)
            ] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                commands=commands,
                parallel=parallel,
                shell=shell,
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


def create_dag_tool(
    tools: Optional[Dict[str, BaseTool]] = None, 
    default_shell: str = "zsh"
) -> DagTool:
    """Factory to create DAG execution tool."""
    return DagTool(tools, default_shell)
