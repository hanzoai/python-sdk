"""Async path operations.

Provides non-blocking path operations using run_in_executor.
All operations are fully async and safe for use in event loops.

Note: Uses ThreadPoolExecutor for filesystem metadata operations (stat, exists,
glob, etc.) rather than aiofiles, as these are fast syscalls that don't benefit
significantly from true async I/O. The executor pattern prevents event loop
blocking while keeping the implementation simple and reliable.

For file content operations (read/write), use hanzo_async.files which wraps aiofiles.
"""

import os
import asyncio
from glob import glob as sync_glob
from typing import List, Optional, Union
from pathlib import Path


async def _run_in_executor(func, *args):
    """Run a sync function in executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


async def path_exists(path: Union[str, Path]) -> bool:
    """Check if path exists asynchronously.

    Args:
        path: Path to check

    Returns:
        True if path exists
    """
    path = Path(path)
    return await _run_in_executor(path.exists)


async def is_file(path: Union[str, Path]) -> bool:
    """Check if path is a file asynchronously.

    Args:
        path: Path to check

    Returns:
        True if path is a file
    """
    path = Path(path)
    return await _run_in_executor(path.is_file)


async def is_dir(path: Union[str, Path]) -> bool:
    """Check if path is a directory asynchronously.

    Args:
        path: Path to check

    Returns:
        True if path is a directory
    """
    path = Path(path)
    return await _run_in_executor(path.is_dir)


async def mkdir(
    path: Union[str, Path],
    parents: bool = False,
    exist_ok: bool = False,
) -> None:
    """Create directory asynchronously.

    Args:
        path: Directory path to create
        parents: Create parent directories (default: False)
        exist_ok: Don't error if exists (default: False)

    Raises:
        FileExistsError: If directory exists and exist_ok=False
        PermissionError: If permission denied
    """
    path = Path(path)

    def _mkdir():
        path.mkdir(parents=parents, exist_ok=exist_ok)

    await _run_in_executor(_mkdir)


async def rmdir(path: Union[str, Path]) -> None:
    """Remove empty directory asynchronously.

    Args:
        path: Directory to remove

    Raises:
        OSError: If directory not empty
        FileNotFoundError: If directory doesn't exist
    """
    path = Path(path)
    await _run_in_executor(path.rmdir)


async def unlink(path: Union[str, Path], missing_ok: bool = False) -> None:
    """Remove file asynchronously.

    Args:
        path: File to remove
        missing_ok: Don't error if file missing (default: False)

    Raises:
        FileNotFoundError: If file doesn't exist and missing_ok=False
    """
    path = Path(path)

    def _unlink():
        path.unlink(missing_ok=missing_ok)

    await _run_in_executor(_unlink)


async def stat(path: Union[str, Path]) -> os.stat_result:
    """Get file/directory stats asynchronously.

    Args:
        path: Path to stat

    Returns:
        os.stat_result with file info

    Raises:
        FileNotFoundError: If path doesn't exist
    """
    path = Path(path)
    return await _run_in_executor(path.stat)


async def listdir(path: Union[str, Path] = ".") -> List[str]:
    """List directory contents asynchronously.

    Args:
        path: Directory to list (default: current directory)

    Returns:
        List of entry names

    Raises:
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
    """
    return await _run_in_executor(os.listdir, str(path))


async def glob(
    pattern: str,
    root_dir: Optional[Union[str, Path]] = None,
    recursive: bool = False,
) -> List[str]:
    """Find files matching pattern asynchronously.

    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.txt")
        root_dir: Root directory for search (default: current directory)
        recursive: Enable ** pattern (default: False)

    Returns:
        List of matching paths
    """
    def _glob():
        if root_dir:
            old_cwd = os.getcwd()
            os.chdir(str(root_dir))
            try:
                return sync_glob(pattern, recursive=recursive)
            finally:
                os.chdir(old_cwd)
        else:
            return sync_glob(pattern, recursive=recursive)

    return await _run_in_executor(_glob)


async def rename(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Rename/move file or directory asynchronously.

    Args:
        src: Source path
        dst: Destination path

    Raises:
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination exists
    """
    src = Path(src)
    dst = Path(dst)
    await _run_in_executor(src.rename, dst)


async def copy(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy file asynchronously.

    Args:
        src: Source file path
        dst: Destination file path

    Raises:
        FileNotFoundError: If source doesn't exist
        PermissionError: If permission denied
    """
    import shutil
    await _run_in_executor(shutil.copy2, str(src), str(dst))


async def copytree(
    src: Union[str, Path],
    dst: Union[str, Path],
    dirs_exist_ok: bool = False,
) -> None:
    """Copy directory tree asynchronously.

    Args:
        src: Source directory path
        dst: Destination directory path
        dirs_exist_ok: Don't error if dst exists (default: False)

    Raises:
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination exists and dirs_exist_ok=False
    """
    import shutil

    def _copytree():
        shutil.copytree(str(src), str(dst), dirs_exist_ok=dirs_exist_ok)

    await _run_in_executor(_copytree)


async def rmtree(path: Union[str, Path], ignore_errors: bool = False) -> None:
    """Remove directory tree asynchronously.

    Args:
        path: Directory to remove
        ignore_errors: Ignore errors during removal (default: False)

    Raises:
        FileNotFoundError: If directory doesn't exist and ignore_errors=False
    """
    import shutil

    def _rmtree():
        shutil.rmtree(str(path), ignore_errors=ignore_errors)

    await _run_in_executor(_rmtree)
