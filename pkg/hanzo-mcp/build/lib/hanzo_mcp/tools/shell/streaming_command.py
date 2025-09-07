"""Streaming command execution with disk-based logging and session management."""

import os
import json
import time
import uuid
import shutil
import asyncio
import subprocess
from typing import Any, Dict, List, Union, Optional
from pathlib import Path
from datetime import datetime, timedelta

from hanzo_mcp.tools.shell.base_process import BaseProcessTool


class StreamingCommandTool(BaseProcessTool):
    """Execute commands with disk-based streaming and session persistence.

    Features:
    - All output streamed directly to disk (no memory usage)
    - Session-based organization of logs
    - Easy continuation/resumption of output
    - Forgiving parameter handling for AI usage
    - Automatic session detection from MCP context
    """

    name = "streaming_command"
    description = "Run commands with disk-based output streaming and easy resumption"

    # Base directory for all session data
    SESSION_BASE_DIR = Path.home() / ".hanzo" / "sessions"

    # Chunk size for streaming (25k tokens ≈ 100KB)
    STREAM_CHUNK_SIZE = 100_000

    # Session retention
    SESSION_RETENTION_DAYS = 30

    def __init__(self):
        """Initialize the streaming command tool."""
        super().__init__()
        self.session_id = self._get_or_create_session()
        self.session_dir = self.SESSION_BASE_DIR / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.commands_dir = self.session_dir / "commands"
        self.commands_dir.mkdir(exist_ok=True)

        # Session metadata file
        self.session_meta_file = self.session_dir / "session.json"
        self._update_session_metadata()

        # Cleanup old sessions on init
        self._cleanup_old_sessions()

    def _get_or_create_session(self) -> str:
        """Get session ID from MCP context or create a new one.

        Returns:
            Session ID string
        """
        # Try to get from environment (MCP might set this)
        session_id = os.environ.get("MCP_SESSION_ID")

        if not session_id:
            # Try to get from Claude Desktop session marker
            claude_session = os.environ.get("CLAUDE_SESSION_ID")
            if claude_session:
                session_id = f"claude_{claude_session}"
            else:
                # Generate new session ID with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_id = f"session_{timestamp}_{uuid.uuid4().hex[:8]}"

        return session_id

    def _update_session_metadata(self) -> None:
        """Update session metadata file."""
        metadata = {
            "session_id": self.session_id,
            "created": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "mcp_context": {
                "session_id": os.environ.get("MCP_SESSION_ID"),
                "claude_session": os.environ.get("CLAUDE_SESSION_ID"),
                "user": os.environ.get("USER"),
            },
        }

        # Merge with existing metadata if present
        if self.session_meta_file.exists():
            try:
                with open(self.session_meta_file, "r") as f:
                    existing = json.load(f)
                    metadata["created"] = existing.get("created", metadata["created"])
            except Exception:
                pass

        with open(self.session_meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _cleanup_old_sessions(self) -> None:
        """Remove sessions older than retention period."""
        if not self.SESSION_BASE_DIR.exists():
            return

        cutoff = datetime.now() - timedelta(days=self.SESSION_RETENTION_DAYS)

        for session_dir in self.SESSION_BASE_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            meta_file = session_dir / "session.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r") as f:
                        meta = json.load(f)
                    last_accessed = datetime.fromisoformat(
                        meta.get("last_accessed", "")
                    )
                    if last_accessed < cutoff:
                        shutil.rmtree(session_dir)
                except Exception:
                    # If we can't read metadata, check directory mtime
                    if datetime.fromtimestamp(session_dir.stat().st_mtime) < cutoff:
                        shutil.rmtree(session_dir)

    def _normalize_command_ref(self, ref: Union[str, int, None]) -> Optional[str]:
        """Normalize various command reference formats.

        Args:
            ref: Command reference - can be:
                - Full command ID (UUID)
                - Short ID (first 8 chars)
                - Index number (1, 2, 3...)
                - "last" or "latest"
                - None

        Returns:
            Full command ID or None
        """
        if not ref:
            return None

        ref_str = str(ref).strip().lower()

        # Handle special cases
        if ref_str in ["last", "latest", "recent"]:
            # Get most recent command
            commands = list(self.commands_dir.glob("*/metadata.json"))
            if not commands:
                return None
            latest = max(commands, key=lambda p: p.stat().st_mtime)
            return latest.parent.name

        # Handle numeric index (1-based for user friendliness)
        if ref_str.isdigit():
            index = int(ref_str) - 1
            commands = sorted(
                self.commands_dir.glob("*/metadata.json"),
                key=lambda p: p.stat().st_mtime,
            )
            if 0 <= index < len(commands):
                return commands[index].parent.name
            return None

        # Handle short ID (first 8 chars)
        if len(ref_str) >= 8:
            # Could be short or full ID
            for cmd_dir in self.commands_dir.iterdir():
                if cmd_dir.name.startswith(ref_str):
                    return cmd_dir.name

        return None

    async def call(self, ctx: Any, **kwargs) -> Dict[str, Any]:
        """MCP tool entry point.

        Args:
            ctx: MCP context
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        return await self.run(**kwargs)

    async def run(
        self,
        command: Optional[str] = None,
        cmd: Optional[str] = None,  # Alias for command
        working_dir: Optional[str] = None,
        cwd: Optional[str] = None,  # Alias for working_dir
        timeout: Optional[Union[int, str]] = None,
        continue_from: Optional[Union[str, int]] = None,
        resume: Optional[Union[str, int]] = None,  # Alias for continue_from
        from_byte: Optional[Union[int, str]] = None,
        chunk_size: Optional[Union[int, str]] = None,
    ) -> Dict[str, Any]:
        """Execute or continue reading a command with maximum forgiveness.

        Args:
            command/cmd: The command to execute (either works)
            working_dir/cwd: Directory to run in (either works)
            timeout: Timeout in seconds (accepts int or string)
            continue_from/resume: Continue reading output from a command
            from_byte: Specific byte position to read from
            chunk_size: Custom chunk size for this read

        Returns:
            Command output with metadata for easy continuation
        """
        # Normalize parameters for maximum forgiveness
        command = command or cmd
        working_dir = working_dir or cwd
        continue_from = continue_from or resume

        # Convert string numbers to int
        if isinstance(timeout, str) and timeout.isdigit():
            timeout = int(timeout)
        if isinstance(from_byte, str) and from_byte.isdigit():
            from_byte = int(from_byte)
        if isinstance(chunk_size, str) and chunk_size.isdigit():
            chunk_size = int(chunk_size)

        chunk_size = chunk_size or self.STREAM_CHUNK_SIZE

        # Handle continuation
        if continue_from:
            return await self._continue_reading(continue_from, from_byte, chunk_size)

        # Need a command for new execution
        if not command:
            return {
                "error": "No command provided. Use 'command' or 'cmd' parameter.",
                "hint": "To continue a previous command, use 'continue_from' with command ID or number.",
                "recent_commands": await self._get_recent_commands(),
            }

        # Execute new command
        return await self._execute_new_command(
            command, working_dir, timeout, chunk_size
        )

    async def _execute_new_command(
        self,
        command: str,
        working_dir: Optional[str],
        timeout: Optional[int],
        chunk_size: int,
    ) -> Dict[str, Any]:
        """Execute a new command with disk-based streaming."""
        # Create command directory
        cmd_id = str(uuid.uuid4())
        cmd_dir = self.commands_dir / cmd_id
        cmd_dir.mkdir()

        # File paths
        output_file = cmd_dir / "output.log"
        error_file = cmd_dir / "error.log"
        metadata_file = cmd_dir / "metadata.json"

        # Save metadata
        metadata = {
            "command_id": cmd_id,
            "command": command,
            "working_dir": working_dir or os.getcwd(),
            "start_time": datetime.now().isoformat(),
            "timeout": timeout,
            "status": "running",
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Start process with output redirection
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            # Create tasks for streaming stdout and stderr to files
            async def stream_to_file(stream, file_path):
                """Stream from async pipe to file."""
                with open(file_path, "wb") as f:
                    while True:
                        chunk = await stream.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        f.flush()  # Ensure immediate write

            # Start streaming tasks
            stdout_task = asyncio.create_task(
                stream_to_file(process.stdout, output_file)
            )
            stderr_task = asyncio.create_task(
                stream_to_file(process.stderr, error_file)
            )

            # Wait for initial output or timeout
            start_time = time.time()
            initial_timeout = min(
                timeout or 5, 5
            )  # Wait max 5 seconds for initial output

            while time.time() - start_time < initial_timeout:
                if output_file.stat().st_size > 0 or error_file.stat().st_size > 0:
                    break
                await asyncio.sleep(0.1)

            # Read initial chunk
            output_content = ""
            error_content = ""

            if output_file.exists() and output_file.stat().st_size > 0:
                with open(output_file, "r", errors="replace") as f:
                    output_content = f.read(chunk_size)

            if error_file.exists() and error_file.stat().st_size > 0:
                with open(error_file, "r", errors="replace") as f:
                    error_content = f.read(1000)  # Just first 1KB of errors

            # Check if process completed quickly
            try:
                await asyncio.wait_for(process.wait(), timeout=0.1)
                exit_code = process.returncode
                status = "completed"
            except asyncio.TimeoutError:
                exit_code = None
                status = "running"

            # Update metadata
            metadata["status"] = status
            if exit_code is not None:
                metadata["exit_code"] = exit_code
                metadata["end_time"] = datetime.now().isoformat()

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Build response
            result = {
                "command_id": cmd_id,
                "short_id": cmd_id[:8],
                "command": command,
                "output": output_content,
                "status": status,
                "bytes_read": len(output_content),
                "session_path": str(cmd_dir),
            }

            if error_content:
                result["stderr"] = error_content

            if exit_code is not None:
                result["exit_code"] = exit_code

            # Add continuation info if more output available
            total_size = output_file.stat().st_size
            if total_size > len(output_content) or status == "running":
                result["has_more"] = True
                result["total_bytes"] = total_size
                result["continue_hints"] = [
                    f"continue_from='{cmd_id[:8]}'",
                    f"resume='last'",
                    f"continue_from={cmd_id}",
                ]
                result["message"] = (
                    f"Command {'is still running' if status == 'running' else 'has more output'}. "
                    f"Use any of: {', '.join(result['continue_hints'])}"
                )

            # Ensure tasks complete
            if status == "completed":
                await stdout_task
                await stderr_task

            return result

        except Exception as e:
            # Update metadata with error
            metadata["status"] = "error"
            metadata["error"] = str(e)
            metadata["end_time"] = datetime.now().isoformat()

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return {
                "error": str(e),
                "command_id": cmd_id,
                "short_id": cmd_id[:8],
                "command": command,
            }

    async def _continue_reading(
        self,
        ref: Union[str, int],
        from_byte: Optional[int],
        chunk_size: int,
    ) -> Dict[str, Any]:
        """Continue reading output from a previous command."""
        # Normalize reference
        cmd_id = self._normalize_command_ref(ref)

        if not cmd_id:
            return {
                "error": f"Command not found: {ref}",
                "hint": "Use 'list' to see available commands",
                "recent_commands": await self._get_recent_commands(),
            }

        cmd_dir = self.commands_dir / cmd_id
        if not cmd_dir.exists():
            return {"error": f"Command directory not found: {cmd_id}"}

        # Load metadata
        metadata_file = cmd_dir / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Determine start position
        output_file = cmd_dir / "output.log"
        if not output_file.exists():
            return {"error": "No output file found"}

        # If no from_byte specified, read from where we left off
        if from_byte is None:
            # Try to determine from previous reads (could track this)
            from_byte = 0  # For now, start from beginning if not specified

        # Read chunk
        try:
            with open(output_file, "r", errors="replace") as f:
                f.seek(from_byte)
                content = f.read(chunk_size)
                new_position = f.tell()
                file_size = output_file.stat().st_size

            # Check if process is still running
            status = metadata.get("status", "unknown")

            # Build response
            result = {
                "command_id": cmd_id,
                "short_id": cmd_id[:8],
                "command": metadata["command"],
                "output": content,
                "status": status,
                "bytes_read": len(content),
                "read_from": from_byte,
                "read_to": new_position,
                "total_bytes": file_size,
            }

            # Add stderr if needed
            error_file = cmd_dir / "error.log"
            if error_file.exists() and error_file.stat().st_size > 0:
                with open(error_file, "r", errors="replace") as f:
                    result["stderr"] = f.read(1000)

            # Add continuation info
            if new_position < file_size or status == "running":
                result["has_more"] = True
                result["continue_hints"] = [
                    f"continue_from='{cmd_id[:8]}' from_byte={new_position}",
                    f"resume='last' from_byte={new_position}",
                ]
                result["message"] = (
                    f"Read {len(content)} bytes. "
                    f"{file_size - new_position} bytes remaining. "
                    f"Use: {result['continue_hints'][0]}"
                )

            return result

        except Exception as e:
            return {"error": f"Error reading output: {str(e)}"}

    async def _get_recent_commands(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get list of recent commands for hints."""
        commands = []

        for cmd_dir in sorted(
            self.commands_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )[:limit]:
            try:
                with open(cmd_dir / "metadata.json", "r") as f:
                    meta = json.load(f)

                output_size = 0
                output_file = cmd_dir / "output.log"
                if output_file.exists():
                    output_size = output_file.stat().st_size

                commands.append(
                    {
                        "id": meta["command_id"][:8],
                        "command": (
                            meta["command"][:50] + "..."
                            if len(meta["command"]) > 50
                            else meta["command"]
                        ),
                        "status": meta.get("status", "unknown"),
                        "output_size": output_size,
                        "time": meta.get("start_time", ""),
                    }
                )
            except Exception:
                continue

        return commands

    async def list(self, limit: Optional[int] = 10) -> Dict[str, Any]:
        """List recent commands in this session.

        Args:
            limit: Maximum number of commands to show

        Returns:
            List of recent commands with details
        """
        commands = await self._get_recent_commands(limit or 10)

        return {
            "session_id": self.session_id,
            "session_path": str(self.session_dir),
            "commands": commands,
            "hint": "Use continue_from='<id>' or resume='last' to read output",
        }

    async def tail(
        self,
        ref: Optional[Union[str, int]] = None,
        lines: Optional[int] = 20,
    ) -> Dict[str, Any]:
        """Get the tail of a command's output (like 'tail -f').

        Args:
            ref: Command reference (defaults to 'last')
            lines: Number of lines to show

        Returns:
            Last N lines of output
        """
        ref = ref or "last"
        cmd_id = self._normalize_command_ref(ref)

        if not cmd_id:
            return {"error": f"Command not found: {ref}"}

        output_file = self.commands_dir / cmd_id / "output.log"
        if not output_file.exists():
            return {"error": "No output file found"}

        try:
            # Use tail command for efficiency
            result = subprocess.run(
                ["tail", "-n", str(lines or 20), str(output_file)],
                capture_output=True,
                text=True,
            )

            return {
                "command_id": cmd_id[:8],
                "output": result.stdout,
                "lines": lines,
            }
        except Exception as e:
            return {"error": f"Error tailing output: {str(e)}"}

    def get_params_schema(self) -> Dict[str, Any]:
        """Get parameter schema - very forgiving."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute (alias: 'cmd')",
                },
                "cmd": {
                    "type": "string",
                    "description": "Alias for 'command'",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (alias: 'cwd')",
                },
                "cwd": {
                    "type": "string",
                    "description": "Alias for 'working_dir'",
                },
                "timeout": {
                    "type": ["integer", "string"],
                    "description": "Timeout in seconds",
                },
                "continue_from": {
                    "type": ["string", "integer"],
                    "description": "Continue reading from command (ID, number, or 'last')",
                },
                "resume": {
                    "type": ["string", "integer"],
                    "description": "Alias for 'continue_from'",
                },
                "from_byte": {
                    "type": ["integer", "string"],
                    "description": "Byte position to read from",
                },
                "chunk_size": {
                    "type": ["integer", "string"],
                    "description": "Custom chunk size for reading",
                },
            },
            "required": [],  # No required fields for maximum forgiveness
        }

    def get_command_args(self, command: str, **kwargs) -> List[str]:
        """Get the command arguments for subprocess.

        Args:
            command: The command or script to run
            **kwargs: Additional arguments (not used for shell commands)

        Returns:
            List of command arguments for subprocess
        """
        # For shell commands, we use shell=True, so return the command as-is
        return [command]

    def get_tool_name(self) -> str:
        """Get the name of the tool being used.

        Returns:
            Tool name
        """
        return "streaming_command"
