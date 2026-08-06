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
        from hanzo_tools.lsp import LSPTool

        assert LSPTool.name == "lsp"


class TestLSPTool:
    """Tests for LSPTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.lsp import LSPTool

        return LSPTool()

    def test_has_description(self, tool):
        assert tool.description
