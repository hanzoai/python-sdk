"""Memory service with plugin support."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .backends.sqlite_plugin import SQLiteBackendPlugin
from .plugin_interface import Capability, PluginRegistry


class PluginMemoryService:
    """Memory service that uses plugins for backend operations."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the service with configuration."""
        self.config_path = config_path
        self.registry = PluginRegistry()
        self._initialized = False

        # Register available plugins
        self._register_available_plugins()

    def _register_available_plugins(self):
        """Register all available backend plugins."""
        # Register SQLite plugin (always available)
        self.registry.register_plugin(SQLiteBackendPlugin())

        # Conditionally register other plugins if dependencies are available
        try:
            # For now, we'll just register the SQLite plugin
            # In the future, we could register other plugins like:
            # from .backends.lancedb_plugin import LanceDBBackendPlugin
            # self.registry.register_plugin(LanceDBBackendPlugin())
            pass
        except ImportError:
            pass  # Skip if dependencies not available

    async def initialize(self, enabled_backends: List[str] = None):
        """Initialize the service and load configured plugins."""
        if self._initialized:
            return

        # If no backends specified, enable default SQLite backend
        if enabled_backends is None:
            enabled_backends = ["sqlite"]

        # Enable configured plugins
        for backend_name in enabled_backends:
            if backend_name in self.registry.get_available_plugins():
                self.registry.enable_plugin(backend_name)
            else:
                print(f"Warning: Backend '{backend_name}' not available, skipping.")

        # Initialize active plugins
        await self.registry.initialize_all_active()
        self._initialized = True

    async def shutdown(self):
        """Shutdown the service and all active plugins."""
        await self.registry.shutdown_all_active()
        self._initialized = False

    async def store_memory(
        self, content: str, metadata: Dict[str, Any], user_id: str = "default", project_id: str = "default"
    ) -> str:
        """Store a memory using active plugins."""
        if not self._initialized:
            await self.initialize()

        # Use the first active plugin for storage
        active_plugins = self.registry.get_active_plugins()
        if not active_plugins:
            raise RuntimeError("No active plugins available")

        # For now, just use the first plugin
        plugin = active_plugins[0]
        return await plugin.store_memory(content, metadata, user_id, project_id)

    async def retrieve_memory(
        self, query: str, user_id: str = "default", project_id: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories using active plugins."""
        if not self._initialized:
            await self.initialize()

        # Use the first active plugin for retrieval
        active_plugins = self.registry.get_active_plugins()
        if not active_plugins:
            raise RuntimeError("No active plugins available")

        # For now, just use the first plugin
        plugin = active_plugins[0]
        return await plugin.retrieve_memory(query, user_id, project_id, limit)

    async def search_memory(
        self, query: str, user_id: str = "default", project_id: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories using active plugins."""
        if not self._initialized:
            await self.initialize()

        # Use the first active plugin for search
        active_plugins = self.registry.get_active_plugins()
        if not active_plugins:
            raise RuntimeError("No active plugins available")

        # For now, just use the first plugin
        plugin = active_plugins[0]
        return await plugin.search_memory(query, user_id, project_id, limit)

    async def delete_memory(self, memory_id: str, user_id: str = "default", project_id: str = "default") -> bool:
        """Delete a memory using active plugins."""
        if not self._initialized:
            await self.initialize()

        # Use the first active plugin for deletion
        active_plugins = self.registry.get_active_plugins()
        if not active_plugins:
            raise RuntimeError("No active plugins available")

        # For now, just use the first plugin
        plugin = active_plugins[0]
        return await plugin.delete_memory(memory_id, user_id, project_id)

    def get_available_backends(self) -> List[str]:
        """Get list of available backends."""
        return self.registry.get_available_plugins()

    def get_active_backends(self) -> List[str]:
        """Get list of active backends."""
        return [plugin.name for plugin in self.registry.get_active_plugins()]

    def get_backend_capabilities(self, backend_name: str) -> List[Capability]:
        """Get capabilities of a specific backend."""
        return self.registry.get_plugin_capabilities(backend_name)

    def has_capability(self, capability: Capability) -> List[str]:
        """Get all backends that support a specific capability."""
        return self.registry.has_capability(capability)

    def enable_backend(self, backend_name: str) -> bool:
        """Enable a specific backend."""
        return self.registry.enable_plugin(backend_name)

    def disable_backend(self, backend_name: str) -> bool:
        """Disable a specific backend."""
        return self.registry.disable_plugin(backend_name)
