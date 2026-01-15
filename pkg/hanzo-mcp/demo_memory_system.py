#!/usr/bin/env python3
"""
Demonstration of the Hanzo MCP Memory System with Modular Plugin Architecture.

This script shows how users can:
1. Install hanzo-mcp with memory support
2. Configure memory backends
3. Use the memory system
"""

import asyncio
import json
from pathlib import Path

from hanzo_mcp.memory_service import PluginMemoryService
from hanzo_mcp.config import load_config, save_global_config, get_global_config_path


async def demo_memory_system():
    """Demonstrate the memory system usage."""
    print("🚀 Hanzo MCP Memory System Demo")
    print("=" * 50)
    
    # Step 1: Show configuration file location
    config_path = get_global_config_path()
    print(f"📁 Configuration file location: {config_path}")
    
    # Step 2: Create a sample configuration
    print("\n🔧 Creating sample configuration...")
    sample_config = {
        "enabled_backends": ["sqlite"],  # Enable SQLite backend
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
        "default_user_id": "demo-user",
        "default_project_id": "demo-project"
    }
    
    print("📋 Sample configuration:")
    print(json.dumps(sample_config, indent=2))
    
    # Step 3: Save and load configuration
    print(f"\n💾 Saving configuration to {config_path}")
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("🔄 Loading configuration...")
    config = load_config()
    print(f"   Enabled backends: {config.enabled_backends}")
    
    # Step 4: Initialize memory service
    print("\n⚡ Initializing memory service...")
    service = PluginMemoryService()
    await service.initialize(enabled_backends=config.enabled_backends)
    print(f"   Active backends: {service.get_active_backends()}")
    
    # Step 5: Demonstrate memory operations
    print("\n🧠 Demonstrating memory operations...")
    
    # Store a memory
    memory_id = await service.store_memory(
        content="The Hanzo MCP modular architecture enables flexible backend selection",
        metadata={"type": "architecture", "domain": "mcp", "importance": 0.9},
        user_id=config.default_user_id,
        project_id=config.default_project_id
    )
    print(f"   Stored memory with ID: {memory_id[:8]}...")
    
    # Store another memory
    memory_id2 = await service.store_memory(
        content="SQLite backend provides lightweight persistence with vector search",
        metadata={"type": "backend", "domain": "storage", "importance": 0.8},
        user_id=config.default_user_id,
        project_id=config.default_project_id
    )
    print(f"   Stored memory with ID: {memory_id2[:8]}...")
    
    # Retrieve memories
    results = await service.retrieve_memory(
        query="architecture",
        user_id=config.default_user_id,
        project_id=config.default_project_id,
        limit=5
    )
    print(f"   Retrieved {len(results)} memories for 'architecture'")
    
    # Step 6: Show available backends and capabilities
    print("\n🧩 Available backends and capabilities:")
    print(f"   Available: {service.get_available_backends()}")
    print(f"   With persistence: {service.has_capability('persistence')}")
    print(f"   With vector search: {service.has_capability('vector_search')}")
    print(f"   With embeddings: {service.has_capability('embeddings')}")
    
    # Step 7: Demonstrate backend management
    print("\n⚙️  Backend management:")
    print(f"   Current active: {service.get_active_backends()}")
    
    # Disable and re-enable
    service.disable_backend("sqlite")
    print(f"   After disabling SQLite: {service.get_active_backends()}")
    
    service.enable_backend("sqlite")
    print(f"   After re-enabling SQLite: {service.get_active_backends()}")
    
    # Step 8: Cleanup
    print("\n🧹 Cleaning up...")
    await service.shutdown()
    
    # Remove demo config
    if config_path.exists():
        config_path.unlink()
        print(f"   Removed config file: {config_path}")
    
    print("\n✨ Demo completed successfully!")
    print("\n💡 Usage:")
    print("   1. Install with memory support: pip install hanzo-mcp[memory]")
    print("   2. Configure backends in ~/.config/hanzo/mcp-settings.json")
    print("   3. Use the memory system with modular backend support")
    print("   4. Enable/disable backends as needed")


if __name__ == "__main__":
    asyncio.run(demo_memory_system())