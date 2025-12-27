"""Tests for hanzo-tools-llm."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import llm
        assert llm is not None
    
    def test_import_tools(self):
        from hanzo_tools.llm import TOOLS
        assert len(TOOLS) > 0
