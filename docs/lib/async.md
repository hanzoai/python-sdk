# hanzo-async

High-performance async I/O for Hanzo AI with automatic uvloop configuration.

## Installation

```bash
pip install hanzo-async
```

## Features

- **Automatic uvloop** - 2-4x faster async on macOS/Linux
- **Async file I/O** - Non-blocking file operations
- **Async subprocess** - Non-blocking command execution
- **Consistent API** - Used across all Hanzo packages

## Quick Start

```python
from hanzo_async import (
    read_file, write_file,
    path_exists, mkdir,
    run_command,
    using_uvloop,
)

# Check if using high-performance backend
if using_uvloop():
    print("Using uvloop for 2-4x faster async")

# Async file operations
content = await read_file("/path/to/file.txt")
await write_file("/path/to/output.txt", "content")

# Async path operations
if await path_exists("/path/to/dir"):
    ...

# Async subprocess
stdout, stderr, code = await run_command("ls", "-la")
```

## Loop Configuration

```python
from hanzo_async import configure_loop, using_uvloop, get_loop

# Configure on import (automatic)
configure_loop()

# Check backend
if using_uvloop():
    print("uvloop active")
else:
    print("Using asyncio (Windows or uvloop not installed)")

# Get current loop
loop = get_loop()
```

## File Operations

### Reading Files

```python
from hanzo_async import read_file, read_json, read_lines

# Read text file
content = await read_file("/path/to/file.txt")

# Read JSON file
data = await read_json("/path/to/config.json")

# Read lines
lines = await read_lines("/path/to/file.txt")
```

### Writing Files

```python
from hanzo_async import write_file, write_json, write_lines, append_file

# Write text file
await write_file("/path/to/file.txt", "content")

# Write JSON file
await write_json("/path/to/config.json", {"key": "value"})

# Write lines
await write_lines("/path/to/file.txt", ["line1", "line2"])

# Append to file
await append_file("/path/to/log.txt", "new entry\n")
```

## Path Operations

```python
from hanzo_async import (
    path_exists, is_file, is_dir,
    mkdir, rmdir, unlink,
    stat, listdir, glob,
)

# Check existence
if await path_exists("/path"):
    ...

# Check type
if await is_file("/path/file.txt"):
    ...
if await is_dir("/path/dir"):
    ...

# Create directory
await mkdir("/path/new/dir", parents=True, exist_ok=True)

# Remove
await unlink("/path/file.txt")  # Remove file
await rmdir("/path/dir")         # Remove directory

# List directory
files = await listdir("/path/dir")

# Glob pattern
matches = await glob("/path/**/*.py")

# Get file info
info = await stat("/path/file.txt")
print(f"Size: {info.st_size}, Modified: {info.st_mtime}")
```

## Process Operations

```python
from hanzo_async import run_command, run_shell, check_command

# Run command with arguments
stdout, stderr, code = await run_command("git", "status")

# Run shell command
stdout, stderr, code = await run_shell("ls -la | grep .py")

# Check if command succeeds (raises on failure)
await check_command("make", "build")
```

## API Reference

### Loop Functions

| Function | Description |
|----------|-------------|
| `configure_loop()` | Configure uvloop (automatic on import) |
| `using_uvloop()` | Check if uvloop is active |
| `get_loop()` | Get current event loop |

### File Functions

| Function | Description |
|----------|-------------|
| `read_file(path)` | Read file as string |
| `read_json(path)` | Read and parse JSON file |
| `read_lines(path)` | Read file as list of lines |
| `write_file(path, content)` | Write string to file |
| `write_json(path, data)` | Write data as JSON |
| `write_lines(path, lines)` | Write list of lines |
| `append_file(path, content)` | Append to file |

### Path Functions

| Function | Description |
|----------|-------------|
| `path_exists(path)` | Check if path exists |
| `is_file(path)` | Check if path is a file |
| `is_dir(path)` | Check if path is a directory |
| `mkdir(path, ...)` | Create directory |
| `rmdir(path)` | Remove directory |
| `unlink(path)` | Remove file |
| `stat(path)` | Get file information |
| `listdir(path)` | List directory contents |
| `glob(pattern)` | Find files matching pattern |

### Process Functions

| Function | Description |
|----------|-------------|
| `run_command(*args)` | Run command with arguments |
| `run_shell(cmd)` | Run shell command |
| `check_command(*args)` | Run and raise on failure |

## Platform Support

| Platform | Backend | Performance |
|----------|---------|-------------|
| macOS | uvloop | 2-4x faster |
| Linux | uvloop | 2-4x faster |
| Windows | asyncio | Standard |

## Why uvloop?

uvloop is a fast, drop-in replacement for asyncio's event loop that uses libuv under the hood. It provides:

- **2-4x faster** async operations
- **Lower latency** for I/O bound tasks
- **Better scalability** under high concurrency

The hanzo-async package automatically configures uvloop when available, falling back to asyncio on Windows or when uvloop isn't installed.
