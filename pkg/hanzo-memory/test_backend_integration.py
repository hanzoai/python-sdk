#!/usr/bin/env python3
"""Test backend integration with all components."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.hanzo_memory.db.factory import get_db_client, reset_db_client
from src.hanzo_memory.models.memory import MemoryCreate
from src.hanzo_memory.models.project import ProjectCreate


async def test_local_backend():
    """Test local file backend."""
    reset_db_client()
    client = get_db_client(backend="local")

    # Initialize
    await client.initialize()

    # Create project
    project = ProjectCreate(
        name="Test Project", description="Test project for local backend"
    )
    created_project = await client.create_project(project, user_id="test_user")
    assert created_project.name == "Test Project"

    # Create memory
    memory = MemoryCreate(
        content="Test memory content", memory_type="test", importance=0.5
    )
    created_memory = await client.create_memory(
        memory, project_id=created_project.project_id, user_id="test_user"
    )
    assert created_memory.content == "Test memory content"

    # Get recent memories
    recent = await client.get_recent_memories(
        project_id=created_project.project_id, user_id="test_user", limit=10
    )
    assert len(recent) > 0

    await client.close()
    print("✅ Local backend test passed")


async def test_lancedb_backend():
    """Test LanceDB backend."""
    reset_db_client()

    # Use temporary directory for LanceDB
    with tempfile.TemporaryDirectory() as tmpdir:
        client = get_db_client(
            backend="lancedb", config={"db_path": tmpdir, "enable_markdown": False}
        )

        # Initialize
        await client.initialize()

        # Create project
        project = ProjectCreate(
            name="LanceDB Test", description="Test project for LanceDB"
        )
        created_project = await client.create_project(project, user_id="test_user")
        assert created_project.name == "LanceDB Test"

        # Create memory
        memory = MemoryCreate(
            content="LanceDB test memory",
            memory_type="test",
            importance=0.7,
            embedding=[0.1] * 384,  # Dummy embedding
        )
        created_memory = await client.create_memory(
            memory, project_id=created_project.project_id, user_id="test_user"
        )
        assert created_memory.content == "LanceDB test memory"

        # Search memories (with dummy embedding)
        results = await client.search_memories(
            query_embedding=[0.1] * 384,
            project_id=created_project.project_id,
            user_id="test_user",
            limit=5,
        )
        assert len(results) > 0

        await client.close()
        print("✅ LanceDB backend test passed")


async def test_markdown_import():
    """Test markdown import in both backends."""
    # Test with local backend
    reset_db_client()
    client = get_db_client(backend="local")
    await client.initialize()

    projects = await client.list_projects()
    markdown_project = next(
        (p for p in projects if p.project_id == "markdown_import"), None
    )

    if markdown_project:
        print(f"✅ Local backend found markdown project: {markdown_project.name}")

    await client.close()

    # Test with LanceDB backend
    reset_db_client()
    client = get_db_client(backend="lancedb")
    await client.initialize()

    projects = await client.list_projects()
    markdown_project = next(
        (p for p in projects if p.project_id == "markdown_import"), None
    )

    if markdown_project:
        print(f"✅ LanceDB backend found markdown project: {markdown_project.name}")

    await client.close()


async def test_backend_switching():
    """Test switching between backends."""
    # Start with local
    reset_db_client()
    client1 = get_db_client(backend="local")
    assert client1.__class__.__name__ == "LocalMemoryClient"

    # Switch to LanceDB
    reset_db_client()
    client2 = get_db_client(backend="lancedb")
    assert client2.__class__.__name__ == "LanceDBClient"

    # Back to local
    reset_db_client()
    client3 = get_db_client(backend="local")
    assert client3.__class__.__name__ == "LocalMemoryClient"

    print("✅ Backend switching test passed")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BACKEND INTEGRATION TESTS")
    print("=" * 60)

    try:
        await test_local_backend()
        await test_lancedb_backend()
        await test_markdown_import()
        await test_backend_switching()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
