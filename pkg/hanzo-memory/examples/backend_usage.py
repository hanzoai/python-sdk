#!/usr/bin/env python3
"""Examples of using different memory backends with the new accessor syntax."""

import asyncio
from hanzo_memory.memory import memory
from hanzo_memory.models.memory import MemoryCreate
from hanzo_memory.models.project import ProjectCreate


async def example_lancedb():
    """Example using LanceDB for vector search."""
    print("\n🚀 LanceDB Example - Vector Search")
    print("-" * 40)

    # Access LanceDB backend using dictionary syntax
    lance = memory["lancedb"]
    await lance.initialize()

    # Create a project
    project = ProjectCreate(
        name="AI Research", description="Storing AI research notes with embeddings"
    )
    proj = await lance.client.create_project(project, user_id="researcher")

    # Store memories with embeddings (normally would use real embeddings)
    memories = [
        "Transformers revolutionized NLP with self-attention mechanisms",
        "GPT models use decoder-only architecture for text generation",
        "BERT uses bidirectional training for better context understanding",
        "Vision transformers apply attention to image patches",
    ]

    for content in memories:
        mem = MemoryCreate(
            content=content,
            memory_type="research",
            importance=0.9,
            embedding=[0.1] * 384,  # Dummy embedding
        )
        await lance.client.create_memory(mem, proj.project_id, "researcher")

    print("✅ Stored research memories with embeddings")

    # Search with vector similarity
    results = await lance.client.search_memories_async(
        query_embedding=[0.1] * 384,  # Would use real query embedding
        project_id=proj.project_id,
        user_id="researcher",
        limit=3,
    )
    print(f"✅ Found {len(results)} similar memories")

    await lance.close()


async def example_kuzudb():
    """Example using KuzuDB for graph relationships."""
    print("\n🕸️ KuzuDB Example - Graph Relationships")
    print("-" * 40)

    try:
        # Access KuzuDB backend using attribute syntax
        kuzu = memory.kuzudb
        await kuzu.initialize()

        # Create a project
        project = ProjectCreate(
            name="Knowledge Graph", description="Building connected knowledge"
        )
        proj = await kuzu.client.create_project(project, user_id="analyst")

        # Store interconnected memories
        memories = [
            ("Python is a programming language", "concept"),
            ("Django is a Python web framework", "framework"),
            ("Flask is another Python web framework", "framework"),
            ("Machine learning often uses Python", "application"),
        ]

        memory_ids = []
        for content, mem_type in memories:
            mem = MemoryCreate(
                content=content,
                memory_type=mem_type,
                importance=0.7,
                embedding=[0.2] * 384,  # Dummy embedding
            )
            created = await kuzu.client.create_memory(mem, proj.project_id, "analyst")
            memory_ids.append(created.memory_id)

        print("✅ Created graph of connected memories")

        # Get related memories (KuzuDB specific feature)
        if hasattr(kuzu.client, "get_related_memories"):
            related = kuzu.client.get_related_memories(memory_ids[0])
            print(f"✅ Found {len(related)} related memories")

        # Get memory graph
        if hasattr(kuzu.client, "get_memory_graph"):
            graph = kuzu.client.get_memory_graph(proj.project_id, depth=2)
            print(f"✅ Retrieved graph with {len(graph.get('nodes', []))} nodes")

        await kuzu.close()

    except ImportError:
        print("❌ KuzuDB not installed. Install with: pip install kuzu")


async def example_local():
    """Example using local storage for development."""
    print("\n📁 Local Storage Example - Simple Development")
    print("-" * 40)

    # Access local backend using context manager
    async with memory.use("local", config={"enable_markdown": False}) as local:
        # Create a project
        project = ProjectCreate(
            name="Dev Notes", description="Quick notes during development"
        )
        proj = await local.client.create_project(project, user_id="developer")

        # Store simple memories
        notes = [
            "TODO: Refactor the authentication module",
            "BUG: Memory leak in background worker",
            "IDEA: Add caching layer for API responses",
        ]

        for note in notes:
            mem = MemoryCreate(content=note, memory_type="note", importance=0.5)
            await local.client.create_memory(mem, proj.project_id, "developer")

        print("✅ Stored development notes locally")

        # Get recent memories
        recent = await local.client.get_recent_memories(
            project_id=proj.project_id, user_id="developer", limit=5
        )
        print(f"✅ Retrieved {len(recent)} recent notes")

    print("✅ Local backend closed automatically (context manager)")


async def example_backend_comparison():
    """Compare different backends for the same use case."""
    print("\n⚖️ Backend Comparison")
    print("-" * 40)

    # List all available backends
    backends = memory.backends()
    print(f"Available backends: {list(backends.keys())}")

    for name, info in backends.items():
        print(f"\n{name.upper()}:")
        print(f"  {info['description']}")
        print(f"  Capabilities: {', '.join(info['capabilities'][:3])}...")


async def example_advanced_patterns():
    """Advanced usage patterns."""
    print("\n🎯 Advanced Patterns")
    print("-" * 40)

    # Pattern 1: Backend selection based on capability
    print("\n1. Capability-based selection:")
    backends = memory.backends()

    # Find backend with vector search
    vector_backends = [
        name
        for name, info in backends.items()
        if "vector_search" in info["capabilities"]
    ]
    print(f"  Vector search backends: {vector_backends}")

    # Find backend with graph queries
    graph_backends = [
        name
        for name, info in backends.items()
        if "graph_queries" in info["capabilities"]
    ]
    print(f"  Graph query backends: {graph_backends}")

    # Pattern 2: Multi-backend usage
    print("\n2. Using multiple backends:")

    # Use LanceDB for vectors, local for quick notes
    lance = memory["lancedb"]
    local = memory["local"]

    print("  ✅ Can use multiple backends simultaneously")

    # Pattern 3: Dynamic backend switching
    print("\n3. Dynamic backend switching:")

    backend_name = "lancedb" if "lancedb" in backends else "local"
    selected = memory[backend_name]
    print(f"  ✅ Dynamically selected: {backend_name}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("MEMORY BACKEND USAGE EXAMPLES")
    print("=" * 60)

    # Run examples
    await example_lancedb()
    await example_local()
    await example_kuzudb()
    await example_backend_comparison()
    await example_advanced_patterns()

    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("\n📚 Quick Reference:")
    print("  memory['lancedb']     - Vector search, embeddings")
    print("  memory['kuzudb']      - Graph relationships")
    print("  memory['infinity']    - High performance")
    print("  memory.local          - Simple file storage")
    print("\n  async with memory.use('backend') as mem:")
    print("      # Auto initialize and close")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
