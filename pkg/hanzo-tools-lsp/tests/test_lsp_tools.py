"""Tests for hanzo-tools-lsp."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import lsp

        assert lsp is not None

    def test_import_tools(self):
        from hanzo_tools.lsp import TOOLS

        assert len(TOOLS) > 0

    def test_import_lsp_tool(self):
        from hanzo_tools.lsp import LspTool

        assert LspTool.name == "lsp"


class TestLspTool:
    """Tests for LspTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.lsp import LspTool

        return LspTool()

    def test_has_description(self, tool):
        assert tool.description
