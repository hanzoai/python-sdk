#!/usr/bin/env python3
"""Test script for update_memory functionality."""

import asyncio
import uuid
from hanzo_memory.memory import memory
from hanzo_memory.models.memory import MemoryCreate


async def test_update_memory():
    """Test the update_memory functionality."""
    print("Testing update_memory functionality...")
    
    # Use local backend for testing
    backend = memory['local']
    await backend.initialize()
    
    # Create a test memory
    test_content = "Original test memory content"
    test_metadata = {"category": "test", "priority": "high"}
    
    memory_create = MemoryCreate(
        content=test_content,
        metadata=test_metadata,
        importance=5.0
    )
    
    created_memory = backend.service.create_memory(
        user_id="test_user",
        project_id="test_project",
        content=test_content,
        metadata=test_metadata,
        importance=5.0
    )
    
    print(f"Created memory: {created_memory.memory_id}")
    print(f"Original content: {created_memory.content}")
    print(f"Original importance: {created_memory.importance}")
    print(f"Original metadata: {created_memory.metadata}")
    
    # Update the memory
    updated_content = "Updated test memory content"
    updated_importance = 8.5
    updated_metadata = {"category": "test", "priority": "critical", "updated": True}
    
    updated_memory = backend.service.update_memory(
        user_id="test_user",
        memory_id=created_memory.memory_id,
        project_id="test_project",
        content=updated_content,
        importance=updated_importance,
        metadata=updated_metadata
    )
    
    if updated_memory:
        print(f"\nSuccessfully updated memory: {updated_memory.memory_id}")
        print(f"Updated content: {updated_memory.content}")
        print(f"Updated importance: {updated_memory.importance}")
        print(f"Updated metadata: {updated_memory.metadata}")
        
        # Verify the update worked
        assert updated_memory.content == updated_content
        assert updated_memory.importance == updated_importance
        assert updated_memory.metadata == updated_metadata
        
        print("\n✅ All assertions passed! Update functionality works correctly.")
    else:
        print("\n❌ Failed to update memory")
    
    # Clean up
    await backend.close()


if __name__ == "__main__":
    asyncio.run(test_update_memory())