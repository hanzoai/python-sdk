# Shell & Command Tools

The shell tools (`hanzo-tools-shell`) provide comprehensive command execution with auto-backgrounding, DAG support, and process management.

## cmd - Unified Command Execution

The `cmd` tool replaces traditional bash/shell commands with intelligent features:

```python
# Simple command
cmd("ls -la")

# Sequential execution
cmd(["mkdir dist", "cp *.js dist/", "zip -r out.zip dist/"])

# Parallel execution
cmd(["npm install", "cargo build"], parallel=True)

# Mixed DAG
cmd([
    "mkdir dist",
    {"parallel": ["cp a dist/", "cp b dist/"]},
    "zip -r out.zip dist/"
])
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | str | - | Single command to execute |
| `commands` | list | - | List of commands for DAG execution |
| `parallel` | bool | `False` | Run all commands in parallel |
| `timeout` | int | `45` | Per-command timeout in seconds |
| `cwd` | str | - | Working directory |
| `env` | dict | - | Environment variables |
| `shell` | str | `zsh` | Shell to use (zsh, bash, sh) |
| `strict` | bool | `False` | Stop on first error |
| `quiet` | bool | `False` | Suppress stdout |

### DAG Syntax

Execute complex dependency graphs:

```python
# Named steps with dependencies
cmd([
    {"id": "build", "run": "make build"},
    {"id": "test", "run": "make test", "after": ["build"]},
    {"id": "deploy", "run": "make deploy", "after": ["test"]}
])

# Nested parallel blocks
cmd([
    "prepare",
    {"parallel": ["task_a", "task_b", "task_c"]},
    "finalize"
])

# Tool invocations
cmd([{"tool": "search", "input": {"pattern": "TODO"}}])
```

### Auto-Backgrounding

Commands exceeding 30 seconds automatically background:

```python
# This will auto-background after 30s
cmd("npm install")  # Returns immediately with process ID

# Disable auto-backgrounding
export HANZO_AUTO_BACKGROUND_TIMEOUT=0
```

## ps - Process Management

Manage background processes:

```python
# List all processes
ps()

# Get specific process
ps(id="cmd_abc123")

# View output logs
ps(logs="cmd_abc123", n=100)  # Last 100 lines

# Kill process
ps(kill="cmd_abc123")

# Kill with specific signal
ps(kill="cmd_abc123", sig=9)  # SIGKILL
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | - | Process ID to query |
| `logs` | str | - | Process ID to get logs from |
| `kill` | str | - | Process ID to kill |
| `sig` | int | `15` | Signal for kill (15=SIGTERM, 9=SIGKILL) |
| `n` | int | `100` | Number of log lines |

## Shell-Specific Tools

### zsh

Execute in zsh (default, most feature-rich):

```python
zsh("echo $ZSH_VERSION")
zsh(["cmd1", "cmd2"], parallel=True)
```

### bash

Execute in bash:

```python
bash("echo $BASH_VERSION")
bash(["cmd1", "cmd2"])
```

### dash

Execute in dash (POSIX-compliant, fastest):

```python
dash("echo 'fast POSIX shell'")
```

## Package Runners

### npx

Run npm packages:

```python
npx(package="prettier", args="--write .")
npx(package="http-server", args="-p 8080")  # Auto-backgrounds
```

### uvx

Run Python packages:

```python
uvx(package="ruff", args="check .")
uvx(package="mkdocs", args="serve")  # Auto-backgrounds
```

## open

Open files or URLs in default application:

```python
open(path="https://example.com")
open(path="./document.pdf")
open(path="/path/to/image.png")
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_AUTO_BACKGROUND_TIMEOUT` | `45` | Seconds before auto-backgrounding (0 to disable) |
| `HANZO_DEFAULT_SHELL` | `zsh` | Default shell for commands |

### VS Code Settings

```json
{
  "hanzo.mcp.commandTimeout": 45,
  "hanzo.mcp.defaultShell": "zsh"
}
```

## Best Practices

### 1. Use DAGs for Dependencies

```python
# Good - explicit dependencies
cmd([
    {"id": "install", "run": "npm install"},
    {"id": "build", "run": "npm run build", "after": ["install"]}
])

# Avoid - relies on shell chaining
cmd("npm install && npm run build")
```

### 2. Parallel Where Possible

```python
# Good - parallel independent tasks
cmd(["npm install", "cargo build", "go mod download"], parallel=True)

# Avoid - sequential when not needed
cmd("npm install")
cmd("cargo build")
cmd("go mod download")
```

### 3. Handle Long-Running Processes

```python
# Start server (auto-backgrounds)
cmd("npm run dev")

# Check if running
ps()

# Get logs
ps(logs="cmd_xxx")

# Stop when done
ps(kill="cmd_xxx")
```

### 4. Use Environment Variables

```python
cmd(
    "deploy.sh",
    env={
        "NODE_ENV": "production",
        "API_KEY": "${DEPLOY_KEY}"
    }
)
```
