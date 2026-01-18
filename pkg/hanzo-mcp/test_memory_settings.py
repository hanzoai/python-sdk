"""Test the memory backend with settings management."""

import json
import asyncio
from pathlib import Path

from hanzo_mcp.config import load_config, save_global_config, get_global_config_path
from hanzo_mcp.memory_service import PluginMemoryService


async def test_memory_backend_with_settings():
    """Test the memory backend with settings management."""
    print("Testing memory backend with settings management...")
    
    # Create a global config file
    config_path = get_global_config_path()
    print(f"Global config path: {config_path}")
    
    # Create sample config
    sample_config = {
        "enabled_backends": ["sqlite"],
        "backend_configs": {
            "sqlite": {
                "enabled": True,
                "path": str(Path.home() / ".hanzo" / "memory.db"),
                "settings": {
                    "auto_migrate": True,
                    "connection_timeout": 30
                }
            }
        },
        "default_user_id": "test-user",
        "default_project_id": "test-project"
    }
    
    # Save the config
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Saved sample config to {config_path}")
    
    # Load config using our system
    loaded_config = load_config()
    print(f"Loaded config enabled backends: {loaded_config.enabled_backends}")
    print(f"Loaded config default user: {loaded_config.default_user_id}")
    print(f"Loaded config default project: {loaded_config.default_project_id}")
    
    # Test memory service with loaded config
    print("\nTesting memory service with loaded config...")
    service = PluginMemoryService()
    
    # Initialize with the loaded config's settings
    await service.initialize(enabled_backends=loaded_config.enabled_backends)
    print(f"Active backends: {service.get_active_backends()}")
    
    # Test memory operations
    print("\nTesting memory operations...")
    
    # Store a memory
    metadata = {"type": "test", "source": "settings_test", "importance": 0.8}
    memory_id = await service.store_memory(
        content="This is a test memory stored using the settings-managed memory backend",
        metadata=metadata,
        user_id=loaded_config.default_user_id,
        project_id=loaded_config.default_project_id
    )
    print(f"Stored memory with ID: {memory_id}")
    
    # Retrieve the memory
    results = await service.retrieve_memory(
        query="test memory",
        user_id=loaded_config.default_user_id,
        project_id=loaded_config.default_project_id,
        limit=5
    )
    print(f"Retrieved {len(results)} memories")
    if results:
        print(f"First result content preview: {results[0]['content'][:50]}...")
        print(f"Result metadata: {results[0]['metadata']}")
    
    # Test search functionality
    print("\nTesting search functionality...")
    search_results = await service.search_memory(
        query="settings-managed memory backend",
        user_id=loaded_config.default_user_id,
        project_id=loaded_config.default_project_id,
        limit=5
    )
    print(f"Searched and found {len(search_results)} memories")
    
    # Test backend management
    print("\nTesting backend management...")
    print(f"Available backends: {service.get_available_backends()}")
    print(f"Active backends: {service.get_active_backends()}")
    
    # Check capabilities
    print(f"Backends with persistence: {service.has_capability('persistence')}")
    print(f"Backends with embeddings: {service.has_capability('embeddings')}")
    
    # Cleanup: shutdown the service
    await service.shutdown()
    print("\nService shut down successfully")
    
    # Optionally, remove the test config file
    if config_path.exists():
        config_path.unlink()
        print(f"Cleaned up config file: {config_path}")
    
    print("\n✅ Memory backend with settings management test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_memory_backend_with_settings())