#!/usr/bin/env python3
"""Test memory management system."""

import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# Add hanzo src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pkg" / "hanzo" / "src"))

from hanzo.memory_manager import MemoryManager, handle_memory_command


class TestMemoryManager:
    """Test memory manager functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create a memory manager instance."""
        return MemoryManager(temp_dir)

    def test_add_memory_fact(self, memory_manager):
        """Test adding a fact memory."""
        memory_id = memory_manager.add_memory("User prefers Python over JavaScript", type="fact", priority=5)
        assert memory_id is not None
        assert len(memory_id) > 0

    def test_add_memory_instruction(self, memory_manager):
        """Test adding an instruction memory."""
        memory_id = memory_manager.add_memory("Always use type hints in Python code", type="instruction", priority=8)
        assert memory_id is not None

    def test_add_memory_context(self, memory_manager):
        """Test adding a context memory."""
        memory_id = memory_manager.add_memory("Working on REST API project", type="context", priority=3)
        assert memory_id is not None

    def test_get_all_memories(self, memory_manager):
        """Test retrieving all memories."""
        # Get initial count (memory manager may start with system memories)
        initial_count = len(memory_manager.get_memories())

        memory_manager.add_memory("Memory 1", type="fact", priority=5)
        memory_manager.add_memory("Memory 2", type="instruction", priority=8)
        memory_manager.add_memory("Memory 3", type="context", priority=3)

        all_memories = memory_manager.get_memories()
        assert len(all_memories) == initial_count + 3

    def test_get_memories_by_type(self, memory_manager):
        """Test retrieving memories filtered by type."""
        # Get initial count for instruction type
        initial_instruction_count = len(memory_manager.get_memories(type="instruction"))

        memory_manager.add_memory("Fact 1", type="fact", priority=5)
        memory_manager.add_memory("Instruction 1", type="instruction", priority=8)
        memory_manager.add_memory("Instruction 2", type="instruction", priority=6)

        instructions = memory_manager.get_memories(type="instruction")
        assert len(instructions) == initial_instruction_count + 2

    def test_set_and_get_preference(self, memory_manager):
        """Test setting and getting preferences."""
        memory_manager.set_preference("theme", "dark")
        memory_manager.set_preference("language", "python")

        theme = memory_manager.get_preference("theme")
        assert theme == "dark"

        language = memory_manager.get_preference("language")
        assert language == "python"

    def test_add_and_get_messages(self, memory_manager):
        """Test adding and retrieving session messages."""
        memory_manager.add_message("user", "Hello AI!")
        memory_manager.add_message("assistant", "Hello! How can I help you today?")

        recent = memory_manager.get_recent_messages(2)
        assert len(recent) == 2

    def test_summarize_for_ai(self, memory_manager):
        """Test AI summary generation."""
        memory_manager.add_memory("Test memory", type="fact", priority=5)
        summary = memory_manager.summarize_for_ai()
        assert summary is not None
        assert isinstance(summary, str)

    def test_export_import_memories(self, temp_dir, memory_manager):
        """Test exporting and importing memories."""
        # Add some memories
        memory_manager.add_memory("Memory 1", type="fact", priority=5)
        memory_manager.add_memory("Memory 2", type="instruction", priority=8)

        # Export
        export_file = f"{temp_dir}/test_export.json"
        memory_manager.export_memories(export_file)
        assert Path(export_file).exists()

        # Import to new manager
        new_temp_dir = tempfile.mkdtemp()
        try:
            new_manager = MemoryManager(new_temp_dir)
            new_manager.import_memories(export_file)

            imported_memories = new_manager.get_memories()
            assert len(imported_memories) >= 2
        finally:
            shutil.rmtree(new_temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
