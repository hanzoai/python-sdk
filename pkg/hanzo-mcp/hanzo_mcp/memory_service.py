"""Memory service with plugin support.

Provides namespace-scoped, key-addressable memory with tags, TTL,
and full TypeScript parity for the blue-red agent coordination protocol.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .backends.sqlite_plugin import SQLiteBackendPlugin
from .plugin_interface import Capability, PluginRegistry


class PluginMemoryService:
    """Memory service that uses plugins for backend operations.

    Supports:
    - namespace: isolate memories into named channels (default: "default")
    - key: address individual memories by name for exact retrieval
    - tags: categorize and filter memories
    - ttl: auto-expire memories after an ISO date
    - append: concatenate content to an existing keyed memory
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the service with configuration."""
        self.config_path = config_path
        self.registry = PluginRegistry()
        self._initialized = False

        # Register available plugins
        self._register_available_plugins()

    def _register_available_plugins(self):
        """Register all available backend plugins."""
        self.registry.register_plugin(SQLiteBackendPlugin())

    async def initialize(self, enabled_backends: List[str] = None):
        """Initialize the service and load configured plugins."""
        if self._initialized:
            return

        if enabled_backends is None:
            enabled_backends = ["sqlite"]

        for backend_name in enabled_backends:
            if backend_name in self.registry.get_available_plugins():
                self.registry.enable_plugin(backend_name)
            else:
                print(f"Warning: Backend '{backend_name}' not available, skipping.")

        await self.registry.initialize_all_active()
        self._initialized = True

    async def shutdown(self):
        """Shutdown the service and all active plugins."""
        await self.registry.shutdown_all_active()
        self._initialized = False

    def _get_plugin(self):
        """Get the first active plugin, initializing if needed."""
        active = self.registry.get_active_plugins()
        if not active:
            raise RuntimeError("No active plugins available")
        return active[0]

    async def _ensure_init(self):
        if not self._initialized:
            await self.initialize()

    # ------------------------------------------------------------------ #
    # Core CRUD — backward compatible + new params
    # ------------------------------------------------------------------ #

    async def store_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        user_id: str = "default",
        project_id: str = "default",
        namespace: str = "default",
        key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ttl: Optional[str] = None,
        append: bool = False,
    ) -> str:
        """Store a memory using active plugins.

        Args:
            content: The memory content.
            metadata: Arbitrary metadata dict.
            user_id: Owner user ID.
            project_id: Project scope.
            namespace: Logical namespace (e.g. "blue-red").
            key: Optional unique key for retrieval.
            tags: Optional list of tags.
            ttl: Optional ISO date string; memory expires after this time.
            append: If True and key exists, concatenate content.

        Returns:
            The memory_id of the stored entry.
        """
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.store_memory(
            content=content,
            metadata=metadata,
            user_id=user_id,
            project_id=project_id,
            namespace=namespace,
            key=key,
            tags=tags,
            ttl=ttl,
            append=append,
        )

    async def retrieve_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories using active plugins."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.retrieve_memory(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            namespace=namespace,
            metadata_filter=metadata_filter,
        )

    async def search_memory(
        self,
        query: str,
        user_id: str = "default",
        project_id: str = "default",
        limit: int = 10,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search memories using active plugins."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.search_memory(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            namespace=namespace,
            metadata_filter=metadata_filter,
        )

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str = "default",
        project_id: str = "default",
    ) -> bool:
        """Delete a memory using active plugins."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.delete_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
        )

    # ------------------------------------------------------------------ #
    # New operations for TypeScript parity
    # ------------------------------------------------------------------ #

    async def get_by_key(self, key: str, namespace: str = "default"):
        """Get memory by exact key or wildcard within namespace.

        Exact key returns a single dict or None.
        Wildcard key (contains '*') returns a list.
        """
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.get_by_key(key=key, namespace=namespace)

    async def list_memories(
        self,
        namespace: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List all memories with optional namespace/tag filters."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.list_memories(namespace=namespace, tag=tag, limit=limit)

    async def stats(self) -> Dict[str, Any]:
        """Return count, namespaces, size info."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.stats()

    async def clear(self, namespace: Optional[str] = None) -> int:
        """Clear all or namespace-specific memories. Returns count deleted."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.clear(namespace=namespace)

    async def tag_memory(self, memory_id: str, tag: str) -> bool:
        """Add a tag to a memory."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.tag_memory(memory_id=memory_id, tag=tag)

    async def untag_memory(self, memory_id: str, tag: str) -> bool:
        """Remove a tag from a memory."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.untag_memory(memory_id=memory_id, tag=tag)

    async def namespaces(self) -> Dict[str, int]:
        """List all namespaces with counts."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.namespaces()

    async def history(self, key: str, namespace: str = "default") -> List[Dict[str, Any]]:
        """Show all versions of a key."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.history(key=key, namespace=namespace)

    async def export_memories(
        self, namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Export memories as a list of dicts."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.export_memories(namespace=namespace)

    async def import_memories(self, data: List[Dict[str, Any]]) -> int:
        """Import memories from exported data. Returns count imported."""
        await self._ensure_init()
        plugin = self._get_plugin()
        return await plugin.import_memories(data=data)

    # ------------------------------------------------------------------ #
    # Backend management (unchanged)
    # ------------------------------------------------------------------ #

    def get_available_backends(self) -> List[str]:
        return self.registry.get_available_plugins()

    def get_active_backends(self) -> List[str]:
        return [plugin.name for plugin in self.registry.get_active_plugins()]

    def get_backend_capabilities(self, backend_name: str) -> List[Capability]:
        return self.registry.get_plugin_capabilities(backend_name)

    def has_capability(self, capability: Capability) -> List[str]:
        return self.registry.has_capability(capability)

    def enable_backend(self, backend_name: str) -> bool:
        return self.registry.enable_plugin(backend_name)

    def disable_backend(self, backend_name: str) -> bool:
        return self.registry.disable_plugin(backend_name)
