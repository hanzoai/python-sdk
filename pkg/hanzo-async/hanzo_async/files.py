"""Async file operations.

Provides non-blocking file I/O using aiofiles.
All operations are fully async and safe for use in event loops.
"""

import json
from typing import Any, List, Optional, Union
from pathlib import Path

import aiofiles
import aiofiles.os


async def read_file(
    path: Union[str, Path],
    encoding: str = "utf-8",
    errors: str = "replace",
) -> str:
    """Read entire file content asynchronously.

    Args:
        path: Path to file
        encoding: Text encoding (default: utf-8)
        errors: Error handling mode (default: replace)

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    async with aiofiles.open(path, "r", encoding=encoding, errors=errors) as f:
        return await f.read()


async def read_json(
    path: Union[str, Path],
    encoding: str = "utf-8",
) -> Any:
    """Read and parse JSON file asynchronously.

    Args:
        path: Path to JSON file
        encoding: Text encoding (default: utf-8)

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    content = await read_file(path, encoding=encoding)
    return json.loads(content)


async def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    mkdir_parents: bool = True,
) -> None:
    """Write content to file asynchronously.

    Args:
        path: Path to file
        content: Content to write
        encoding: Text encoding (default: utf-8)
        mkdir_parents: Create parent directories if needed (default: True)

    Raises:
        PermissionError: If file can't be written
    """
    path = Path(path)
    if mkdir_parents:
        from hanzo_async.paths import mkdir
        await mkdir(path.parent, parents=True, exist_ok=True)

    async with aiofiles.open(path, "w", encoding=encoding) as f:
        await f.write(content)


async def write_json(
    path: Union[str, Path],
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    mkdir_parents: bool = True,
) -> None:
    """Write data as JSON file asynchronously.

    Args:
        path: Path to file
        data: Data to serialize as JSON
        encoding: Text encoding (default: utf-8)
        indent: JSON indentation (default: 2)
        mkdir_parents: Create parent directories if needed (default: True)

    Raises:
        TypeError: If data is not JSON serializable
        PermissionError: If file can't be written
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    await write_file(path, content, encoding=encoding, mkdir_parents=mkdir_parents)


async def append_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    mkdir_parents: bool = True,
) -> None:
    """Append content to file asynchronously.

    Args:
        path: Path to file
        content: Content to append
        encoding: Text encoding (default: utf-8)
        mkdir_parents: Create parent directories if needed (default: True)

    Raises:
        PermissionError: If file can't be written
    """
    path = Path(path)
    if mkdir_parents:
        from hanzo_async.paths import mkdir
        await mkdir(path.parent, parents=True, exist_ok=True)

    async with aiofiles.open(path, "a", encoding=encoding) as f:
        await f.write(content)


async def read_lines(
    path: Union[str, Path],
    encoding: str = "utf-8",
    strip: bool = True,
) -> List[str]:
    """Read file lines asynchronously.

    Args:
        path: Path to file
        encoding: Text encoding (default: utf-8)
        strip: Strip whitespace from lines (default: True)

    Returns:
        List of lines

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    content = await read_file(path, encoding=encoding)
    lines = content.splitlines()
    if strip:
        lines = [line.strip() for line in lines]
    return lines


async def write_lines(
    path: Union[str, Path],
    lines: List[str],
    encoding: str = "utf-8",
    mkdir_parents: bool = True,
) -> None:
    """Write lines to file asynchronously.

    Args:
        path: Path to file
        lines: Lines to write
        encoding: Text encoding (default: utf-8)
        mkdir_parents: Create parent directories if needed (default: True)

    Raises:
        PermissionError: If file can't be written
    """
    content = "\n".join(lines) + "\n"
    await write_file(path, content, encoding=encoding, mkdir_parents=mkdir_parents)


async def read_bytes(path: Union[str, Path]) -> bytes:
    """Read file as bytes asynchronously.

    Args:
        path: Path to file

    Returns:
        File content as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    async with aiofiles.open(path, "rb") as f:
        return await f.read()


async def write_bytes(
    path: Union[str, Path],
    content: bytes,
    mkdir_parents: bool = True,
) -> None:
    """Write bytes to file asynchronously.

    Args:
        path: Path to file
        content: Bytes to write
        mkdir_parents: Create parent directories if needed (default: True)

    Raises:
        PermissionError: If file can't be written
    """
    path = Path(path)
    if mkdir_parents:
        from hanzo_async.paths import mkdir
        await mkdir(path.parent, parents=True, exist_ok=True)

    async with aiofiles.open(path, "wb") as f:
        await f.write(content)
