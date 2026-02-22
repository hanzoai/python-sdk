#!/usr/bin/env python3
"""Test script to verify markdown memory integration."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hanzo_memory.db.local_client import LocalMemoryClient
from hanzo_memory.db.markdown_reader import MarkdownMemoryReader

console = Console()


async def test_markdown_memory():
    """Test markdown memory integration."""
    console.print("\n[bold cyan]Testing Markdown Memory Integration[/bold cyan]\n")

    # Initialize the client with markdown support
    console.print("📂 Initializing local memory client with markdown support...")
    client = LocalMemoryClient(enable_markdown=True)

    # Initialize the database
    await client.initialize()

    # Check for markdown files
    console.print("\n[bold]🔍 Finding markdown files:[/bold]")
    reader = MarkdownMemoryReader()
    md_files = reader.find_markdown_files()

    if not md_files:
        console.print(
            "  [yellow]No markdown files found in watched directories[/yellow]"
        )
        console.print("  Watched directories:")
        for dir in reader.watch_dirs[:5]:
            console.print(f"    - {dir}")
    else:
        table = Table(title="Found Markdown Files")
        table.add_column("File", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Size", style="yellow")

        for file in md_files[:10]:  # Show first 10
            if file.exists():
                size = file.stat().st_size
                size_str = f"{size:,} bytes"
                table.add_row(file.name, str(file.parent), size_str)

        console.print(table)

    # Check imported memories
    console.print("\n[bold]📚 Checking imported memories:[/bold]")

    # Get the markdown import project
    projects = await client.list_projects()
    markdown_project = next(
        (p for p in projects if p.project_id == "markdown_import"), None
    )

    if markdown_project:
        console.print(f"  ✅ Found markdown import project: {markdown_project.name}")

        # Count memories by type
        memories_by_type = {}
        for memory in client.memories.values():
            if memory.get("project_id") == "markdown_import":
                mem_type = memory.get("memory_type", "unknown")
                memories_by_type[mem_type] = memories_by_type.get(mem_type, 0) + 1

        if memories_by_type:
            console.print("\n  [bold]Memory counts by type:[/bold]")
            for mem_type, count in sorted(memories_by_type.items()):
                console.print(f"    {mem_type}: {count}")

            # Show sample memories
            console.print("\n  [bold]Sample imported memories:[/bold]")
            sample_memories = [
                m
                for m in client.memories.values()
                if m.get("project_id") == "markdown_import"
            ][:3]

            for i, memory in enumerate(sample_memories, 1):
                source_file = memory.get("context", {}).get("file_name", "Unknown")
                section_title = memory.get("context", {}).get(
                    "section_title", "No title"
                )
                content_preview = memory.get("content", "")[:100] + "..."
                importance = memory.get("importance", 0)

                panel = Panel(
                    f"[dim]{content_preview}[/dim]\n\n"
                    f"[bold]Source:[/bold] {source_file}\n"
                    f"[bold]Section:[/bold] {section_title}\n"
                    f"[bold]Type:[/bold] {memory.get('memory_type', 'unknown')}\n"
                    f"[bold]Importance:[/bold] {importance:.2f}",
                    title=f"Memory {i}",
                    border_style="blue",
                )
                console.print(panel)
        else:
            console.print(
                "  [yellow]No memories found in markdown import project[/yellow]"
            )
    else:
        console.print("  [yellow]No markdown import project found[/yellow]")

    # Test creating a new memory
    console.print("\n[bold]✏️ Testing memory creation:[/bold]")
    from hanzo_memory.models.memory import MemoryCreate

    test_memory = MemoryCreate(
        content="This is a test memory created from the test script",
        memory_type="test",
        importance=0.5,
        context={"test": True},
        source="test_script",
    )

    created_memory = await client.create_memory(
        test_memory, project_id="test_project", user_id="test_user"
    )

    console.print(f"  ✅ Created test memory with ID: {created_memory.id}")

    # Test searching (without embeddings for now)
    console.print("\n[bold]🔎 Testing memory retrieval:[/bold]")
    recent_memories = await client.get_recent_memories(
        project_id="test_project", user_id="test_user", limit=5
    )

    console.print(f"  Found {len(recent_memories)} recent memories")

    # Clean up
    await client.close()
    console.print("\n[bold green]✅ Test completed successfully![/bold green]")


if __name__ == "__main__":
    asyncio.run(test_markdown_memory())
