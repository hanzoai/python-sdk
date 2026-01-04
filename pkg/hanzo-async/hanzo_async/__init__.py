"""Hanzo Async - Unified async I/O for Hanzo AI.

High-performance async operations with uvloop backend and asyncio fallback.

Features:
- Automatic uvloop configuration (falls back to asyncio on Windows)
- Async file I/O (read, write, append, exists, mkdir)
- Async path operations (exists, is_file, is_dir, stat)
- Async subprocess execution
- Consistent patterns across all Hanzo packages

Usage:
    from hanzo_async import read_file, write_file, path_exists, run_command
    from hanzo_async import configure_loop, using_uvloop

    # Check if using uvloop
    if using_uvloop():
        print("Using uvloop for high-performance async")

    # Async file operations
    content = await read_file("/path/to/file")
    await write_file("/path/to/file", "content")

    # Async path operations
    if await path_exists("/path/to/file"):
        ...

    # Async subprocess
    stdout, stderr, code = await run_command("ls", "-la")
"""

import sys
import asyncio
from functools import lru_cache

# Track uvloop configuration state
_uvloop_configured = False
_using_uvloop = False


def configure_loop() -> bool:
    """Configure the event loop for high performance.

    Uses uvloop on macOS/Linux, falls back to asyncio on Windows.
    Safe to call multiple times - only configures once.

    Returns:
        True if uvloop is active, False if using asyncio fallback
    """
    global _uvloop_configured, _using_uvloop

    if _uvloop_configured:
        return _using_uvloop

    _uvloop_configured = True

    # Windows doesn't support uvloop
    if sys.platform == "win32":
        _using_uvloop = False
        return False

    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        _using_uvloop = True
        return True
    except ImportError:
        _using_uvloop = False
        return False


def using_uvloop() -> bool:
    """Check if uvloop is active.

    Returns:
        True if using uvloop, False if using asyncio
    """
    if not _uvloop_configured:
        configure_loop()
    return _using_uvloop


def get_loop() -> asyncio.AbstractEventLoop:
    """Get the current event loop, creating if necessary.

    Handles Python 3.10+ deprecation of get_event_loop() in non-async contexts.

    Returns:
        The current event loop
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # Not in async context, create new loop
        if not _uvloop_configured:
            configure_loop()
        return asyncio.new_event_loop()


# Auto-configure on import
configure_loop()

# Export file operations
from hanzo_async.files import (
    read_file,
    read_json,
    write_file,
    write_json,
    append_file,
    read_lines,
    write_lines,
)

# Export path operations
from hanzo_async.paths import (
    path_exists,
    is_file,
    is_dir,
    mkdir,
    rmdir,
    unlink,
    stat,
    listdir,
    glob,
)

# Export process operations
from hanzo_async.process import (
    run_command,
    run_shell,
    check_command,
)

__all__ = [
    # Loop configuration
    "configure_loop",
    "using_uvloop",
    "get_loop",
    # File operations
    "read_file",
    "read_json",
    "write_file",
    "write_json",
    "append_file",
    "read_lines",
    "write_lines",
    # Path operations
    "path_exists",
    "is_file",
    "is_dir",
    "mkdir",
    "rmdir",
    "unlink",
    "stat",
    "listdir",
    "glob",
    # Process operations
    "run_command",
    "run_shell",
    "check_command",
]
