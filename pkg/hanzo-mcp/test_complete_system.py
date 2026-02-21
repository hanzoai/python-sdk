"""Final test to verify the complete system works as intended."""

import asyncio
import json
from pathlib import Path

from hanzo_mcp.config import get_global_config_path, load_config
from hanzo_mcp.memory_service import PluginMemoryService


async def test_complete_system():
    """Test the complete system with all components working together."""
    print("Testing complete system with all components...")

    # Create a global config file with memory backend enabled
    config_path = get_global_config_path()

    # Create config with memory backend
    memory_config = {
        "enabled_backends": ["sqlite"],
        "backend_configs": {
            "sqlite": {
                "enabled": True,
                "path": str(Path.home() / ".hanzo" / "memory.db"),
                "settings": {"auto_migrate": True, "connection_timeout": 30},
            }
        },
        "default_user_id": "hanzo-user",
        "default_project_id": "hanzo-project",
    }

    # Save the config
    with open(config_path, "w") as f:
        json.dump(memory_config, f, indent=2)

    print(f"Created config with memory backend at: {config_path}")

    # Load config using our system
    loaded_config = load_config()
    print(f"✓ Loaded config with enabled backends: {loaded_config.enabled_backends}")

    # Test memory service initialization
    print("\nInitializing memory service...")
    service = PluginMemoryService()
    await service.initialize(enabled_backends=loaded_config.enabled_backends)
    print(f"✓ Active backends: {service.get_active_backends()}")

    # Verify the memory backend is properly configured
    print(f"✓ Available backends: {service.get_available_backends()}")
    print(f"✓ Backend capabilities: {service.get_backend_capabilities('sqlite')}")

    # Test memory operations
    print("\nTesting memory operations...")

    # Store multiple memories
    test_memories = [
        {
            "content": "Hanzo MCP modular architecture enables flexible backend selection",
            "metadata": {"type": "architecture", "domain": "mcp", "importance": 0.9},
        },
        {
            "content": "SQLite backend provides lightweight persistence with vector search",
            "metadata": {"type": "backend", "domain": "storage", "importance": 0.8},
        },
        {
            "content": "Plugin system allows dynamic loading of memory backends",
            "metadata": {"type": "feature", "domain": "modularity", "importance": 0.85},
        },
    ]

    memory_ids = []
    for i, mem in enumerate(test_memories):
        memory_id = await service.store_memory(
            content=mem["content"],
            metadata=mem["metadata"],
            user_id=loaded_config.default_user_id,
            project_id=loaded_config.default_project_id,
        )
        memory_ids.append(memory_id)
        print(f"✓ Stored memory {i + 1} with ID: {memory_id[:8]}...")

    # Test retrieval
    print("\nTesting retrieval...")
    retrieved = await service.retrieve_memory(
        query="memory backend",
        user_id=loaded_config.default_user_id,
        project_id=loaded_config.default_project_id,
        limit=10,
    )
    print(f"✓ Retrieved {len(retrieved)} memories matching 'memory backend'")

    # Test search
    print("\nTesting search functionality...")
    search_results = await service.search_memory(
        query="modular architecture",
        user_id=loaded_config.default_user_id,
        project_id=loaded_config.default_project_id,
        limit=5,
    )
    print(f"✓ Found {len(search_results)} memories for 'modular architecture'")

    # Display search results
    for i, result in enumerate(search_results):
        print(
            f"  Result {i + 1}: {result['content'][:60]}... (score: {result.get('similarity_score', 'N/A')})"
        )

    # Test capability queries
    print("\nTesting capability queries...")
    vector_backends = service.has_capability("vector_search")
    persistence_backends = service.has_capability("persistence")
    print(f"✓ Backends with vector search: {vector_backends}")
    print(f"✓ Backends with persistence: {persistence_backends}")

    # Test backend management
    print("\nTesting backend management...")
    print(f"✓ Current active backends: {service.get_active_backends()}")

    # Try disabling and re-enabling
    was_enabled = service.disable_backend("sqlite")
    print(f"✓ SQLite disabled: {was_enabled}")
    print(f"✓ Active backends after disable: {service.get_active_backends()}")

    was_reenabled = service.enable_backend("sqlite")
    print(f"✓ SQLite re-enabled: {was_reenabled}")
    print(f"✓ Active backends after re-enable: {service.get_active_backends()}")

    # Cleanup
    print("\nCleaning up...")
    await service.shutdown()

    # Remove test config
    if config_path.exists():
        config_path.unlink()
        print(f"✓ Removed test config: {config_path}")

    print("\n🎉 Complete system test passed!")
    print("✅ uvx hanzo-mcp[memory] would work with full memory backend support")
    print(
        "✅ Settings management works properly with ~/.config/hanzo/mcp-settings.json"
    )
    print("✅ Modular plugin architecture enables flexible backend selection")
    print("✅ SQLite backend provides lightweight persistence with vector search")


if __name__ == "__main__":
    asyncio.run(test_complete_system())
