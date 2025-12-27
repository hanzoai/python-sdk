"""Tests for hanzo-tools-fs."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import fs

        assert fs is not None

    def test_import_tools(self):
        from hanzo_tools.fs import TOOLS

        assert len(TOOLS) > 0

    def test_import_read_tool(self):
        from hanzo_tools.fs import ReadTool

        assert ReadTool.name == "read"

    def test_import_write_tool(self):
        from hanzo_tools.fs import WriteTool

        assert WriteTool.name == "write"

    def test_import_edit_tool(self):
        from hanzo_tools.fs import EditTool

        assert EditTool.name == "edit"


class TestReadTool:
    """Tests for ReadTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.fs import ReadTool

        return ReadTool()

    def test_has_description(self, tool):
        assert tool.description
        assert "read" in tool.description.lower()


class TestWriteTool:
    """Tests for WriteTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.fs import WriteTool

        return WriteTool()

    def test_has_description(self, tool):
        assert tool.description
        assert "write" in tool.description.lower()
