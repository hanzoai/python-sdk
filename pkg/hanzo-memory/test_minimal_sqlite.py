"""Test to verify SQLite backend works with minimal dependencies."""

import asyncio
import tempfile
from pathlib import Path

from hanzo_memory.memory import memory
from hanzo_memory.models.memory import MemoryCreate


async def test_minimal_sqlite_backend():
    """Test that SQLite backend works with minimal dependencies."""
    print("Testing minimal SQLite backend functionality...")

    # Create a temporary database file for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        # Get SQLite backend
        print("Getting SQLite backend...")
        sqlite_backend = memory["sqlite"]

        # Initialize with temporary path
        sqlite_backend._client = None  # Reset client
        sqlite_backend.config = {"db_path": tmp_path}

        # Initialize the backend
        print("Initializing SQLite backend...")
        await sqlite_backend.initialize()

        print("✅ SQLite backend initialized successfully!")

        # Test creating a simple memory (without relying on embedding service)
        print("Testing memory creation...")
        from hanzo_memory.db.sqlite_client import SQLiteMemoryClient

        client = SQLiteMemoryClient(db_path=tmp_path)

        # Create a memory directly using the client
        import uuid
        from datetime import datetime
        import json

        memory_id = str(uuid.uuid4())
        user_id = "test-user"
        project_id = "test-project"
        content = "This is a test memory for SQLite backend"

        # Add memory without embedding to avoid dependency on embedding service
        result = client.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            embedding=[],  # Empty embedding to avoid embedding service dependency
            metadata={"source": "test"},
            importance=0.8,
        )

        print(f"✅ Memory created with ID: {result['memory_id']}")

        # Test retrieving the memory
        print("Testing memory retrieval...")
        projects = client.get_user_projects(user_id)
        print(f"✅ Found {len(projects)} projects")

        # Close the client
        client.close()

        print("🎉 Minimal SQLite backend test completed successfully!")
        print(
            "✅ SQLite backend works with just plaintext files and minimal dependencies"
        )

    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    asyncio.run(test_minimal_sqlite_backend())
