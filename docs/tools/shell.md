# hanzo-tools-shell

Unified command execution with DAG support, auto-backgrounding, and process management. The shell toolkit provides the `cmd`, `zsh`, `bash`, and `ps` tools.

## Installation

```bash
pip install hanzo-tools-shell
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-shell` provides:

- **cmd** - Unified command execution with DAG support
- **zsh** / **bash** / **shell** - Shell-specific execution
- **ps** - Process management (list, kill, logs)
- **npx** / **uvx** - Package runner tools
- **open** - Platform-aware file/URL opener

## Key Features

### Auto-Backgrounding

Commands automatically background after 30 seconds (configurable):

```python
# Long-running command auto-backgrounds
cmd("npm run build")  # If takes >30s, continues in background

# Check status later
ps()  # List all background processes
ps(logs="cmd_abc123")  # View output
ps(kill="cmd_abc123")  # Stop process
```

### DAG Execution

Execute commands with dependency graphs:

```python
# Sequential (default)
cmd(["mkdir dist", "cp files dist/", "zip -r out.zip dist/"])

# Parallel
cmd(["npm install", "cargo build"], parallel=True)

# Mixed DAG with dependencies
cmd([
    "mkdir -p dist",
    {"parallel": ["cp a.txt dist/", "cp b.txt dist/"]},
    "zip -r out.zip dist/"
])
```

## Tools Reference

### cmd

The primary command execution tool:

```python
# Simple command
cmd("ls -la")

# Sequential commands
cmd(["git status", "git diff", "git log -5"])

# Parallel execution
cmd(["npm install", "pip install -r requirements.txt"], parallel=True)

# Mixed DAG
cmd([
    "mkdir -p dist",
    {"parallel": ["build-frontend", "build-backend"]},
    "deploy"
])

# With options
cmd(
    "npm test",
    timeout=120,      # Command timeout in seconds
    cwd="/project",   # Working directory
    env={"NODE_ENV": "test"},  # Environment variables
    quiet=True,       # Suppress stdout
    strict=True       # Stop on first error
)
```

### zsh / bash / shell

Shell-specific wrappers around `cmd`:

```python
# Use specific shell
zsh("echo $SHELL")  # Uses zsh
bash("echo $SHELL")  # Uses bash
shell("echo $SHELL")  # Auto-detects: zsh > bash > sh

# Same options as cmd
zsh(["cmd1", "cmd2"], parallel=True, timeout=60)
```

### ps

Process management for background commands:

```python
# List all background processes
ps()

# Get specific process info
ps(id="cmd_abc123")

# View process output (last 100 lines by default)
ps(logs="cmd_abc123")
ps(logs="cmd_abc123", n=50)  # Last 50 lines

# Kill process
ps(kill="cmd_abc123")  # SIGTERM (default)
ps(kill="cmd_abc123", sig=9)  # SIGKILL
```

### npx / uvx

Package runners with auto-backgrounding:

```python
# Run npm packages
npx("create-react-app my-app")
npx("http-server -p 8080")  # Auto-backgrounds if long-running

# Run Python packages
uvx("ruff check .")
uvx("mkdocs serve")  # Auto-backgrounds if long-running
```

### open

Platform-aware opener for files and URLs:

```python
# Open URLs
open("https://example.com")

# Open files with default application
open("./document.pdf")
open("/path/to/image.png")
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_AUTO_BACKGROUND_TIMEOUT` | `45` | Seconds before auto-backgrounding (0 to disable) |
| `HANZO_DEFAULT_SHELL` | `zsh` | Default shell for execution |

### Timeout Configuration

```python
# Disable auto-backgrounding for a command
cmd("long-running-command", timeout=0)

# Set global timeout via environment
import os
os.environ["HANZO_AUTO_BACKGROUND_TIMEOUT"] = "120"  # 2 minutes
```

## Examples

### Build Pipeline

```python
# Parallel build with sequential deploy
cmd([
    {"parallel": [
        "npm run build:frontend",
        "npm run build:backend",
        "npm run build:docs"
    ]},
    "npm run test",
    "npm run deploy"
])
```

### Development Server

```python
# Start dev server (auto-backgrounds)
cmd("npm run dev")

# Later, check status
ps()
# Output: cmd_abc123 | running | npm run dev | started 5m ago

# View logs
ps(logs="cmd_abc123")

# Stop when done
ps(kill="cmd_abc123")
```

### Tool Invocation in DAG

```python
# Mix shell commands with tool calls
cmd([
    "git pull origin main",
    {"tool": "search", "input": {"pattern": "TODO"}},
    "npm test"
])
```

### Parallel File Operations

```python
# Process multiple files in parallel
cmd([
    ["process file1.txt", "process file2.txt", "process file3.txt"]
], parallel=True)
```

## Architecture

### ShellExecutor

Single async execution engine for all shell tools:

```
CmdTool (cmd)           # Unified execution graph (DAG)
    ├── ZshTool (zsh)   # Thin shim: shell=zsh
    ├── BashTool (bash) # Thin shim: shell=bash
    └── ShellTool       # Smart shim: zsh > bash > sh

ShellExecutor (singleton)
    └── ProcessManager (singleton)
        └── ps tool (process listing/kill/logs)
```

### Process Lifecycle

1. Command starts with `asyncio.create_subprocess_exec`
2. Wait for completion with configured timeout
3. If timeout reached: register with ProcessManager, continue in background
4. User can monitor with `ps --logs <id>` or stop with `ps --kill <id>`

## Error Handling

```python
# Strict mode: stop on first error
cmd(["cmd1", "cmd2", "cmd3"], strict=True)

# Default: continue on errors, report all
cmd(["cmd1", "cmd2", "cmd3"])  # Returns combined output with errors

# Check exit codes in response
result = cmd("might-fail")
if "exit code" in result.lower():
    # Handle error
    ...
```

## Best Practices

1. **Use DAG for dependencies**: Let the executor handle ordering
2. **Parallelize independent operations**: Use `parallel=True` for speed
3. **Set appropriate timeouts**: Avoid blocking on hung processes
4. **Use `ps` for long tasks**: Don't wait for builds, check later
5. **Prefer `cmd` over raw shell**: Better error handling and logging
