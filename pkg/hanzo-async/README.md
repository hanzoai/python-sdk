# hanzo-async

Unified async I/O for Hanzo AI - high-performance with uvloop fallback.

## Features

- **Automatic uvloop configuration** - Falls back to asyncio on Windows
- **Async file I/O** - Read, write, append with aiofiles
- **Async path operations** - exists, is_file, mkdir, etc.
- **Async subprocess execution** - run_command, run_shell
- **Consistent patterns** - Same API across all Hanzo packages

## Installation

```bash
pip install hanzo-async

# With uvloop support (recommended for macOS/Linux)
pip install hanzo-async[uvloop]
```

## Quick Start

```python
from hanzo_async import (
    # Loop configuration
    configure_loop,
    using_uvloop,

    # File operations
    read_file,
    write_file,
    read_json,
    write_json,

    # Path operations
    path_exists,
    is_file,
    is_dir,
    mkdir,

    # Process operations
    run_command,
    run_shell,
)

# Check if using uvloop
if using_uvloop():
    print("Using uvloop for high-performance async")

# Async file operations
async def example():
    # Read/write files
    content = await read_file("/path/to/file.txt")
    await write_file("/path/to/output.txt", content)

    # JSON handling
    data = await read_json("/path/to/config.json")
    data["updated"] = True
    await write_json("/path/to/config.json", data)

    # Path operations
    if await path_exists("/path/to/file"):
        if await is_file("/path/to/file"):
            await unlink("/path/to/file")

    await mkdir("/path/to/new/dir", parents=True, exist_ok=True)

    # Run commands
    stdout, stderr, code = await run_command("ls", "-la")
    stdout, stderr, code = await run_shell("echo $HOME && pwd")
```

## API Reference

### Loop Configuration

- `configure_loop()` - Configure uvloop (auto-called on import)
- `using_uvloop()` - Check if uvloop is active
- `get_loop()` - Get current event loop

### File Operations

- `read_file(path)` - Read file content
- `write_file(path, content)` - Write content to file
- `append_file(path, content)` - Append to file
- `read_json(path)` - Read and parse JSON
- `write_json(path, data)` - Write JSON to file
- `read_lines(path)` - Read file as lines
- `write_lines(path, lines)` - Write lines to file
- `read_bytes(path)` - Read file as bytes
- `write_bytes(path, content)` - Write bytes to file

### Path Operations

- `path_exists(path)` - Check if path exists
- `is_file(path)` - Check if path is file
- `is_dir(path)` - Check if path is directory
- `mkdir(path, parents=False, exist_ok=False)` - Create directory
- `rmdir(path)` - Remove empty directory
- `unlink(path, missing_ok=False)` - Remove file
- `stat(path)` - Get file/directory stats
- `listdir(path)` - List directory contents
- `glob(pattern, root_dir=None, recursive=False)` - Find files
- `rename(src, dst)` - Rename/move file
- `copy(src, dst)` - Copy file
- `copytree(src, dst)` - Copy directory tree
- `rmtree(path)` - Remove directory tree

### Process Operations

- `run_command(*args)` - Run command with args
- `run_shell(command)` - Run shell command
- `check_command(command)` - Check if command exists
- `which(command)` - Find command path
- `start_background(*args)` - Start background process

## Why hanzo-async?

1. **Consistent async patterns** - All Hanzo packages use the same I/O patterns
2. **High performance** - uvloop provides 2-4x faster async on Unix
3. **Automatic fallback** - Works on Windows with standard asyncio
4. **No event loop blocking** - All operations are truly async
5. **Easy to use** - Simple function-based API

## License

MIT
