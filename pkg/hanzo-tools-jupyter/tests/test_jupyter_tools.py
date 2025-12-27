"""Tests for hanzo-tools-jupyter."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import jupyter

        assert jupyter is not None

    def test_import_tools(self):
        from hanzo_tools.jupyter import TOOLS

        assert len(TOOLS) > 0
