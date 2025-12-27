"""Tests for hanzo-tools-mcp."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import mcp_tools

        assert mcp_tools is not None

    def test_import_tools(self):
        from hanzo_tools.mcp_tools import TOOLS

        assert len(TOOLS) > 0
