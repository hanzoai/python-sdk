"""Test script to verify SQLite memory backend functionality."""

import asyncio
import tempfile
from pathlib import Path

from hanzo_memory.memory import memory
from hanzo_memory.models.memory import MemoryCreate


async def test_sqlite_backend():
    """Test SQLite memory backend."""
    print("\n[bold cyan]Testing SQLite Memory Backend[/bold cyan]\n")

    # Create a temporary database file for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        # Get SQLite backend
        print("📂 Getting SQLite backend...")
        sqlite_backend = memory["sqlite"]  # Use indexing instead of attribute access

        # Initialize with temporary path
        sqlite_backend._client = None  # Reset client
        sqlite_backend.config = {"db_path": tmp_path}

        # Initialize the backend
        print("🔌 Initializing SQLite backend...")
        await sqlite_backend.initialize()

        # Test creating a memory
        print("📝 Creating a test memory...")
        memory_create = MemoryCreate(
            content="This is a test memory for SQLite backend",
            memory_type="test",
            importance=0.8,
            context={"test": True},
            metadata={"source": "test"},
        )

        created_memory = await sqlite_backend.service.create_memory(
            memory=memory_create, project_id="test-project", user_id="test-user"
        )

        print(f"✅ Created memory with ID: {created_memory.id}")

        # Test searching for the memory
        print("🔍 Testing memory search...")
        search_results = await sqlite_backend.service.search_memories(
            query="test memory", project_id="test-project", user_id="test-user", limit=5
        )

        print(f"✅ Found {len(search_results)} memories")
        if search_results:
            print(f"   First result: {search_results[0].memory.content[:50]}...")

        # Test creating a project
        print("📁 Creating a test project...")
        from hanzo_memory.models.project import ProjectCreate

        project_create = ProjectCreate(
            name="Test Project",
            description="A test project for SQLite backend",
            metadata={"test": True},
        )

        created_project = await sqlite_backend.service.db.create_project(
            project_id="test-project",
            user_id="test-user",
            name="Test Project",
            description="A test project for SQLite backend",
            metadata={"test": True},
        )

        print(f"✅ Created project: {created_project['name']}")

        # Test getting user projects
        print("📋 Getting user projects...")
        user_projects = await sqlite_backend.service.db.get_user_projects("test-user")
        print(f"✅ Found {len(user_projects)} projects")

        # Close the backend
        print("🛑 Closing SQLite backend...")
        await sqlite_backend.close()

        print("\n🎉 SQLite backend test completed successfully!")

    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    asyncio.run(test_sqlite_backend())
