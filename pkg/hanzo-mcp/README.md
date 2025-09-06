# Hanzo Model Context Protocol (MCP)

[![PyPI](https://img.shields.io/pypi/v/hanzo-mcp.svg)](https://pypi.org/project/hanzo-mcp/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo-mcp.svg)](https://pypi.org/project/hanzo-mcp/)

Model Context Protocol implementation for advanced tool use and context management.

## Installation

```bash
pip install hanzo-mcp
```

## Features

- **Tool Management**: Register and manage AI tools
- **File Operations**: Read, write, edit files
- **Code Intelligence**: AST analysis, symbol search
- **Shell Execution**: Run commands safely
- **Agent Delegation**: Recursive agent capabilities
- **Memory Integration**: Persistent context storage
- **Batch Operations**: Execute multiple tools efficiently

## Quick Start

### Basic Usage

```python
from hanzo_mcp import create_mcp_server

# Create MCP server
server = create_mcp_server()

# Register tools
server.register_filesystem_tools()
server.register_shell_tools()
server.register_agent_tools()

# Start server
await server.start()
```

### Tool Categories

#### Filesystem Tools

```python
# Read file
content = await server.tools.read(file_path="/path/to/file.py")

# Write file
await server.tools.write(
    file_path="/path/to/new.py",
    content="print('Hello')"
)

# Edit file
await server.tools.edit(
    file_path="/path/to/file.py",
    old_string="old code",
    new_string="new code"
)

# Multi-edit
await server.tools.multi_edit(
    file_path="/path/to/file.py",
    edits=[
        {"old_string": "foo", "new_string": "bar"},
        {"old_string": "baz", "new_string": "qux"}
    ]
)
```

#### Search Tools

```python
# Unified search (grep + AST + semantic)
results = await server.tools.search(
    pattern="function_name",
    path="/project"
)

# AST-aware search
results = await server.tools.grep_ast(
    pattern="class.*Service",
    path="/src"
)

# Symbol search
symbols = await server.tools.symbols(
    pattern="def test_",
    path="/tests"
)
```

#### Shell Tools

```python
# Run command
result = await server.tools.bash(
    command="ls -la",
    cwd="/project"
)

# Run with auto-backgrounding
result = await server.tools.bash(
    command="python server.py",
    timeout=120000  # Auto-backgrounds after 2 min
)

# Manage processes
processes = await server.tools.process(action="list")
logs = await server.tools.process(
    action="logs",
    id="bash_abc123"
)
```

#### Agent Tools

```python
# Dispatch agent for complex tasks
result = await server.tools.dispatch_agent(
    prompt="Analyze the codebase architecture",
    path="/project"
)

# Network of agents
result = await server.tools.network(
    task="Implement user authentication",
    agents=["architect", "developer", "tester"]
)

# CLI tool integration
result = await server.tools.claude(
    args=["--analyze", "main.py"]
)
```

#### Batch Operations

```python
# Execute multiple tools in parallel
results = await server.tools.batch(
    description="Read multiple files",
    invocations=[
        {"tool_name": "read", "input": {"file_path": "file1.py"}},
        {"tool_name": "read", "input": {"file_path": "file2.py"}},
        {"tool_name": "grep", "input": {"pattern": "TODO"}}
    ]
)
```

## Advanced Features

### Custom Tools

```python
from hanzo_mcp import Tool

class MyCustomTool(Tool):
    name = "my_tool"
    description = "Custom tool"
    
    async def call(self, ctx, **params):
        # Tool implementation
        return "Result"

# Register custom tool
server.register_tool(MyCustomTool())
```

### Permission Management

```python
from hanzo_mcp import PermissionManager

# Create permission manager
pm = PermissionManager()

# Set permission mode
pm.set_mode("review")  # review, auto_approve, auto_deny

# Check permission
allowed = await pm.check_permission(
    tool="write",
    params={"file_path": "/etc/passwd"}
)
```

### Context Management

```python
from hanzo_mcp import ToolContext

# Create context
ctx = ToolContext(
    cwd="/project",
    env={"API_KEY": "secret"},
    timeout=30000
)

# Use with tools
result = await tool.call(ctx, **params)
```

## Configuration

### Environment Variables

```bash
# API keys for agent tools
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Tool settings
MCP_PERMISSION_MODE=review
MCP_MAX_FILE_SIZE=10485760
MCP_TIMEOUT=120000

# Search settings
MCP_SEARCH_IGNORE=node_modules,*.pyc
MCP_SEARCH_MAX_RESULTS=100
```

### Configuration File

```yaml
tools:
  filesystem:
    enabled: true
    max_file_size: 10MB
    allowed_paths:
      - /home/user/projects
      - /tmp
    
  shell:
    enabled: true
    timeout: 120000
    auto_background: true
    
  agent:
    enabled: true
    models:
      - claude-3-opus
      - gpt-4
    
  search:
    ignore_patterns:
      - node_modules
      - "*.pyc"
      - .git
    max_results: 100

permissions:
  mode: review  # review, auto_approve, auto_deny
  whitelist:
    - read
    - grep
    - search
  blacklist:
    - rm
    - sudo
```

## CLI Usage

### Installation to Claude Desktop

```bash
# Install to Claude Desktop
hanzo-mcp install-desktop

# Serve MCP
hanzo-mcp serve --port 3000
```

### Standalone Server

```bash
# Start MCP server
hanzo-mcp serve

# With custom config
hanzo-mcp serve --config mcp-config.yaml

# With specific tools
hanzo-mcp serve --tools filesystem,shell,agent
```

## Development

### Setup

```bash
cd pkg/hanzo-mcp
uv sync --all-extras
```

### Testing

```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/ -m integration

# With coverage
pytest tests/ --cov=hanzo_mcp
```

### Building

```bash
uv build
```

## Architecture

### Tool Categories

- **Filesystem**: File operations (read, write, edit)
- **Search**: Code search (grep, AST, semantic)
- **Shell**: Command execution and process management
- **Agent**: AI agent delegation and orchestration
- **Memory**: Context and knowledge persistence
- **Config**: Configuration management
- **LLM**: Direct LLM interactions

### Security

- Permission system for dangerous operations
- Path validation and sandboxing
- Command injection protection
- Rate limiting on operations
- Audit logging

## License

Apache License 2.0