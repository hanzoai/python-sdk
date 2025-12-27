"""Tests for hanzo-tools-refactor."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import refactor
        assert refactor is not None
    
    def test_import_tools(self):
        from hanzo_tools.refactor import TOOLS
        assert len(TOOLS) > 0
    
    def test_import_refactor_tool(self):
        from hanzo_tools.refactor import RefactorTool
        assert RefactorTool.name == "refactor"


class TestRefactorTool:
    """Tests for RefactorTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.refactor import RefactorTool
        return RefactorTool()
    
    def test_has_description(self, tool):
        assert tool.description
        assert "refactor" in tool.description.lower()
