"""Plugin interface and registry for memory backends."""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class Capability(str, Enum):
    """Memory backend capabilities."""

    VECTOR_SEARCH = "vector_search"
    FULL_TEXT_SEARCH = "full_text_search"
    STRUCTURED_QUERY = "structured_query"
    PERSISTENCE = "persistence"
    EMBEDDINGS = "embeddings"
    GRAPH_QUERIES = "graph_queries"
    TIME_SERIES = "time_series"
    MARKDOWN_IMPORT = "markdown_import"


@runtime_checkable
class MemoryBackendPlugin(Protocol):
    """Interface for memory backend plugins."""

    @property
    def name(self) -> str:
        """Unique name of the backend."""
        ...

    @property
    def capabilities(self) -> List[Capability]:
        """List of capabilities provided by this backend."""
        ...

    async def initialize(self) -> None:
        """Initialize the backend."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the backend."""
        ...

    async def store_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        user_id: str = "default",
        project_id: str = "default",
    ) -> str:
        """Store a memory and return its ID."""
        ...

    async def retrieve_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        ...

    async def search_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories based on query with scoring."""
        ...

    async def delete_memory(
        self, memory_id: str, user_id: str = "default", project_id: str = "default"
    ) -> bool:
        """Delete a memory by ID."""
        ...


class PluginRegistry:
    """Registry for memory backend plugins."""

    def __init__(self):
        self._plugins: Dict[str, MemoryBackendPlugin] = {}
        self._active_plugins: List[str] = []
        self._initialized = False

    def register_plugin(self, plugin: MemoryBackendPlugin):
        """Register a new plugin."""
        self._plugins[plugin.name] = plugin

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            if name in self._active_plugins:
                self._active_plugins.remove(name)
            return True
        return False

    def enable_plugin(self, name: str) -> bool:
        """Enable a registered plugin."""
        if name in self._plugins and name not in self._active_plugins:
            self._active_plugins.append(name)
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable an active plugin."""
        if name in self._active_plugins:
            self._active_plugins.remove(name)
            return True
        return False

    def get_plugin(self, name: str) -> Optional[MemoryBackendPlugin]:
        """Get a specific plugin."""
        return self._plugins.get(name)

    def get_active_plugins(self) -> List[MemoryBackendPlugin]:
        """Get all active plugins."""
        return [self._plugins[name] for name in self._active_plugins]

    def get_available_plugins(self) -> List[str]:
        """Get names of all registered plugins."""
        return list(self._plugins.keys())

    def get_plugin_capabilities(self, name: str) -> List[Capability]:
        """Get capabilities of a specific plugin."""
        plugin = self.get_plugin(name)
        return plugin.capabilities if plugin else []

    def has_capability(self, capability: Capability) -> List[str]:
        """Get all plugins that support a specific capability."""
        result = []
        for name, plugin in self._plugins.items():
            if capability in plugin.capabilities:
                result.append(name)
        return result

    async def initialize_all_active(self):
        """Initialize all active plugins."""
        if not self._initialized:
            for plugin in self.get_active_plugins():
                await plugin.initialize()
            self._initialized = True

    async def shutdown_all_active(self):
        """Shutdown all active plugins."""
        for plugin in self.get_active_plugins():
            await plugin.shutdown()
        self._initialized = False


# Global registry instance
registry = PluginRegistry()
