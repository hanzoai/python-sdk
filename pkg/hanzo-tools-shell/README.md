# hanzo-tools-shell

Shell execution tools for Hanzo MCP with DAG support and Shellflow DSL.

## Installation

```bash
pip install hanzo-tools-shell
```

## Tools

### dag - DAG Execution Engine
Execute commands with directed acyclic graph semantics.

```python
# Serial execution (default)
dag(["ls", "pwd", "git status"])

# Parallel execution
dag(["npm install", "cargo build"], parallel=True)

# Mixed DAG with parallel blocks
dag([
    "mkdir -p dist",
    {"parallel": ["cp a.txt dist/", "cp b.txt dist/"]},
    "zip -r out.zip dist/"
])

# Tool invocations
dag([{"tool": "search", "input": {"pattern": "TODO"}}])

# Named nodes with dependencies
dag([
    {"id": "build", "run": "make build"},
    {"id": "test", "run": "make test", "after": ["build"]},
])
```

### zsh - Primary Shell with Shellflow DSL
Execute shell commands with optional Shellflow syntax.

```python
# Simple command
zsh("ls -la")

# Shellflow DSL syntax
zsh("mkdir dist ; { cp a dist/ & cp b dist/ } ; zip out")

# With shell parameter
zsh("echo $BASH_VERSION", shell="bash")
```

**Shellflow Syntax:**
- `A ; B` - Sequential execution
- `{ A & B }` - Parallel execution
- `A ; { B & C } ; D` - Mixed DAG

### ps - Process Management
Monitor and control background processes.

```python
ps()                     # List all processes
ps(id="abc123")          # Get specific process
ps(kill="abc123")        # Kill process (SIGTERM)
ps(logs="abc123", n=50)  # Last 50 lines of output
```

### Additional Tools
- **shell** - Smart shell (zsh > bash fallback)
- **bash** - Explicit bash execution
- **npx** - Node package execution with auto-backgrounding
- **uvx** - Python package execution with auto-backgrounding
- **open** - Open files/URLs in system apps
- **curl** - HTTP client without shell escaping issues
- **jq** - JSON processor
- **wget** - File/site downloads

## Auto-Backgrounding

Commands that exceed the timeout (default 60s) are automatically backgrounded:

```python
dag(["long-running-command"], timeout=30)
# If command exceeds 30s, it continues in background
# Use ps --logs <id> to view output
```

## Performance

Shellflow DSL is optimized for high throughput:
- Simple commands: ~7M ops/sec
- Sequential: ~2.2M ops/sec  
- Mixed DAG: ~100k ops/sec

## License

MIT
