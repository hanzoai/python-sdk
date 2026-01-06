# hanzo-tools-core

The foundation package for all Hanzo tool implementations. Provides base classes, type definitions, and utilities for building MCP-compatible tools.

## Installation

```bash
pip install hanzo-tools-core
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-core` provides:

- **BaseTool** - Abstract base class for all tool implementations
- **FileSystemTool** - Specialized base for file operations
- **ToolRegistry** - Central registry for tool management
- **MCPResourceDocument** - Structured response format
- **ToolContext** - Runtime context for tool execution
- **PermissionManager** - Path-based access control

## Quick Start

### Creating a Custom Tool

```python
from hanzo_tools.core import BaseTool, ToolContext

class MyTool(BaseTool):
    """A custom tool implementation."""

    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something useful"

    async def call(self, ctx: ToolContext, message: str) -> str:
        """Execute the tool.

        Args:
            ctx: Tool execution context
            message: Input message to process

        Returns:
            Processed result
        """
        return f"Processed: {message}"

    def register(self, mcp_server):
        """Register with MCP server."""
        @mcp_server.tool(name=self.name, description=self.description)
        async def handler(message: str) -> str:
            ctx = ToolContext()
            return await self.call(ctx, message=message)
```

### Using the Tool Registry

```python
from hanzo_tools.core import ToolRegistry, BaseTool

# Register tools
registry = ToolRegistry()
registry.register(MyTool())

# Get a tool by name
tool = registry.get("my_tool")

# List all registered tools
for name, tool in registry.items():
    print(f"{name}: {tool.description}")
```

## Base Classes

### BaseTool

The abstract base class all tools must inherit from:

```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Abstract base class for all Hanzo tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description shown to LLMs."""
        ...

    @abstractmethod
    async def call(self, ctx: ToolContext, **params) -> str:
        """Execute the tool with given parameters."""
        ...

    @abstractmethod
    def register(self, mcp_server: FastMCP) -> None:
        """Register the tool with an MCP server."""
        ...
```

### FileSystemTool

Specialized base class for tools that operate on the filesystem:

```python
from hanzo_tools.core import FileSystemTool

class ReadTool(FileSystemTool):
    """Read file contents."""

    @property
    def name(self) -> str:
        return "read"

    async def call(self, ctx, file_path: str) -> str:
        # Automatic path validation and permission checking
        validated_path = self.validate_path(file_path)
        async with aiofiles.open(validated_path) as f:
            return await f.read()
```

## Response Format

### MCPResourceDocument

Structured format for tool responses:

```python
from hanzo_tools.core import MCPResourceDocument

# Create a document response
doc = MCPResourceDocument(
    uri="file:///path/to/file.py",
    mime_type="text/x-python",
    text="def hello(): pass"
)

# Convert to JSON string for MCP
response = doc.to_json_string()
```

## Context Management

### ToolContext

Runtime context passed to every tool invocation:

```python
from hanzo_tools.core import ToolContext, create_tool_context

# Create context with custom settings
ctx = create_tool_context(
    allowed_paths=["/home/user/project"],
    enable_write=True,
    timeout=30.0
)

# Access context in tool
async def call(self, ctx: ToolContext, **params):
    if ctx.enable_write:
        # Perform write operation
        ...
```

## Permission Management

### PermissionManager

Controls which paths tools can access:

```python
from hanzo_tools.core import PermissionManager

pm = PermissionManager(
    allowed_paths=[
        "/home/user/project",
        "/tmp"
    ],
    denied_paths=[
        "/home/user/project/.env",
        "/home/user/project/secrets"
    ]
)

# Check if path is allowed
if pm.is_allowed("/home/user/project/src/main.py"):
    # Safe to access
    ...
```

## Decorators

### auto_timeout

Automatically handle timeouts for long-running operations:

```python
from hanzo_tools.core import auto_timeout

class SlowTool(BaseTool):
    @auto_timeout(seconds=30)
    async def call(self, ctx, **params):
        # Will automatically timeout after 30 seconds
        result = await slow_operation()
        return result
```

## Error Handling

Tools should return error messages as strings rather than raising exceptions:

```python
async def call(self, ctx, file_path: str) -> str:
    try:
        content = await read_file(file_path)
        return content
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"
```

## API Reference

::: hanzo_tools.core.base.BaseTool
    options:
      show_source: false
      members:
        - name
        - description
        - call
        - register

::: hanzo_tools.core.base.FileSystemTool

::: hanzo_tools.core.base.ToolRegistry

::: hanzo_tools.core.types.MCPResourceDocument

::: hanzo_tools.core.context.ToolContext

::: hanzo_tools.core.permissions.PermissionManager
