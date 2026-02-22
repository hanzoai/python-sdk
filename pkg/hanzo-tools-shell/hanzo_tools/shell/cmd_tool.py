"""Cmd tool - unified execution graph (DAG) for command execution.

The primary command execution tool for hanzo-mcp. Run commands with:
- Serial execution (default)
- Parallel execution
- Mixed execution graphs
- Tool invocations
- Auto-backgrounding at 45s
"""

import os
import shutil
import asyncio
from enum import Enum
from typing import Any, Dict, List, Union, Optional, Annotated, override
from datetime import datetime
from dataclasses import field, dataclass

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.shell.base_process import get_shell_executor


class NodeStatus(Enum):
    """Execution status of a command node."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CmdResult:
    """Result from a single command execution."""

    node_id: str
    command: str
    stdout: str
    stderr: str
    status: NodeStatus
    exit_code: int
    duration_ms: int = 0
    node_type: str = "shell"


@dataclass
class CmdNode:
    """A node in the execution graph."""

    id: str
    command: Union[str, Dict[str, Any]]
    depends_on: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[CmdResult] = None


Command = Union[str, Dict[str, Any], List[Any]]


class CmdTool(BaseTool):
    """Unified command execution with DAG support.

    The primary tool for running shell commands. Supports:
    - Simple commands: cmd("ls -la")
    - Serial execution: cmd(["ls", "pwd", "git status"])
    - Parallel execution: cmd(["npm i", "cargo build"], parallel=True)
    - Mixed DAG: cmd(["mkdir dist", {"parallel": ["cp a", "cp b"]}, "zip out"])
    - Tool invocations: cmd([{"tool": "search", "input": {"pattern": "TODO"}}])
    - Named deps: cmd([{"id": "a", "run": "...", "after": ["b"]}])

    Auto-backgrounds commands after 45s. Uses zsh by default.
    """

    name = "cmd"

    def __init__(
        self,
        tools: Optional[Dict[str, BaseTool]] = None,
        default_shell: str = "zsh",
    ):
        """Initialize command execution tool."""
        super().__init__()
        self.tools = tools or {}
        self.default_shell = self._resolve_shell(default_shell)

    def _resolve_shell(self, preferred: str) -> str:
        """Resolve shell - prefer zsh, fallback to bash/fish/sh.

        Supports: zsh, bash, fish, sh, dash, ksh, tcsh, csh
        """
        # Allow override via environment
        force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
        if force_shell:
            return force_shell

        # Shell priority: modern shells first
        shell_priority = ["zsh", "bash", "fish", "dash", "sh"]
        search_paths = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/bin",
            "/usr/bin",
            "/usr/local/fish/bin",  # Common fish location
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
        shell_name = os.path.basename(self.default_shell)
        return f"""Execute commands with DAG support (shell: {shell_name}).

SIMPLE:
  cmd("ls -la")                     # Single command
  cmd("A ; B ; C")                  # Sequential via shell

ARRAYS:
  cmd(["a", "b", "c"])              # Sequential
  cmd(["a", "b"], parallel=True)    # All parallel
  cmd(["a", ["b", "c"], "d"])       # Nested = parallel

DAG:
  cmd([
      "mkdir dist",
      {{"parallel": ["cp a dist/", "cp b dist/"]}},
      "zip -r out.zip dist/"
  ])

TOOL INVOCATION:
  cmd([{{"tool": "search", "input": {{"pattern": "TODO"}}}}])

OPTIONS:
  parallel: Run ALL top-level commands concurrently
  shell: Use different shell (zsh, bash, fish, dash, sh)
  strict: Stop on first error
  quiet: Suppress stdout
  timeout: Per-command timeout (default: 45s)
  cwd: Working directory
  env: Environment variables

AUTO-BACKGROUNDING: Commands exceeding 45s auto-background.
Use ps --logs <id> to view, ps --kill <id> to stop."""

    async def _run_shell(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        shell: Optional[str] = None,
    ) -> CmdResult:
        """Run a shell command with auto-backgrounding on timeout.

        Uses the shared ShellExecutor for consistent 45s auto-backgrounding.
        """
        start_time = datetime.now()
        node_id = f"shell_{id(cmd)}"
        executor = get_shell_executor()
        use_shell = shell or self.default_shell

        stdout, stderr, exit_code, was_backgrounded, process_id = (
            await executor.run_shell(
                command=cmd,
                shell=use_shell,
                cwd=cwd,
                env=env,
                timeout=float(timeout),
                tool_name="cmd",
            )
        )

        duration = int((datetime.now() - start_time).total_seconds() * 1000)

        if was_backgrounded:
            return CmdResult(
                node_id=node_id,
                command=cmd,
                stdout=stdout,
                stderr=stderr,
                status=NodeStatus.SUCCESS,  # Backgrounded = success from caller's POV
                exit_code=0,
                duration_ms=duration,
                node_type="shell",
            )

        return CmdResult(
            node_id=node_id,
            command=cmd,
            stdout=stdout,
            stderr=stderr,
            status=NodeStatus.SUCCESS if exit_code == 0 else NodeStatus.FAILED,
            exit_code=exit_code,
            duration_ms=duration,
            node_type="shell",
        )

    async def _run_tool(
        self, tool_name: str, tool_input: Dict[str, Any], ctx: MCPContext
    ) -> CmdResult:
        """Run an MCP tool invocation."""
        start_time = datetime.now()
        node_id = f"tool_{tool_name}"

        if tool_name not in self.tools:
            return CmdResult(
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

            return CmdResult(
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
            return CmdResult(
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
    ) -> CmdResult:
        """Execute a single command node.

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

            return CmdResult(
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
                tasks = [
                    self._execute_node(c, ctx, cwd, env, timeout, shell)
                    for c in parallel_cmds
                ]
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

                return CmdResult(
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
                return await self._execute_node(run_cmd, ctx, cwd, env, timeout, shell)

            return CmdResult(
                node_id="unknown",
                command=str(cmd),
                stdout="",
                stderr=f"Unknown command format: {cmd}",
                status=NodeStatus.FAILED,
                exit_code=1,
                duration_ms=0,
                node_type="unknown",
            )

        return CmdResult(
            node_id="unknown",
            command=str(cmd),
            stdout="",
            stderr=f"Unknown command type: {type(cmd).__name__}",
            status=NodeStatus.FAILED,
            exit_code=1,
            duration_ms=0,
            node_type="unknown",
        )

    def _format_output(self, results: List[CmdResult], quiet: bool = False) -> str:
        """Format command execution results."""
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
            output_parts.append(
                f"\n[cmd] {len(results)} nodes, {total_duration}ms, {status}"
            )

        return "\n".join(output_parts) if output_parts else "(no output)"

    @override
    @auto_timeout("cmd")
    async def call(
        self,
        ctx: MCPContext,
        command: Optional[str] = None,
        commands: Optional[List[Command]] = None,
        parallel: bool = False,
        shell: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        strict: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> str:
        """Execute commands with optional DAG semantics.

        Args:
            command: Single command string (simple mode)
            commands: List of commands for DAG mode
            parallel: Run all commands concurrently
            shell: Shell to use (default: zsh)
            cwd: Working directory
            env: Additional environment variables
            timeout: Per-command timeout in seconds (default: 45)
            strict: Stop on first error
            quiet: Suppress stdout
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Single command mode
        if command and not commands:
            result = await self._run_shell(command, cwd, env, timeout, shell)
            if result.status == NodeStatus.SUCCESS:
                return result.stdout if result.stdout else "(no output)"
            return (
                f"{result.stdout}\n[stderr] {result.stderr}"
                if result.stderr
                else result.stdout
            )

        # DAG mode
        if not commands:
            return "Error: Provide either 'command' (string) or 'commands' (list)"

        results: List[CmdResult] = []

        if parallel:
            tasks = [
                self._execute_node(cmd, ctx, cwd, env, timeout, shell)
                for cmd in commands
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                (
                    r
                    if not isinstance(r, Exception)
                    else CmdResult(
                        node_id=f"error_{i}",
                        command=str(commands[i]),
                        stdout="",
                        stderr=str(r),
                        status=NodeStatus.FAILED,
                        exit_code=1,
                        duration_ms=0,
                        node_type="error",
                    )
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
        """Register cmd tool with MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def cmd_handler(
            command: Annotated[
                Optional[str],
                Field(description="Single command to execute", default=None),
            ] = None,
            commands: Annotated[
                Optional[List[Any]],
                Field(description="List of commands for DAG execution", default=None),
            ] = None,
            parallel: Annotated[
                bool, Field(description="Run all commands in parallel", default=False)
            ] = False,
            shell: Annotated[
                Optional[str], Field(description="Shell: zsh, bash, sh", default=None)
            ] = None,
            cwd: Annotated[
                Optional[str], Field(description="Working directory", default=None)
            ] = None,
            env: Annotated[
                Optional[Dict[str, str]],
                Field(description="Environment variables", default=None),
            ] = None,
            timeout: Annotated[
                int, Field(description="Timeout per command (seconds)", default=30)
            ] = 30,
            strict: Annotated[
                bool, Field(description="Stop on first error", default=False)
            ] = False,
            quiet: Annotated[
                bool, Field(description="Suppress stdout", default=False)
            ] = False,
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


def create_cmd_tool(
    tools: Optional[Dict[str, BaseTool]] = None, default_shell: str = "zsh"
) -> CmdTool:
    """Factory to create command execution tool."""
    return CmdTool(tools, default_shell)


# Singleton instance
cmd_tool = CmdTool()
