# Modular Plugin Architecture for Hanzo-MCP Memory System

## Overview
This document outlines a modular plugin architecture for the Hanzo-MCP memory system that allows users to enable specific backends and capabilities as needed, without requiring heavy dependencies by default.

## Current Architecture
- `hanzo-mcp`: Main MCP server
- `hanzo-tools-memory`: Memory tools package with unified interface
- `hanzo-memory`: Full memory backend implementation with multiple backends

## Proposed Plugin Architecture

### 1. Plugin Interface
Define a standard interface for memory backends that can be loaded dynamically:

```python
from abc import ABC, abstractmethod
from typing import Protocol, Optional, List, Dict, Any

class MemoryBackendPlugin(Protocol):
    """Interface for memory backend plugins."""
    
    @property
    def name(self) -> str:
        """Unique name of the backend."""
        ...
        
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities provided by this backend."""
        ...
    
    async def initialize(self) -> None:
        """Initialize the backend."""
        ...
    
    async def shutdown(self) -> None:
        """Shutdown the backend."""
        ...
    
    async def store_memory(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store a memory and return its ID."""
        ...
    
    async def retrieve_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        ...
```

### 2. Plugin Registry
A central registry to manage available plugins:

```python
class PluginRegistry:
    """Registry for memory backend plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, MemoryBackendPlugin] = {}
        self._active_plugins: List[str] = []
    
    def register_plugin(self, plugin: MemoryBackendPlugin):
        """Register a new plugin."""
        self._plugins[plugin.name] = plugin
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a registered plugin."""
        if name in self._plugins and name not in self._active_plugins:
            self._active_plugins.append(name)
            return True
        return False
    
    def get_active_plugins(self) -> List[MemoryBackendPlugin]:
        """Get all active plugins."""
        return [self._plugins[name] for name in self._active_plugins]
```

### 3. Configuration-Based Loading
Allow users to configure which backends to load via configuration:

```python
# config.py
from pydantic import BaseModel
from typing import List

class PluginConfig(BaseModel):
    enabled_backends: List[str] = ["sqlite"]  # Default to lightweight SQLite
    backend_configs: Dict[str, Dict[str, Any]] = {
        "sqlite": {"path": "~/.hanzo/memory.db"},
        "lancedb": {"path": "./data/lancedb"},
        "redis": {"url": "redis://localhost:6379"}
    }
```

### 4. Lazy Loading
Only load plugins when they are actually needed:

```python
class MemoryService:
    """Memory service that uses plugins."""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.registry = PluginRegistry()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service and load configured plugins."""
        if self._initialized:
            return
            
        # Register all available plugins
        self._register_available_plugins()
        
        # Enable configured plugins
        for backend_name in self.config.enabled_backends:
            self.registry.enable_plugin(backend_name)
        
        # Initialize active plugins
        for plugin in self.registry.get_active_plugins():
            await plugin.initialize()
        
        self._initialized = True
    
    def _register_available_plugins(self):
        """Register all available backend plugins."""
        # Register SQLite plugin
        from .backends.sqlite_plugin import SQLiteBackendPlugin
        self.registry.register_plugin(SQLiteBackendPlugin())
        
        # Conditionally register other plugins if dependencies are available
        try:
            from .backends.lancedb_plugin import LanceDBBackendPlugin
            self.registry.register_plugin(LanceDBBackendPlugin())
        except ImportError:
            pass  # Skip if dependencies not available
        
        try:
            from .backends.redis_plugin import RedisBackendPlugin
            self.registry.register_plugin(RedisBackendPlugin())
        except ImportError:
            pass
```

### 5. User Experience
Users can enable backends as needed:

```bash
# Default installation - only lightweight SQLite
pip install hanzo-mcp

# With full memory capabilities
pip install hanzo-mcp[memory]

# With specific backends
pip install hanzo-mcp[memory,lancedb,redis]

# Or configure via config file
echo '{"enabled_backends": ["sqlite", "lancedb"]}' > hanzo_config.json
```

## Benefits

1. **Modularity**: Users only install what they need
2. **Flexibility**: Easy to add new backends
3. **Performance**: Only load necessary components
4. **Scalability**: Different backends for different use cases
5. **Maintainability**: Clear separation of concerns

## Implementation Steps

1. Define the plugin interface
2. Create the registry system
3. Implement the lazy loading mechanism
4. Create adapter classes for existing backends
5. Update configuration system
6. Update documentation and examples

This architecture would allow users to have a lightweight MCP server by default, but enable advanced memory capabilities when needed, without having to rebuild or restart the entire system.