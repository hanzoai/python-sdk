"""Base classes for process execution tools.

All process execution uses asyncio.subprocess for consistency.
All file I/O uses aiofiles for non-blocking operations.
"""

import asyncio
import os
import uuid
import tempfile
from abc import abstractmethod
from typing import Any, Dict, List, Optional, override
from pathlib import Path

import aiofiles
import aiofiles.os

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.truncate import truncate_response
from hanzo_mcp.tools.common.permissions import PermissionManager


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
            await aiofiles.os.makedirs(self._log_dir, exist_ok=True)
            self._initialized = True

    def add_process(self, process_id: str, process: asyncio.subprocess.Process, log_file: str) -> None:
        """Add a process to track.

        Args:
            process_id: Unique process identifier
            process: asyncio subprocess instance
            log_file: Path to log file
        """
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

        Uses returncode attribute which works for asyncio.subprocess.Process.
        returncode is None if process is still running.
        """
        result = {}
        for pid, proc in list(self._processes.items()):
            # asyncio.subprocess.Process uses returncode directly (no poll())
            # returncode is None while running, set to exit code when done
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
                # Clean up finished processes
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
        """Create a log file for a process (async-safe).

        Args:
            process_id: Process identifier

        Returns:
            Path to the created log file
        """
        await self._ensure_log_dir()
        log_file = self._log_dir / f"{process_id}.log"
        # Create empty file asynchronously
        async with aiofiles.open(log_file, "w") as f:
            pass
        return log_file

    def mark_completed(self, process_id: str, return_code: int) -> None:
        """Mark a process as completed with the given return code.

        Args:
            process_id: Process identifier
            return_code: Process exit code
        """
        # Remove from tracking
        self.remove_process(process_id)


class BaseProcessTool(BaseTool):
    """Base class for all process execution tools."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """Initialize the process tool.

        Args:
            permission_manager: Optional permission manager for access control
        """
        super().__init__()
        self.permission_manager = permission_manager
        self.process_manager = ProcessManager()
        # Import here to avoid circular import
        from hanzo_mcp.tools.shell.auto_background import AutoBackgroundExecutor

        self.auto_background_executor = AutoBackgroundExecutor(self.process_manager)

    @abstractmethod
    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get the command arguments for subprocess.

        Args:
            command: The command or script to run
            **kwargs: Additional arguments specific to the tool

        Returns:
            List of command arguments for subprocess
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool being used (e.g., 'bash', 'uvx', 'npx')."""
        pass

    async def execute_sync(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Execute a command with auto-backgrounding after 2 minutes.

        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds (ignored - auto-backgrounds after 2 minutes)
            **kwargs: Additional tool-specific arguments

        Returns:
            Command output or background status

        Raises:
            RuntimeError: If command fails
        """
        # Check permissions if manager is available
        if self.permission_manager and cwd:
            if not self.permission_manager.is_path_allowed(str(cwd)):
                raise PermissionError(f"Access denied to path: {cwd}")

        # Get command arguments
        cmd_args = self.get_command_args(command, **kwargs)

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Execute with auto-backgrounding
        output, was_backgrounded, process_id = await self.auto_background_executor.execute_with_auto_background(
            cmd_args=cmd_args,
            tool_name=self.get_tool_name(),
            cwd=cwd,
            env=process_env,
        )

        if was_backgrounded:
            return output
        else:
            if output.startswith("Command failed"):
                raise RuntimeError(output)
            # Get configurable max tokens from environment, default to 25000
            max_tokens = int(os.environ.get("HANZO_MCP_MAX_RESPONSE_TOKENS", "25000"))
            # Truncate output to prevent token limit issues
            return truncate_response(
                output,
                max_tokens=max_tokens,
                truncation_message=f"\n\n[Command output truncated due to {max_tokens} token limit. Output may be available in logs or files. Set HANZO_MCP_MAX_RESPONSE_TOKENS env var to adjust limit.]",
            )

    async def execute_background(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a command in the background using asyncio.

        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional tool-specific arguments

        Returns:
            Dict with process_id and log_file
        """
        # Check permissions if manager is available
        if self.permission_manager and cwd:
            if not self.permission_manager.is_path_allowed(str(cwd)):
                raise PermissionError(f"Access denied to path: {cwd}")

        # Generate process ID and log file
        process_id = f"{self.get_tool_name()}_{uuid.uuid4().hex[:8]}"
        log_file = self.process_manager.log_dir / f"{process_id}.log"

        # Get command arguments
        cmd_args = self.get_command_args(command, **kwargs)

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Start process using asyncio (pure async, no sync subprocess)
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=cwd,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        # Track the process
        self.process_manager.add_process(process_id, process, str(log_file))

        # Start background task to read output to log file
        asyncio.create_task(self._write_output_to_log(process, log_file, process_id))

        return {
            "process_id": process_id,
            "pid": process.pid,
            "log_file": str(log_file),
            "status": "started",
        }

    async def _write_output_to_log(
        self,
        process: asyncio.subprocess.Process,
        log_file: Path,
        process_id: str
    ) -> None:
        """Write process output to log file in background.

        Uses aiofiles for non-blocking file I/O to avoid blocking the event loop.

        Args:
            process: The asyncio subprocess
            log_file: Path to write output
            process_id: Process identifier for cleanup
        """
        try:
            async with aiofiles.open(log_file, "w") as f:
                if process.stdout:
                    async for line in process.stdout:
                        await f.write(line.decode("utf-8", errors="replace"))
                        await f.flush()

            # Wait for process to complete
            return_code = await process.wait()

            # Add completion marker
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"\n=== Process completed with exit code {return_code} ===\n")

            # Mark as completed
            self.process_manager.mark_completed(process_id, return_code)

        except Exception as e:
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"\n=== Error: {str(e)} ===\n")
            self.process_manager.mark_completed(process_id, -1)


class BaseBinaryTool(BaseProcessTool):
    """Base class for binary execution tools (like npx, uvx)."""

    @abstractmethod
    def get_binary_name(self) -> str:
        """Get the name of the binary to execute."""
        pass

    @override
    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get command arguments for binary execution.

        Args:
            command: The package or command to run
            **kwargs: Additional arguments (args, flags, etc.)

        Returns:
            List of command arguments
        """
        cmd_args = [self.get_binary_name()]

        # Add any binary-specific flags
        if "flags" in kwargs:
            cmd_args.extend(kwargs["flags"])

        # Add the command/package
        cmd_args.append(command)

        # Add any additional arguments
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
        """Get command arguments for script execution.

        Args:
            command: The script content to execute
            **kwargs: Additional arguments

        Returns:
            List of command arguments
        """
        cmd_args = [self.get_interpreter()]
        cmd_args.extend(self.get_script_flags())

        # For inline scripts, use -c flag
        if not kwargs.get("is_file", False):
            cmd_args.extend(["-c", command])
        else:
            cmd_args.append(command)

        return cmd_args

    @override
    def get_tool_name(self) -> str:
        """Get the tool name (interpreter name by default)."""
        return self.get_interpreter()
