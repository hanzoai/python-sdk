"""Tests for hanzo-tools-editor."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import editor
        assert editor is not None
    
    def test_import_tools(self):
        from hanzo_tools.editor import TOOLS
        assert len(TOOLS) > 0
