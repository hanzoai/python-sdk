"""Base classes for process execution tools.

All process execution uses asyncio.subprocess for consistency.
All file I/O uses hanzo_async for non-blocking operations with uvloop support.
"""

import os
import time
import uuid
import asyncio
import tempfile
from abc import abstractmethod
from typing import Any, Dict, List, Tuple, Optional, override
from pathlib import Path

from hanzo_async import mkdir, write_file, append_file

from hanzo_tools.core import BaseTool, PermissionManager
from hanzo_tools.shell.truncate import truncate_response


class ProcessManager:
    """Singleton manager for background processes.

    All processes are asyncio.subprocess.Process instances.
    """

    _instance = None
    _processes: Dict[str, asyncio.subprocess.Process] = {}
    _logs: Dict[str, str] = {}
    _log_dir = Path(tempfile.gettempdir()) / "hanzo_mcp_logs"
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _ensure_log_dir(self) -> None:
        """Ensure log directory exists (async-safe)."""
        if not self._initialized:
            await mkdir(self._log_dir, parents=True, exist_ok=True)
            self._initialized = True

    def add_process(self, process_id: str, process: asyncio.subprocess.Process, log_file: str) -> None:
        """Add a process to track."""
        self._processes[process_id] = process
        self._logs[process_id] = log_file

    def get_process(self, process_id: str) -> Optional[asyncio.subprocess.Process]:
        """Get a tracked process."""
        return self._processes.get(process_id)

    def remove_process(self, process_id: str) -> None:
        """Remove a process from tracking."""
        self._processes.pop(process_id, None)
        self._logs.pop(process_id, None)

    def list_processes(self) -> Dict[str, Dict[str, Any]]:
        """List all tracked processes.
        
        Note: Uses list(items()) to create snapshot before cleanup,
        preventing RuntimeError from dict modification during iteration.
        Completed processes are cleaned up after being reported.
        """
        result = {}
        for pid, proc in list(self._processes.items()):
            is_running = proc.returncode is None

            if is_running:
                result[pid] = {
                    "pid": proc.pid,
                    "running": True,
                    "log_file": self._logs.get(pid),
                }
            else:
                result[pid] = {
                    "pid": proc.pid,
                    "running": False,
                    "return_code": proc.returncode,
                    "log_file": self._logs.get(pid),
                }
                self.remove_process(pid)
        return result

    def get_log_file(self, process_id: str) -> Optional[Path]:
        """Get log file path for a process."""
        log_path = self._logs.get(process_id)
        return Path(log_path) if log_path else None

    @property
    def log_dir(self) -> Path:
        """Get the log directory."""
        return self._log_dir

    async def create_log_file(self, process_id: str) -> Path:
        """Create a log file for a process (async-safe)."""
        await self._ensure_log_dir()
        log_file = self._log_dir / f"{process_id}.log"
        await write_file(log_file, "")
        return log_file

    def mark_completed(self, process_id: str, return_code: int) -> None:
        """Mark a process as completed."""
        self.remove_process(process_id)


class AutoBackgroundExecutor:
    """Executor that automatically backgrounds long-running processes.

    IMPORTANT: Always backgrounds after MAX_FOREGROUND_TIMEOUT (30s) to keep
    the agent loop responsive. Longer timeouts only affect the background
    process lifetime, not the foreground wait time.
    """

    DEFAULT_TIMEOUT = 30.0  # Default timeout for backgrounding
    MAX_FOREGROUND_TIMEOUT = 30.0  # ALWAYS background after 30s, even if longer timeout given

    def __init__(self, process_manager: ProcessManager, timeout: float = DEFAULT_TIMEOUT):
        """Initialize the auto-background executor."""
        self.process_manager = process_manager
        self.default_timeout = timeout

    async def execute_with_auto_background(
        self,
        cmd_args: list[str],
        tool_name: str,
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """Execute a command with automatic backgrounding if it takes too long.

        Returns:
            Tuple of (output/status, was_backgrounded, process_id)

        Note: Always backgrounds after MAX_FOREGROUND_TIMEOUT (30s) to keep
        the agent loop responsive. The passed timeout is stored for reference
        but doesn't extend foreground wait time.
        """
        # ALWAYS cap at MAX_FOREGROUND_TIMEOUT to keep agent loop responsive
        # Longer timeouts only affect background process, not foreground wait
        requested_timeout = timeout if timeout is not None else self.default_timeout
        effective_timeout = min(requested_timeout, self.MAX_FOREGROUND_TIMEOUT)

        # Fast path for tests - still async but with shorter timeout
        if os.getenv("HANZO_MCP_FAST_TESTS") == "1":
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd) if cwd else None,
                    env=env,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                if proc.returncode != 0:
                    return (
                        f"Command failed with exit code {proc.returncode}:\n"
                        f"{stdout.decode('utf-8', errors='replace')}"
                        f"{stderr.decode('utf-8', errors='replace')}",
                        False,
                        None,
                    )
                return stdout.decode("utf-8", errors="replace"), False, None
            except asyncio.TimeoutError:
                return "Command timed out in test mode", False, None
            except Exception as e:
                return f"Error executing command: {e}", False, None

        # Generate process ID
        process_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

        # Create log file
        log_file = await self.process_manager.create_log_file(process_id)

        # Start the process
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
            env=env,
        )

        # Track in process manager
        self.process_manager.add_process(process_id, process, str(log_file))

        # Try to wait for completion with timeout
        start_time = time.time()
        output_lines = []

        try:

            async def read_output():
                if process.stdout:
                    async for line in process.stdout:
                        line_str = line.decode("utf-8", errors="replace")
                        output_lines.append(line_str)
                        await append_file(log_file, line_str)

            async def wait_for_process():
                return await process.wait()

            read_task = asyncio.create_task(read_output())
            wait_task = asyncio.create_task(wait_for_process())

            done, pending = await asyncio.wait(
                [read_task, wait_task],
                timeout=effective_timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if wait_task in done:
                return_code = await wait_task

                try:
                    await asyncio.wait_for(read_task, timeout=0.5)
                except asyncio.TimeoutError:
                    read_task.cancel()
                    try:
                        await read_task
                    except asyncio.CancelledError:
                        pass

                self.process_manager.mark_completed(process_id, return_code)

                output = "".join(output_lines)
                if return_code != 0:
                    return (
                        f"Command failed with exit code {return_code}:\n{output}",
                        False,
                        None,
                    )
                else:
                    return output, False, None

            else:
                # Timeout - background the process
                for task in pending:
                    task.cancel()

                asyncio.create_task(self._background_reader(process, process_id, log_file))

                elapsed = time.time() - start_time
                partial_output = "".join(output_lines[-50:])

                return (
                    f"Process automatically backgrounded after {elapsed:.1f}s\n"
                    f"Process ID: {process_id}\n"
                    f"Log file: {log_file}\n\n"
                    f"Use 'ps --logs {process_id}' to view full output\n"
                    f"Use 'ps --kill {process_id}' to stop the process\n\n"
                    f"=== Last output ===\n{partial_output}",
                    True,
                    process_id,
                )

        except Exception as e:
            self.process_manager.mark_completed(process_id, -1)
            return f"Error executing command: {str(e)}", False, None

    async def _background_reader(self, process, process_id: str, log_file: Path):
        """Continue reading output from a backgrounded process."""
        try:
            if process.stdout:
                async for line in process.stdout:
                    await append_file(log_file, line.decode("utf-8", errors="replace"))

            return_code = await process.wait()
            self.process_manager.mark_completed(process_id, return_code)

            await append_file(log_file, f"\n\n=== Process completed with exit code {return_code} ===\n")

        except Exception as e:
            await append_file(log_file, f"\n\n=== Background reader error: {str(e)} ===\n")
            self.process_manager.mark_completed(process_id, -1)


class BaseProcessTool(BaseTool):
    """Base class for all process execution tools."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """Initialize the process tool."""
        super().__init__()
        self.permission_manager = permission_manager
        self.process_manager = ProcessManager()
        self.auto_background_executor = AutoBackgroundExecutor(self.process_manager)

    @abstractmethod
    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get the command arguments for subprocess."""
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool being used."""
        pass

    async def execute_sync(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Execute a command with auto-backgrounding after 2 minutes."""
        if self.permission_manager and cwd:
            if not self.permission_manager.is_path_allowed(str(cwd)):
                raise PermissionError(f"Access denied to path: {cwd}")

        cmd_args = self.get_command_args(command, **kwargs)

        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        output, was_backgrounded, process_id = await self.auto_background_executor.execute_with_auto_background(
            cmd_args=cmd_args,
            tool_name=self.get_tool_name(),
            cwd=cwd,
            env=process_env,
            timeout=float(timeout) if timeout is not None else None,
        )

        if was_backgrounded:
            return output
        else:
            if output.startswith("Command failed"):
                raise RuntimeError(output)
            max_tokens = int(os.environ.get("HANZO_MCP_MAX_RESPONSE_TOKENS", "25000"))
            return truncate_response(
                output,
                max_tokens=max_tokens,
                truncation_message=f"\n\n[Command output truncated due to {max_tokens} token limit.]",
            )

    async def execute_background(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a command in the background."""
        if self.permission_manager and cwd:
            if not self.permission_manager.is_path_allowed(str(cwd)):
                raise PermissionError(f"Access denied to path: {cwd}")

        process_id = f"{self.get_tool_name()}_{uuid.uuid4().hex[:8]}"
        log_file = self.process_manager.log_dir / f"{process_id}.log"

        cmd_args = self.get_command_args(command, **kwargs)

        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=cwd,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        self.process_manager.add_process(process_id, process, str(log_file))
        asyncio.create_task(self._write_output_to_log(process, log_file, process_id))

        return {
            "process_id": process_id,
            "pid": process.pid,
            "log_file": str(log_file),
            "status": "started",
        }

    async def _write_output_to_log(self, process: asyncio.subprocess.Process, log_file: Path, process_id: str) -> None:
        """Write process output to log file in background."""
        try:
            # Clear log file
            await write_file(log_file, "")
            if process.stdout:
                async for line in process.stdout:
                    await append_file(log_file, line.decode("utf-8", errors="replace"))

            return_code = await process.wait()

            await append_file(log_file, f"\n=== Process completed with exit code {return_code} ===\n")

            self.process_manager.mark_completed(process_id, return_code)

        except Exception as e:
            await append_file(log_file, f"\n=== Error: {str(e)} ===\n")
            self.process_manager.mark_completed(process_id, -1)


class BaseBinaryTool(BaseProcessTool):
    """Base class for binary execution tools (like npx, uvx)."""

    @abstractmethod
    def get_binary_name(self) -> str:
        """Get the name of the binary to execute."""
        pass

    @override
    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get command arguments for binary execution."""
        cmd_args = [self.get_binary_name()]

        if "flags" in kwargs:
            cmd_args.extend(kwargs["flags"])

        cmd_args.append(command)

        if "args" in kwargs:
            if isinstance(kwargs["args"], str):
                cmd_args.extend(kwargs["args"].split())
            else:
                cmd_args.extend(kwargs["args"])

        return cmd_args

    @override
    def get_tool_name(self) -> str:
        """Get the tool name (same as binary name by default)."""
        return self.get_binary_name()


class BaseScriptTool(BaseProcessTool):
    """Base class for script execution tools (like bash, python)."""

    @abstractmethod
    def get_interpreter(self) -> str:
        """Get the interpreter to use."""
        pass

    @abstractmethod
    def get_script_flags(self) -> List[str]:
        """Get default flags for the interpreter."""
        pass

    @override
    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get command arguments for script execution."""
        cmd_args = [self.get_interpreter()]
        cmd_args.extend(self.get_script_flags())
        cmd_args.append(command)
        return cmd_args

    @override
    def get_tool_name(self) -> str:
        """Get the tool name (interpreter name by default)."""
        return self.get_interpreter()


# Shared singleton for shell execution
_shell_executor: Optional["ShellExecutor"] = None


class ShellExecutor:
    """Shared async shell executor for all shell tools.

    Ensures consistent auto-backgrounding behavior across dag, zsh, shell, bash tools.
    Uses a singleton pattern to share process management state.
    Auto-backgrounds after 30s to keep agent loop responsive.
    """

    DEFAULT_TIMEOUT = 30.0  # Auto-background after 30 seconds

    _instance: Optional["ShellExecutor"] = None

    def __new__(cls) -> "ShellExecutor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._process_manager = ProcessManager()

    @property
    def process_manager(self) -> ProcessManager:
        return self._process_manager

    async def run_shell(
        self,
        command: str,
        shell: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT,
        tool_name: str = "shell",
    ) -> Tuple[str, str, int, bool, Optional[str]]:
        """Run a shell command with auto-backgrounding on timeout.

        Args:
            command: Shell command to execute
            shell: Shell binary path (e.g., /bin/zsh)
            cwd: Working directory
            env: Environment variables
            timeout: Timeout before auto-backgrounding (default: 30s)
            tool_name: Tool name for process ID prefix

        Returns:
            Tuple of (stdout, stderr, exit_code, was_backgrounded, process_id)
        """
        # Cap timeout at 30s for foreground wait - keep agent loop responsive
        effective_timeout = min(timeout, self.DEFAULT_TIMEOUT)

        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        shell_name = os.path.basename(shell)
        process_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
        log_file = await self._process_manager.create_log_file(process_id)

        try:
            proc = await asyncio.create_subprocess_exec(
                shell,
                "-c",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=run_env,
                # Prevent zombie processes - use start_new_session on Unix
                start_new_session=True,
            )

            stdout_chunks: list[bytes] = []
            stderr_chunks: list[bytes] = []

            async def read_stdout():
                if proc.stdout:
                    while True:
                        chunk = await proc.stdout.read(8192)
                        if not chunk:
                            break
                        stdout_chunks.append(chunk)

            async def read_stderr():
                if proc.stderr:
                    while True:
                        chunk = await proc.stderr.read(8192)
                        if not chunk:
                            break
                        stderr_chunks.append(chunk)

            try:
                # Read streams and wait for process with timeout
                await asyncio.wait_for(
                    asyncio.gather(read_stdout(), read_stderr(), proc.wait()),
                    timeout=effective_timeout
                )

                exit_code = proc.returncode or 0
                return (
                    b"".join(stdout_chunks).decode("utf-8", errors="replace"),
                    b"".join(stderr_chunks).decode("utf-8", errors="replace"),
                    exit_code,
                    False,  # Not backgrounded
                    None,   # No process_id (completed)
                )

            except asyncio.TimeoutError:
                # Background the process - don't kill it
                partial_stdout = b"".join(stdout_chunks).decode("utf-8", errors="replace")
                partial_stderr = b"".join(stderr_chunks).decode("utf-8", errors="replace")
                
                await write_file(log_file,
                    f"[{shell_name}] Command backgrounded after {effective_timeout}s timeout\n"
                    f"[{shell_name}] Command: {command}\n"
                    f"[{shell_name}] PID: {proc.pid}\n"
                    + "-" * 40 + "\n"
                    f"{partial_stdout}{partial_stderr}"
                )

                self._process_manager.add_process(process_id, proc, str(log_file))
                asyncio.create_task(self._capture_background_output(proc, log_file, process_id))

                return (
                    f"[backgrounded] Process {process_id} (PID {proc.pid}) running in background.\n"
                    f"Use: ps --logs {process_id}  # view output\n"
                    f"Use: ps --kill {process_id}  # stop process",
                    "",
                    0,
                    True,  # Was backgrounded
                    process_id,
                )

        except Exception as e:
            # Clean up on error - kill process if it exists
            try:
                if proc and proc.returncode is None:
                    proc.kill()
                    await proc.wait()
            except Exception:
                pass
            return (
                "",
                str(e),
                1,
                False,
                None,
            )

    async def _capture_background_output(
        self,
        proc: asyncio.subprocess.Process,
        log_file: Path,
        process_id: str,
    ) -> None:
        """Capture output from backgrounded process to log file."""
        try:
            async def read_stream(stream, prefix: str) -> None:
                if stream:
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        await append_file(log_file, f"{prefix}{line.decode('utf-8', errors='replace')}")

            await asyncio.gather(
                read_stream(proc.stdout, ""),
                read_stream(proc.stderr, "[stderr] "),
            )

            await proc.wait()
            await append_file(log_file, f"\n[shell] Process exited with code {proc.returncode}\n")

            self._process_manager.mark_completed(process_id, proc.returncode or 0)
        except Exception:
            self._process_manager.mark_completed(process_id, -1)


def get_shell_executor() -> ShellExecutor:
    """Get the shared shell executor singleton."""
    global _shell_executor
    if _shell_executor is None:
        _shell_executor = ShellExecutor()
    return _shell_executor
