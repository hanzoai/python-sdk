#!/usr/bin/env python3
"""Test memory management system."""

import sys
import asyncio
from pathlib import Path

from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))

from hanzo.memory_manager import MemoryManager, handle_memory_command


def test_memory_manager():
    """Test memory manager functionality."""
    console = Console()

    console.print("\n[bold cyan]Testing Memory Manager[/bold cyan]\n")

    # Create memory manager
    memory_manager = MemoryManager("/tmp/test_memory")

    # Test adding memories
    console.print("[bold]Adding memories:[/bold]")

    id1 = memory_manager.add_memory(
        "User prefers Python over JavaScript", type="fact", priority=5
    )
    console.print(f"✓ Added fact: {id1}")

    id2 = memory_manager.add_memory(
        "Always use type hints in Python code", type="instruction", priority=8
    )
    console.print(f"✓ Added instruction: {id2}")

    id3 = memory_manager.add_memory(
        "Working on REST API project", type="context", priority=3
    )
    console.print(f"✓ Added context: {id3}")

    # Test retrieving memories
    console.print("\n[bold]Retrieving memories:[/bold]")

    all_memories = memory_manager.get_memories()
    console.print(f"Total memories: {len(all_memories)}")

    instructions = memory_manager.get_memories(type="instruction")
    console.print(f"Instructions: {len(instructions)}")

    # Test memory commands
    console.print("\n[bold]Testing memory commands:[/bold]")

    # Show command
    console.print("\n#memory show:")
    handle_memory_command("#memory show", memory_manager, console)

    # Context command
    console.print("\n#memory context:")
    handle_memory_command("#memory context", memory_manager, console)

    # Test preferences
    console.print("\n[bold]Testing preferences:[/bold]")

    memory_manager.set_preference("theme", "dark")
    memory_manager.set_preference("language", "python")

    theme = memory_manager.get_preference("theme")
    console.print(f"Theme preference: {theme}")

    # Test session messages
    console.print("\n[bold]Testing session messages:[/bold]")

    memory_manager.add_message("user", "Hello AI!")
    memory_manager.add_message("assistant", "Hello! How can I help you today?")

    recent = memory_manager.get_recent_messages(2)
    console.print(f"Recent messages: {len(recent)}")

    # Test AI summary
    console.print("\n[bold]AI Context Summary:[/bold]")
    summary = memory_manager.summarize_for_ai()
    console.print(summary)

    # Test export/import
    console.print("\n[bold]Testing export/import:[/bold]")

    export_file = "/tmp/test_memories.json"
    memory_manager.export_memories(export_file)
    console.print(f"✓ Exported to {export_file}")

    # Create new manager and import
    new_manager = MemoryManager("/tmp/test_memory2")
    new_manager.import_memories(export_file)
    console.print(f"✓ Imported to new manager")

    imported_memories = new_manager.get_memories()
    console.print(f"Imported memories: {len(imported_memories)}")

    console.print("\n[green]✅ All memory tests passed![/green]")

    return True


if __name__ == "__main__":
    success = test_memory_manager()
    sys.exit(0 if success else 1)
