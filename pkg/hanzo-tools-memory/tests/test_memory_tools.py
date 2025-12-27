"""Tests for hanzo-tools-memory."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import memory

        assert memory is not None

    def test_import_tools(self):
        from hanzo_tools.memory import TOOLS

        assert len(TOOLS) > 0


class TestMemoryTool:
    """Tests for MemoryTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.memory import TOOLS

        return TOOLS[0]() if TOOLS else None

    def test_has_description(self, tool):
        if tool:
            assert tool.description
