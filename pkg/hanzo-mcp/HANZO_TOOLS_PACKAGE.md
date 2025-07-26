# hanzo-tools Package Design

The `hanzo-tools` package extracts the tool framework from hanzo-mcp to provide a reusable foundation for building tools across all Hanzo packages.

## Package Structure

```
pkg/hanzo-tools/
├── pyproject.toml
├── README.md
├── src/
│   └── hanzo_tools/
│       ├── __init__.py
│       ├── base.py              # BaseTool abstract class
│       ├── registry.py          # ToolRegistry for registration
│       ├── context.py           # ToolContext management
│       ├── permissions.py       # PermissionManager
│       ├── decorators.py        # @tool decorator
│       ├── batch.py            # BatchTool for parallel execution
│       ├── pagination.py       # Pagination support
│       ├── streaming.py        # StreamingTool base
│       ├── errors.py           # Tool-specific exceptions
│       └── utils.py            # Utility functions
└── tests/
    ├── test_base.py
    ├── test_registry.py
    ├── test_permissions.py
    └── test_batch.py
```

## Core Components

### 1. BaseTool (base.py)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T', bound='BaseTool')

class BaseTool(ABC, Generic[T]):
    """Abstract base class for all tools."""
    
    name: str
    description: str
    version: str = "1.0.0"
    
    def __init__(self, permission_manager: Optional['PermissionManager'] = None):
        self.permission_manager = permission_manager
        self._validate()
    
    @abstractmethod
    async def call(self, context: 'ToolContext', **kwargs) -> Any:
        """Execute the tool with given context and arguments."""
        pass
    
    def _validate(self) -> None:
        """Validate tool configuration."""
        if not self.name:
            raise ValueError("Tool must have a name")
        if not self.description:
            raise ValueError("Tool must have a description")
    
    @classmethod
    def register(cls: type[T], registry: 'ToolRegistry') -> T:
        """Register this tool with a registry."""
        tool = cls()
        registry.register(tool)
        return tool
```

### 2. ToolRegistry (registry.py)
```python
from typing import Dict, List, Optional, Protocol
import inspect

class ToolProtocol(Protocol):
    """Protocol for tool registration."""
    name: str
    description: str
    
    async def call(self, context: 'ToolContext', **kwargs) -> Any: ...

class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolProtocol] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: ToolProtocol, category: str = "general") -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        
        self._tools[tool.name] = tool
        
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)
    
    def get(self, name: str) -> Optional[ToolProtocol]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        """List tools in a category."""
        return self._categories.get(category, [])
```

### 3. Tool Decorator (decorators.py)
```python
from functools import wraps
from typing import Callable, Any, Optional
import inspect

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
    permissions: Optional[List[str]] = None
):
    """Decorator to create a tool from a function."""
    
    def decorator(func: Callable) -> 'FunctionTool':
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or "No description"
        
        # Extract parameters from function signature
        sig = inspect.signature(func)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name not in ['self', 'context']:
                params[param_name] = {
                    'type': param.annotation,
                    'required': param.default == param.empty,
                    'default': param.default if param.default != param.empty else None
                }
        
        class FunctionTool(BaseTool):
            name = tool_name
            description = tool_desc
            parameters = params
            required_permissions = permissions or []
            
            async def call(self, context: ToolContext, **kwargs):
                # Check permissions
                if self.permission_manager and self.required_permissions:
                    for perm in self.required_permissions:
                        if not self.permission_manager.has_permission(perm):
                            raise PermissionError(f"Missing permission: {perm}")
                
                # Call the wrapped function
                if inspect.iscoroutinefunction(func):
                    return await func(context=context, **kwargs)
                else:
                    return func(context=context, **kwargs)
        
        return FunctionTool()
    
    return decorator
```

### 4. BatchTool (batch.py)
```python
import asyncio
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor

class BatchTool(BaseTool):
    """Tool for executing multiple operations in parallel."""
    
    name = "batch"
    description = "Execute multiple tool calls in parallel"
    
    def __init__(self, registry: ToolRegistry, max_workers: int = 10):
        super().__init__()
        self.registry = registry
        self.max_workers = max_workers
    
    async def call(self, context: ToolContext, operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple operations in parallel.
        
        Args:
            context: Tool context
            operations: List of dicts with 'tool' and 'args' keys
            
        Returns:
            List of results in the same order as operations
        """
        tasks = []
        
        for op in operations:
            tool_name = op.get('tool')
            args = op.get('args', {})
            
            tool = self.registry.get(tool_name)
            if not tool:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Create task for this operation
            task = asyncio.create_task(tool.call(context, **args))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'error': str(result),
                    'tool': operations[i]['tool']
                })
            else:
                processed_results.append({
                    'result': result,
                    'tool': operations[i]['tool']
                })
        
        return processed_results
```

### 5. Permissions (permissions.py)
```python
from typing import Set, List, Optional
from pathlib import Path
import fnmatch

class PermissionManager:
    """Manage permissions for tool execution."""
    
    def __init__(self):
        self._allowed_paths: Set[Path] = set()
        self._denied_paths: Set[Path] = set()
        self._permissions: Set[str] = set()
    
    def add_allowed_path(self, path: str) -> None:
        """Add an allowed path."""
        self._allowed_paths.add(Path(path).resolve())
    
    def add_denied_path(self, path: str) -> None:
        """Add a denied path."""
        self._denied_paths.add(Path(path).resolve())
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed."""
        p = Path(path).resolve()
        
        # Check denied paths first
        for denied in self._denied_paths:
            if p.is_relative_to(denied):
                return False
        
        # Check allowed paths
        for allowed in self._allowed_paths:
            if p.is_relative_to(allowed):
                return True
        
        # Default deny if no allowed paths configured
        return len(self._allowed_paths) == 0
    
    def grant_permission(self, permission: str) -> None:
        """Grant a permission."""
        self._permissions.add(permission)
    
    def revoke_permission(self, permission: str) -> None:
        """Revoke a permission."""
        self._permissions.discard(permission)
    
    def has_permission(self, permission: str) -> bool:
        """Check if a permission is granted."""
        return permission in self._permissions
```

## Usage Examples

### Creating a Simple Tool
```python
from hanzo_tools import tool, ToolContext

@tool(name="greet", description="Greet someone", category="social")
async def greet_tool(context: ToolContext, name: str, formal: bool = False) -> str:
    if formal:
        return f"Good day, {name}."
    return f"Hello, {name}!"
```

### Creating a Class-Based Tool
```python
from hanzo_tools import BaseTool, ToolContext

class FileReadTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file"
    
    async def call(self, context: ToolContext, path: str) -> str:
        # Check permissions
        if not self.permission_manager.is_path_allowed(path):
            raise PermissionError(f"Access denied: {path}")
        
        with open(path, 'r') as f:
            return f.read()
```

### Using the Registry
```python
from hanzo_tools import ToolRegistry, PermissionManager

# Create registry and permission manager
registry = ToolRegistry()
pm = PermissionManager()
pm.add_allowed_path("/workspace")

# Register tools
greet_tool.register(registry)
FileReadTool(pm).register(registry)

# Use tools
context = ToolContext()
result = await registry.get("greet").call(context, name="World")
```

### Batch Execution
```python
from hanzo_tools import BatchTool

batch = BatchTool(registry)
results = await batch.call(context, operations=[
    {"tool": "greet", "args": {"name": "Alice"}},
    {"tool": "greet", "args": {"name": "Bob", "formal": True}},
    {"tool": "read_file", "args": {"path": "/workspace/readme.txt"}}
])
```

## Integration with MCP

hanzo-mcp would use hanzo-tools as its foundation:

```python
# In hanzo-mcp
from hanzo_tools import BaseTool, ToolRegistry, tool
from mcp.server import FastMCP

class MCPToolAdapter:
    """Adapt hanzo-tools for MCP server."""
    
    def __init__(self, mcp_server: FastMCP, registry: ToolRegistry):
        self.mcp = mcp_server
        self.registry = registry
    
    def register_all(self):
        """Register all tools with MCP server."""
        for tool_name in self.registry.list_tools():
            tool = self.registry.get(tool_name)
            self._register_mcp_tool(tool)
    
    def _register_mcp_tool(self, tool: BaseTool):
        """Register a single tool with MCP."""
        @self.mcp.tool(name=tool.name, description=tool.description)
        async def mcp_handler(context, **kwargs):
            # Convert MCP context to ToolContext
            tool_context = self._convert_context(context)
            return await tool.call(tool_context, **kwargs)
```

## Benefits

1. **Reusable**: Any package can use hanzo-tools to create tools
2. **Consistent**: Same tool patterns everywhere
3. **Extensible**: Easy to add new tool types
4. **Testable**: Built-in test utilities
5. **Type-Safe**: Full type hints throughout
6. **Async-First**: Designed for async/await patterns