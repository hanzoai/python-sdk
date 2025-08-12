"""Auto-backgrounding shell execution.

This module provides automatic backgrounding of long-running processes.
Commands that take more than 2 minutes automatically continue in background.
"""

import time
import uuid
import asyncio
from typing import Tuple, Optional
from pathlib import Path

from hanzo_mcp.tools.shell.base_process import ProcessManager


class AutoBackgroundExecutor:
    """Executor that automatically backgrounds long-running processes."""

    # Default timeout before auto-backgrounding (2 minutes)
    DEFAULT_TIMEOUT = 120.0

    def __init__(
        self, process_manager: ProcessManager, timeout: float = DEFAULT_TIMEOUT
    ):
        """Initialize the auto-background executor.

        Args:
            process_manager: Process manager for tracking background processes
            timeout: Timeout in seconds before auto-backgrounding (default: 120s)
        """
        self.process_manager = process_manager
        self.timeout = timeout

    async def execute_with_auto_background(
        self,
        cmd_args: list[str],
        tool_name: str,
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """Execute a command with automatic backgrounding if it takes too long.

        Args:
            cmd_args: Command arguments list
            tool_name: Name of the tool (for process ID generation)
            cwd: Working directory
            env: Environment variables

        Returns:
            Tuple of (output/status, was_backgrounded, process_id)
        """
        # Generate process ID
        process_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

        # Create log file
        log_file = self.process_manager.create_log_file(process_id)

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
            # Create tasks for reading output and waiting for process
            async def read_output():
                """Read output from process."""
                if process.stdout:
                    async for line in process.stdout:
                        line_str = line.decode("utf-8", errors="replace")
                        output_lines.append(line_str)
                        # Also write to log file
                        with open(log_file, "a") as f:
                            f.write(line_str)

            async def wait_for_process():
                """Wait for process to complete."""
                return await process.wait()

            # Run both tasks with timeout
            read_task = asyncio.create_task(read_output())
            wait_task = asyncio.create_task(wait_for_process())

            # Wait for either timeout or completion
            done, pending = await asyncio.wait(
                [read_task, wait_task],
                timeout=self.timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Check if process completed
            if wait_task in done:
                # Process completed within timeout
                return_code = await wait_task
                await read_task  # Ensure all output is read

                # Mark process as completed
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
                # Timeout reached - background the process
                # Cancel the tasks we were waiting on
                for task in pending:
                    task.cancel()

                # Continue reading output in background
                asyncio.create_task(
                    self._background_reader(process, process_id, log_file)
                )

                # Return status message
                elapsed = time.time() - start_time
                partial_output = "".join(output_lines[-50:])  # Last 50 lines

                return (
                    f"Process automatically backgrounded after {elapsed:.1f}s\n"
                    f"Process ID: {process_id}\n"
                    f"Log file: {log_file}\n\n"
                    f"Use 'process --action logs --id {process_id}' to view full output\n"
                    f"Use 'process --action kill --id {process_id}' to stop the process\n\n"
                    f"=== Last output ===\n{partial_output}",
                    True,
                    process_id,
                )

        except Exception as e:
            # Handle errors
            self.process_manager.mark_completed(process_id, -1)
            return f"Error executing command: {str(e)}", False, None

    async def _background_reader(self, process, process_id: str, log_file: Path):
        """Continue reading output from a backgrounded process.

        Args:
            process: The subprocess
            process_id: Process identifier
            log_file: Log file path
        """
        try:
            # Continue reading output
            if process.stdout:
                async for line in process.stdout:
                    with open(log_file, "a") as f:
                        f.write(line.decode("utf-8", errors="replace"))

            # Wait for process to complete
            return_code = await process.wait()

            # Mark as completed
            self.process_manager.mark_completed(process_id, return_code)

            # Add completion marker to log
            with open(log_file, "a") as f:
                f.write(f"\n\n=== Process completed with exit code {return_code} ===\n")

        except Exception as e:
            # Log error
            with open(log_file, "a") as f:
                f.write(f"\n\n=== Background reader error: {str(e)} ===\n")

            self.process_manager.mark_completed(process_id, -1)


def format_auto_background_message(
    process_id: str,
    elapsed_time: float,
    log_file: str,
    partial_output: str = "",
) -> str:
    """Format a user-friendly message for auto-backgrounded processes.

    Args:
        process_id: Process identifier
        elapsed_time: Time elapsed before backgrounding
        log_file: Path to log file
        partial_output: Partial output to show

    Returns:
        Formatted message
    """
    return (
        f"🔄 Process automatically backgrounded after {elapsed_time:.1f}s\n\n"
        f"📋 Process ID: {process_id}\n"
        f"📄 Log file: {log_file}\n\n"
        f"Commands:\n"
        f"  • View logs: process --action logs --id {process_id}\n"
        f"  • Check status: process\n"
        f"  • Stop process: process --action kill --id {process_id}\n"
        f"{chr(10) + '=== Recent output ===' + chr(10) + partial_output if partial_output else ''}"
    )
