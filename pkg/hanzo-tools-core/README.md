# hanzo-tools-core

Core infrastructure for Hanzo MCP tools.

## Installation

```bash
pip install hanzo-tools-core
```

## Components

### BaseTool
Base class for all Hanzo tools.

```python
from hanzo_tools.core import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    
    @property
    def description(self) -> str:
        return "My custom tool"
    
    async def call(self, ctx, **params) -> str:
        return "result"
```

### ToolRegistry
Manage tool registration and discovery.

```python
from hanzo_tools.core import ToolRegistry

ToolRegistry.register_tools(mcp_server, [MyTool()])
```

### PermissionManager
Access control for file and command operations.

```python
from hanzo_tools.core import PermissionManager

pm = PermissionManager(allowed_paths=["/home/user/project"])
if pm.can_access("/home/user/project/file.py"):
    # proceed
```

### Decorators

```python
from hanzo_tools.core import auto_timeout

@auto_timeout("my_tool")
async def my_function():
    # Auto-backgrounds after timeout
    pass
```

## License

MIT
