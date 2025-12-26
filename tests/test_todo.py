#!/usr/bin/env python
"""Test the todo manager directly."""

import sys
import asyncio
from pathlib import Path

import pytest
from rich.console import Console

# Add hanzo src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pkg" / "hanzo" / "src"))

from hanzo.interactive.todo_manager import TodoManager


async def test_todo():
    console = Console()
    manager = TodoManager(console)

    # Add some todos
    print("Adding todos...")
    todo1 = manager.add_todo(
        title="Implement new feature",
        description="Add support for webhooks",
        priority="high",
        tags=["dev", "backend"],
        due_date="2025-01-15",
    )
    print(f"Added: {todo1.title} (ID: {todo1.id})")

    todo2 = manager.quick_add("Fix bug in auth system #bug #urgent !urgent @today")
    print(f"Added: {todo2.title} (ID: {todo2.id})")

    todo3 = manager.quick_add("Write documentation #docs !low")
    print(f"Added: {todo3.title} (ID: {todo3.id})")

    # Display todos
    print("\nAll Todos:")
    manager.display_todos()

    # Update a todo
    print(f"\nMarking {todo2.id} as in progress...")
    manager.update_todo(todo2.id, status="in_progress")

    # Display filtered todos
    print("\nHigh priority todos:")
    high_priority = manager.list_todos(priority="high")
    manager.display_todos(high_priority, "High Priority")

    # Show statistics
    print("\nStatistics:")
    manager.display_statistics()

    # Show detail
    print(f"\nDetail for {todo1.id}:")
    manager.display_todo_detail(todo1)


if __name__ == "__main__":
    asyncio.run(test_todo())
