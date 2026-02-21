# hanzo-tools

Core infrastructure and plugin framework for Hanzo AI's modular MCP tool system.

## Install

```bash
pip install hanzo-tools          # Core only
pip install hanzo-tools[dev]     # filesystem, shell, editor, lsp, refactor, todo, reasoning, config
pip install hanzo-tools[ai]      # llm, agent, memory
pip install hanzo-tools[all]     # Everything
```

Individual tool packages can be installed separately:

```bash
pip install hanzo-tools-fs
pip install hanzo-tools-shell
pip install hanzo-tools-browser
pip install hanzo-tools-llm
pip install hanzo-tools-memory
pip install hanzo-tools-editor
pip install hanzo-tools-vector
# ... etc
```

## Usage

### Register all discovered tools

```python
from hanzo_tools import discover_tools, register_all
from mcp.server import FastMCP

mcp = FastMCP("my-server")

# Auto-discover and register all installed tool packages
registered = register_all(mcp)
```

### Register individual tool packages

```python
from hanzo_tools.fs import register_tools as register_fs
from hanzo_tools.shell import register_tools as register_shell

register_fs(mcp, permission_manager)
register_shell(mcp)
```

### Build a custom tool

```python
from typing import Any
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from hanzo_tools.core import BaseTool, ToolRegistry, with_error_logging

class WeatherTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get current weather for a location"

    @with_error_logging("get_weather")
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        location = params["location"]
        return f"Weather in {location}: 72°F, sunny"

    def register(self, mcp_server: FastMCP) -> None:
        @mcp_server.tool()
        async def get_weather(location: str, ctx: MCPContext) -> str:
            """Get current weather for a location."""
            return await self.call(ctx, location=location)

# Register with the MCP server
ToolRegistry.register_tool(mcp, WeatherTool())
```

### Filesystem tools with permissions

```python
from hanzo_tools.core import FileSystemTool, PermissionManager

pm = PermissionManager(
    allowed_paths=["/home/user/projects"],
    deny_patterns=[".git", "node_modules", ".env"],
)

class ReadFileTool(FileSystemTool):
    def __init__(self):
        super().__init__(permission_manager=pm)

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read a file"

    async def call(self, ctx, **params):
        path = params["path"]
        if not self.is_path_allowed(path):
            return "Access denied"
        return open(path).read()

    def register(self, mcp_server):
        @mcp_server.tool()
        async def read_file(path: str, ctx) -> str:
            """Read a file."""
            return await self.call(ctx, path=path)
```

### Decorators

```python
from hanzo_tools.core import auto_timeout, with_error_logging, handle_connection_errors

@auto_timeout("search", timeout=120)
@with_error_logging("search")
@handle_connection_errors
async def search_files(pattern: str, path: str) -> str:
    ...
```

Timeouts are configurable via environment variables:

```bash
HANZO_TIMEOUT_SEARCH=300   # Override search timeout to 5 minutes
HANZO_TIMEOUT_BROWSER=600  # Override browser timeout to 10 minutes
```

### Tool enable/disable

```python
from hanzo_tools.core import ToolRegistry

# Disable a tool at runtime
ToolRegistry.set_tool_enabled("browser", False)

# Check if a tool is enabled
if ToolRegistry.is_tool_enabled("browser"):
    ...
```

Tool states persist to `~/.hanzo/mcp/tool_states.json`.

## Architecture

```
hanzo-tools (core)
├── BaseTool          — Abstract base for all tools
├── FileSystemTool    — Base for filesystem tools with permissions
├── ToolRegistry      — Enable/disable and registration
├── ToolContext       — Execution context with logging/progress
├── PermissionManager — Path-based access control
├── MCPResourceDocument — Structured response formatting
├── auto_timeout      — Configurable async timeouts
├── with_error_logging — Error logging to ~/.hanzo/mcp/logs/
├── handle_connection_errors — Graceful disconnect handling
├── validate_path_parameter  — Path validation
├── discover_tools()  — Plugin discovery via entry points
└── register_all()    — Auto-register all discovered tools

hanzo-tools-fs        — File read/write/search/glob
hanzo-tools-shell     — Shell command execution
hanzo-tools-browser   — Browser automation (Playwright)
hanzo-tools-editor    — Code editing with AST awareness
hanzo-tools-lsp       — Language Server Protocol integration
hanzo-tools-refactor  — Refactoring operations
hanzo-tools-llm       — LLM inference tools
hanzo-tools-agent     — Agent orchestration
hanzo-tools-memory    — Persistent memory/context
hanzo-tools-vector    — Vector DB operations
hanzo-tools-database  — Database query tools
hanzo-tools-jupyter   — Jupyter notebook tools
hanzo-tools-todo      — Task/todo management
hanzo-tools-reasoning — Chain-of-thought reasoning
hanzo-tools-config    — Configuration management
hanzo-tools-mcp       — MCP protocol utilities
hanzo-tools-computer  — Computer use (screen/keyboard)
```

Tool packages register via `importlib.metadata` entry points (`group="hanzo.tools"`), enabling automatic discovery without explicit imports.

## API

### Core Classes

| Class | Purpose |
|-------|---------|
| `BaseTool` | Abstract base — implement `name`, `description`, `call()`, `register()` |
| `FileSystemTool` | Extends BaseTool with `permission_manager` and `validate_path()` |
| `ToolRegistry` | Class-level enable/disable with JSON persistence |
| `ToolContext` | Wraps MCP context with `info()`, `warning()`, `error()`, `progress()` |
| `PermissionManager` | Allowed paths + deny patterns for filesystem access control |
| `MCPResourceDocument` | Response type with `to_json_string()`, `to_readable_string()`, `to_dict()` |
| `ValidationResult` | Boolean result with optional error message |

### Decorators

| Decorator | Purpose |
|-----------|---------|
| `@auto_timeout(name, timeout=None)` | Async timeout with env var override (`HANZO_TIMEOUT_*`) |
| `@with_error_logging(name)` | Log errors to `~/.hanzo/mcp/logs/` and return friendly messages |
| `@handle_connection_errors` | Catch disconnects gracefully |
| `@retry(max_attempts, delay, backoff)` | Exponential backoff retry |

### Top-level Functions

| Function | Purpose |
|----------|---------|
| `discover_tools()` | Find all installed tool packages via entry points |
| `register_all(mcp, pm, enabled)` | Register all discovered tools with an MCP server |

## License

MIT
