"""Async process operations.

Provides non-blocking subprocess execution.
All operations are fully async and safe for use in event loops.
"""

import asyncio
import shutil
from typing import Dict, List, Optional, Tuple, Union


async def run_command(
    *args: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    capture: bool = True,
) -> Tuple[str, str, int]:
    """Run command asynchronously.

    Args:
        *args: Command and arguments
        cwd: Working directory (default: current)
        env: Environment variables to add
        timeout: Timeout in seconds (default: None = no timeout)
        capture: Capture stdout/stderr (default: True)

    Returns:
        Tuple of (stdout, stderr, exit_code)

    Raises:
        asyncio.TimeoutError: If timeout exceeded
        FileNotFoundError: If command not found

    Examples:
        stdout, stderr, code = await run_command("ls", "-la")
        stdout, stderr, code = await run_command("git", "status", cwd="/repo")
    """
    import os

    # Merge environment
    full_env = None
    if env:
        full_env = os.environ.copy()
        full_env.update(env)

    # Create subprocess
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        cwd=cwd,
        env=full_env,
    )

    try:
        if timeout:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        else:
            stdout, stderr = await proc.communicate()

        stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

        return stdout_str, stderr_str, proc.returncode or 0

    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise


async def run_shell(
    command: str,
    shell: Optional[str] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    capture: bool = True,
) -> Tuple[str, str, int]:
    """Run shell command asynchronously.

    Args:
        command: Shell command string
        shell: Shell to use (default: auto-detect zsh > bash > sh)
        cwd: Working directory (default: current)
        env: Environment variables to add
        timeout: Timeout in seconds (default: None = no timeout)
        capture: Capture stdout/stderr (default: True)

    Returns:
        Tuple of (stdout, stderr, exit_code)

    Raises:
        asyncio.TimeoutError: If timeout exceeded
        FileNotFoundError: If shell not found

    Examples:
        stdout, stderr, code = await run_shell("ls -la && pwd")
        stdout, stderr, code = await run_shell("echo $PATH", shell="bash")
    """
    import os

    # Auto-detect shell
    if not shell:
        shell = _detect_shell()

    # Merge environment
    full_env = None
    if env:
        full_env = os.environ.copy()
        full_env.update(env)

    # Create subprocess with shell
    proc = await asyncio.create_subprocess_exec(
        shell, "-c", command,
        stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        cwd=cwd,
        env=full_env,
    )

    try:
        if timeout:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        else:
            stdout, stderr = await proc.communicate()

        stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

        return stdout_str, stderr_str, proc.returncode or 0

    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise


async def check_command(command: str) -> bool:
    """Check if command is available.

    Args:
        command: Command name to check

    Returns:
        True if command is available
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, shutil.which, command)
    return result is not None


def _detect_shell() -> str:
    """Detect the best available shell.

    Returns:
        Path to shell (zsh > bash > fish > sh)
    """
    import os

    # Check environment variable override
    force_shell = os.environ.get("HANZO_SHELL")
    if force_shell:
        return force_shell

    # Shell priority
    shells = ["zsh", "bash", "fish", "sh"]
    search_paths = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/bin",
        "/usr/bin",
    ]

    for shell in shells:
        for prefix in search_paths:
            full_path = f"{prefix}/{shell}"
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        found = shutil.which(shell)
        if found:
            return found

    return "sh"


async def which(command: str) -> Optional[str]:
    """Find command path asynchronously.

    Args:
        command: Command name to find

    Returns:
        Full path to command, or None if not found
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, shutil.which, command)


async def start_background(
    *args: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> asyncio.subprocess.Process:
    """Start a background process.

    Args:
        *args: Command and arguments
        cwd: Working directory (default: current)
        env: Environment variables to add

    Returns:
        asyncio.subprocess.Process handle

    Examples:
        proc = await start_background("python", "server.py")
        # Later...
        proc.terminate()
        await proc.wait()
    """
    import os

    # Merge environment
    full_env = None
    if env:
        full_env = os.environ.copy()
        full_env.update(env)

    return await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=full_env,
    )
