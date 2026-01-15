#!/usr/bin/env python3
"""Test script for hybrid memory system."""

import os
import sys
import asyncio
from pathlib import Path

# Add the tools package to Python path
sys.path.insert(0, str(Path(__file__).parent / "hanzo_tools"))

from hanzo_tools.core import PermissionManager
from hanzo_tools.database.memory_manager import MemoryManager
from hanzo_tools.database.memory_tool import MemoryTool


async def test_memory_system():
    """Test the hybrid memory system."""
    print("🧠 Testing Hybrid Memory System")
    print("=" * 50)
    
    # Create permission manager (allow all for testing)
    permission_manager = PermissionManager(allowed_paths=["/"])
    
    # Create memory manager
    memory_manager = MemoryManager(permission_manager)
    
    # Create memory tool
    memory_tool = MemoryTool(permission_manager)
    
    # Test project path
    test_project = Path("/tmp/test_hanzo_project")
    test_project.mkdir(exist_ok=True)
    os.chdir(test_project)
    
    print(f"📁 Test project: {test_project}")
    
    # Mock MCP context (simplified)
    class MockContext:
        pass
    
    ctx = MockContext()
    
    # Test 1: Initialize memory structure
    print("\n1. 📋 Initialize memory structure...")
    from hanzo_tools.database.init_memory import init_project_memory, init_global_memory
    
    try:
        init_global_memory()
        init_project_memory(str(test_project))
        print("✓ Memory structure initialized")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
    
    # Test 2: Write memory files
    print("\n2. ✏️  Write memory files...")
    
    try:
        # Global memory
        result = await memory_tool.call(ctx, 
            action="write",
            file_path="test_rules.md", 
            content="# Test Rules\n\nThis is a test rule file.",
            scope="global",
            category="test"
        )
        print(f"✓ Global write: {result}")
        
        # Project memory
        result = await memory_tool.call(ctx,
            action="write",
            file_path="test_architecture.md",
            content="# Test Architecture\n\nThis describes the test architecture.",
            scope="project",
            category="architecture"
        )
        print(f"✓ Project write: {result}")
        
    except Exception as e:
        print(f"✗ Write failed: {e}")
    
    # Test 3: Read memory files
    print("\n3. 📖 Read memory files...")
    
    try:
        result = await memory_tool.call(ctx,
            action="read",
            file_path="test_rules.md",
            scope="global"
        )
        print("✓ Global read successful")
        print(f"Content preview: {result[:100]}...")
        
        result = await memory_tool.call(ctx,
            action="read", 
            file_path="test_architecture.md",
            scope="project"
        )
        print("✓ Project read successful")
        print(f"Content preview: {result[:100]}...")
        
    except Exception as e:
        print(f"✗ Read failed: {e}")
    
    # Test 4: Append to memory files
    print("\n4. ➕ Append to memory files...")
    
    try:
        result = await memory_tool.call(ctx,
            action="append",
            file_path="sessions/test_session.md",
            content="This is a test session entry with important insights.",
            scope="project",
            category="session"
        )
        print(f"✓ Append: {result}")
    except Exception as e:
        print(f"✗ Append failed: {e}")
    
    # Test 5: Create structured memories
    print("\n5. 🗃️  Create structured memories...")
    
    try:
        result = await memory_tool.call(ctx,
            action="create",
            content="This is a test structured memory with high importance",
            category="test",
            importance=8,
            scope="project"
        )
        print(f"✓ Create structured: {result}")
    except Exception as e:
        print(f"✗ Create failed: {e}")
    
    # Test 6: Search memories
    print("\n6. 🔍 Search memories...")
    
    try:
        result = await memory_tool.call(ctx,
            action="search",
            content="test",
            scope="both",
            limit=5
        )
        print("✓ Search successful")
        print(f"Results preview: {result[:300]}...")
    except Exception as e:
        print(f"✗ Search failed: {e}")
    
    # Test 7: List memory files
    print("\n7. 📋 List memory files...")
    
    try:
        result = await memory_tool.call(ctx,
            action="list",
            scope="both"
        )
        print("✓ List successful")
        print(f"List preview: {result[:200]}...")
    except Exception as e:
        print(f"✗ List failed: {e}")
    
    # Test 8: Get statistics
    print("\n8. 📊 Get memory statistics...")
    
    try:
        result = await memory_tool.call(ctx,
            action="stats",
            scope="both"
        )
        print("✓ Stats successful")
        print(f"Stats preview: {result[:300]}...")
    except Exception as e:
        print(f"✗ Stats failed: {e}")
    
    # Test 9: Test database features
    print("\n9. 🗄️  Test database features...")
    
    try:
        # Test FTS5 search
        results = memory_manager.search_memories("test architecture", "both", str(test_project))
        print(f"✓ FTS5 search found {len(results)} results")
        
        # Get stats
        stats = memory_manager.get_memory_stats("both", str(test_project))
        print(f"✓ Database stats: {stats['markdown_files']} markdown files, {stats['structured_memories']} memories")
        
        # Test sqlite-vec availability
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            conn.enable_load_extension(True)
            conn.load_extension("vec0")
            conn.close()
            print("✓ sqlite-vec extension available")
        except:
            print("⚠️  sqlite-vec extension not available (optional)")
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Memory system test completed!")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(test_project)
        print(f"🧹 Cleaned up test project: {test_project}")
    except:
        pass


if __name__ == "__main__":
    asyncio.run(test_memory_system())