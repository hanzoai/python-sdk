"""Tests for hanzo-tools-vector."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import vector
        assert vector is not None
    
    def test_import_tools(self):
        from hanzo_tools.vector import TOOLS
        assert len(TOOLS) > 0
