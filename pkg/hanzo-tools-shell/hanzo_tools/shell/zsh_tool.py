"""Unified Zsh shell tool with DAG execution support.

Combines simple shell execution with DAG (directed acyclic graph) semantics.
Supports serial, parallel, and complex mixed execution patterns.

Usage:
    zsh("ls -la")                           # Single command
    zsh(["ls", "pwd", "git status"])        # Serial execution
    zsh(["npm i", "cargo build"], parallel=True)  # Parallel
    zsh([
        "mkdir dist",
        {"parallel": ["cp a.txt dist/", "cp b.txt dist/"]},
        "zip -r out.zip dist/"
    ])  # Mixed DAG
"""

import os
import uuid
import shutil
import asyncio
import platform
from enum import Enum
from typing import Any, Dict, List, Union, Optional, Annotated, override
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass

import aiofiles
from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.shell.base_process import ProcessManager
from hanzo_tools.shell.shellflow import parse as parse_shellflow, to_commands as shellflow_to_commands


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
    node_type: str = "shell"


@dataclass
class DagNode:
    """A node in the execution DAG."""

    id: str
    command: Union[str, Dict[str, Any]]
    depends_on: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[DagResult] = None


Command = Union[str, Dict[str, Any], List[Any]]


class ZshTool(BaseTool):
    """Zsh shell with full DAG execution support.

    The primary shell tool for hanzo-mcp. Supports:
    - Simple command execution: zsh("ls -la")
    - Serial execution: zsh(["cmd1", "cmd2"])
    - Parallel execution: zsh(["cmd1", "cmd2"], parallel=True)
    - Mixed DAG patterns: zsh(["setup", {"parallel": ["a", "b"]}, "finish"])
    - Tool invocations: zsh([{"tool": "search", "input": {"pattern": "TODO"}}])
    - Named dependencies: zsh([{"id": "a", "run": "...", "after": ["b"]}])

    Uses zsh by default, falls back to bash.
    Auto-backgrounds long-running processes.
    """

    name = "zsh"

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        """Initialize Zsh tool with optional tool registry for DAG tool invocations."""
        super().__init__()
        self.tools = tools or {}
        self._shell = self._resolve_shell()

    def _resolve_shell(self) -> str:
        """Resolve shell - prefer zsh, fallback to bash."""
        # Allow override
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        shell_priority = ["zsh", "bash"]
        search_paths = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/bin",
            "/usr/bin",
        ]

        for shell in shell_priority:
            for prefix in search_paths:
                full_path = f"{prefix}/{shell}"
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
            found = shutil.which(shell)
            if found:
                return found

        return "sh"

    @property
    @override
    def description(self) -> str:
        shell_name = os.path.basename(self._shell)
        return f"""Zsh shell with DAG execution support (using: {shell_name}).

SHELLFLOW SYNTAX (inline DAG):
  zsh("A ; B ; C")                    # Sequential
  zsh("{{ A & B & C }}")                # Parallel
  zsh("setup ; {{ a & b & c }} ; done") # Mixed

ARRAY SYNTAX:
  zsh(["a", "b", "c"])                # Sequential
  zsh(["a", ["b", "c", "d"], "e"])    # Nested = parallel
  zsh(["a", "b"], parallel=True)      # All parallel

EXAMPLE:
  zsh("mkdir -p dist ; {{ cp a dist/ & cp b dist/ }} ; zip -r out.zip dist/")

OPTIONS:
  shell: Use different shell (bash, sh, fish)
  parallel: Run ALL top-level commands concurrently
  strict: Stop on first error
  quiet: Suppress stdout
  timeout: Per-command timeout (default: 120s)
  cwd: Working directory
  env: Environment variables

AUTO-BACKGROUNDING: Commands exceeding timeout auto-background.
Use ps --logs <id> to view, ps --kill <id> to stop."""

    async def _run_shell(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        shell: Optional[str] = None,
    ) -> DagResult:
        """Run a shell command with auto-backgrounding on timeout."""
        start_time = datetime.now()
        node_id = f"shell_{id(cmd)}"
        process_manager = ProcessManager()
        
        # Use specified shell or default
        use_shell = shell or self._shell

        try:
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            shell_name = os.path.basename(use_shell)
            process_id = f"{shell_name}_{uuid.uuid4().hex[:8]}"
            log_file = await process_manager.create_log_file(process_id)

            proc = await asyncio.create_subprocess_exec(
                use_shell,
                "-c",
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=run_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

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
                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                async with aiofiles.open(log_file, "w") as f:
                    await f.write(f"[{shell_name}] Command backgrounded after {timeout}s timeout\n")
                    await f.write(f"[{shell_name}] Command: {cmd}\n")
                    await f.write(f"[{shell_name}] PID: {proc.pid}\n")
                    await f.write(f"[{shell_name}] Started: {start_time.isoformat()}\n")
                    await f.write("-" * 40 + "\n")

                process_manager.add_process(process_id, proc, str(log_file))
                asyncio.create_task(self._capture_background_output(proc, log_file))

                return DagResult(
                    node_id=node_id,
                    command=cmd,
                    stdout=f"[backgrounded] Process {process_id} (PID {proc.pid}) running in background.\n"
                    f"Use: ps --logs {process_id}  # view output\n"
                    f"Use: ps --kill {process_id}  # stop process",
                    stderr="",
                    status=NodeStatus.SUCCESS,
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

    async def _capture_background_output(self, proc: asyncio.subprocess.Process, log_file: Path) -> None:
        """Capture output from backgrounded process to log file."""
        try:
            async with aiofiles.open(log_file, "a") as f:

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

                await proc.wait()
                await f.write(f"\n[shell] Process exited with code {proc.returncode}\n")
        except Exception:
            pass

    async def _run_tool(self, tool_name: str, tool_input: Dict[str, Any], ctx: MCPContext) -> DagResult:
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
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        timeout: int,
        shell: Optional[str] = None,
    ) -> DagResult:
        """Execute a single DAG node.
        
        Supports:
        - str: Single command
        - list: Nested array = parallel execution
        - dict with "parallel": Explicit parallel block
        - dict with "tool": Tool invocation
        - dict with "run": Command wrapper
        """

        if isinstance(cmd, str):
            return await self._run_shell(cmd, cwd, env, timeout, shell)

        # Nested array = parallel execution
        if isinstance(cmd, list):
            tasks = [self._execute_node(c, ctx, cwd, env, timeout, shell) for c in cmd]
            results = await asyncio.gather(*tasks, return_exceptions=True)

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
                node_id=f"parallel_{len(cmd)}",
                command=f"parallel[{len(cmd)} tasks]",
                stdout="\n".join(combined_stdout),
                stderr="\n".join(combined_stderr),
                status=NodeStatus.SUCCESS if all_success else NodeStatus.FAILED,
                exit_code=0 if all_success else 1,
                duration_ms=total_duration,
                node_type="parallel",
            )

        if isinstance(cmd, dict):
            if "tool" in cmd:
                return await self._run_tool(cmd["tool"], cmd.get("input", {}), ctx)

            if "parallel" in cmd:
                parallel_cmds = cmd["parallel"]
                tasks = [self._execute_node(c, ctx, cwd, env, timeout, shell) for c in parallel_cmds]
                results = await asyncio.gather(*tasks, return_exceptions=True)

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

            if "run" in cmd:
                run_cmd = cmd["run"]
                return await self._execute_node(run_cmd, ctx, cwd, env, timeout)

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

    def _format_output(self, results: List[DagResult], quiet: bool = False) -> str:
        """Format DAG execution results."""
        output_parts = []
        total_duration = 0
        failed_count = 0

        for r in results:
            total_duration += r.duration_ms

            if r.status == NodeStatus.FAILED:
                failed_count += 1

            if r.stdout and not quiet:
                output_parts.append(r.stdout.rstrip())

            if r.stderr:
                output_parts.append(f"[stderr] {r.stderr.rstrip()}")

        if len(results) > 1:
            status = "✓" if failed_count == 0 else f"✗ ({failed_count} failed)"
            output_parts.append(f"\n[zsh] {len(results)} nodes, {total_duration}ms, {status}")

        return "\n".join(output_parts) if output_parts else "(no output)"

    @override
    @auto_timeout("zsh")
    async def call(
        self,
        ctx: MCPContext,
        command: Optional[str] = None,
        commands: Optional[List[Command]] = None,
        parallel: bool = False,
        shell: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        strict: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> str:
        """Execute shell commands with optional DAG semantics.
        
        Args:
            command: Single command string (simple mode)
            commands: List of commands for DAG mode
            parallel: Run all commands concurrently
            shell: Shell to use (default: zsh, options: bash, sh, fish, etc.)
            cwd: Working directory
            env: Additional environment variables
            timeout: Per-command timeout in seconds
            strict: Stop on first error
            quiet: Suppress stdout
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Single command mode
        if command and not commands:
            # Check for shellflow syntax (contains ; or { & })
            if ';' in command or ('&' in command and '{' in command):
                # Parse as shellflow
                commands = shellflow_to_commands(parse_shellflow(command))
            else:
                # Simple command
                result = await self._run_shell(command, cwd, env, timeout, shell)
                if result.status == NodeStatus.SUCCESS:
                    return result.stdout if result.stdout else "(no output)"
                return f"{result.stdout}\n[stderr] {result.stderr}" if result.stderr else result.stdout

        # DAG mode
        if not commands:
            return "Error: Provide either 'command' (string) or 'commands' (list)"

        results: List[DagResult] = []

        if parallel:
            tasks = [self._execute_node(cmd, ctx, cwd, env, timeout, shell) for cmd in commands]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                r
                if not isinstance(r, Exception)
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
            for cmd in commands:
                result = await self._execute_node(cmd, ctx, cwd, env, timeout, shell)
                results.append(result)

                if strict and result.status == NodeStatus.FAILED:
                    break

        return self._format_output(results, quiet)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register zsh tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def zsh(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands for DAG execution", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run all commands in parallel", default=False)] = False,
            shell: Annotated[
                Optional[str], Field(description="Shell to use: zsh, bash, sh, fish (default: zsh)", default=None)
            ] = None,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout per command (seconds)", default=120)] = 120,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=shell,
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class ShellTool(ZshTool):
    """Alias for ZshTool - smart shell that uses zsh > bash."""

    name = "shell"

    @property
    @override
    def description(self) -> str:
        shell_name = os.path.basename(self._shell)
        return f"""Run shell commands using the best available shell (currently: {shell_name}).

Automatically selects:
- Zsh if available (with .zshrc)
- User's preferred shell ($SHELL)
- Bash as fallback

Full Shellflow + DAG support.

SHELLFLOW:
  shell("A ; B ; C")                  # Sequential
  shell("{{ A & B & C }}")              # Parallel
  shell("setup ; {{ a & b }} ; done")   # Mixed

ARRAYS:
  shell(["a", "b", "c"])              # Sequential
  shell(["a", ["b", "c"], "d"])       # Nested = parallel"""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register shell tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def shell(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands for DAG execution", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run all commands in parallel", default=False)] = False,
            shell: Annotated[
                Optional[str], Field(description="Shell to use: zsh, bash, sh, fish", default=None)
            ] = None,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout per command (seconds)", default=120)] = 120,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                shell=shell,
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


class BashTool(ZshTool):
    """Bash shell with DAG support - alias for ZshTool with bash default."""

    name = "bash"

    def _resolve_shell(self) -> str:
        """Use bash as default shell."""
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell
        
        # Prefer bash
        bash_path = shutil.which("bash")
        if bash_path:
            return bash_path
        return "sh"

    @property
    @override
    def description(self) -> str:
        return """Bash shell with DAG execution support.

Same as zsh but defaults to bash. Full Shellflow + DAG support.

SHELLFLOW:
  bash("A ; B ; C")                  # Sequential
  bash("{ A & B & C }")              # Parallel
  bash("setup ; { a & b } ; done")   # Mixed

ARRAYS:
  bash(["a", "b", "c"])              # Sequential
  bash(["a", ["b", "c"], "d"])       # Nested = parallel"""

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register bash tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def bash(
            command: Annotated[
                Optional[str], Field(description="Single command to execute", default=None)
            ] = None,
            commands: Annotated[
                Optional[List[Any]], Field(description="List of commands for DAG execution", default=None)
            ] = None,
            parallel: Annotated[bool, Field(description="Run all commands in parallel", default=False)] = False,
            cwd: Annotated[Optional[str], Field(description="Working directory", default=None)] = None,
            env: Annotated[Optional[Dict[str, str]], Field(description="Environment variables", default=None)] = None,
            timeout: Annotated[int, Field(description="Timeout per command (seconds)", default=120)] = 120,
            strict: Annotated[bool, Field(description="Stop on first error", default=False)] = False,
            quiet: Annotated[bool, Field(description="Suppress stdout", default=False)] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                command=command,
                commands=commands,
                parallel=parallel,
                cwd=cwd,
                env=env,
                timeout=timeout,
                strict=strict,
                quiet=quiet,
            )


# Create tool instances
zsh_tool = ZshTool()
shell_tool = ShellTool()
bash_tool = BashTool()
