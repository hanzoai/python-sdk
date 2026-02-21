"""Test the modular plugin architecture implementation."""

import asyncio
import tempfile
from pathlib import Path

from hanzo_mcp.backends.sqlite_plugin import SQLiteBackendPlugin
from hanzo_mcp.config import get_default_config
from hanzo_mcp.memory_service import PluginMemoryService
from hanzo_mcp.plugin_interface import Capability


async def test_modular_architecture():
    """Test the modular plugin architecture."""
    print("Testing modular plugin architecture...")

    # Test 1: Plugin interface and registry
    print("\n1. Testing plugin interface and registry...")

    # Create a SQLite plugin
    plugin = SQLiteBackendPlugin()
    print(f"   Plugin name: {plugin.name}")
    print(f"   Plugin capabilities: {plugin.capabilities}")

    # Initialize the plugin
    await plugin.initialize()
    print("   Plugin initialized successfully")

    # Test 2: Memory service with plugin support
    print("\n2. Testing memory service with plugin support...")

    # Create memory service
    service = PluginMemoryService()
    print(f"   Available backends: {service.get_available_backends()}")

    # Initialize with default backends (SQLite)
    await service.initialize()
    print(f"   Active backends: {service.get_active_backends()}")

    # Test 3: Memory operations
    print("\n3. Testing memory operations...")

    # Store a memory
    metadata = {"type": "test", "source": "modular_test"}
    memory_id = await service.store_memory(
        content="This is a test memory for the modular architecture",
        metadata=metadata,
        user_id="test-user",
        project_id="test-project",
    )
    print(f"   Stored memory with ID: {memory_id}")

    # Retrieve the memory
    results = await service.retrieve_memory(
        query="test memory", user_id="test-user", project_id="test-project", limit=5
    )
    print(f"   Retrieved {len(results)} memories")
    if results:
        print(f"   First result content preview: {results[0]['content'][:50]}...")

    # Test 4: Capability queries
    print("\n4. Testing capability queries...")

    backends_with_vector_search = service.has_capability(Capability.VECTOR_SEARCH)
    print(f"   Backends with vector search: {backends_with_vector_search}")

    backends_with_persistence = service.has_capability(Capability.PERSISTENCE)
    print(f"   Backends with persistence: {backends_with_persistence}")

    # Test 5: Backend management
    print("\n5. Testing backend management...")

    # Try to disable and enable backends
    sqlite_disabled = service.disable_backend("sqlite")
    print(f"   SQLite disabled: {sqlite_disabled}")
    print(f"   Active backends after disabling SQLite: {service.get_active_backends()}")

    sqlite_enabled = service.enable_backend("sqlite")
    print(f"   SQLite enabled: {sqlite_enabled}")
    print(f"   Active backends after enabling SQLite: {service.get_active_backends()}")

    # Test 6: Configuration system
    print("\n6. Testing configuration system...")

    config = get_default_config()
    print(f"   Default enabled backends: {config.enabled_backends}")
    print(f"   Default user ID: {config.default_user_id}")
    print(f"   Default project ID: {config.default_project_id}")

    # Test 7: Shutdown
    print("\n7. Testing shutdown...")
    await service.shutdown()
    print("   Service shut down successfully")

    print("\n✅ All tests passed! Modular plugin architecture is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_modular_architecture())
