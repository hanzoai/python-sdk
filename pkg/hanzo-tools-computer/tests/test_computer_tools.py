"""Tests for hanzo-tools-computer."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import computer
        assert computer is not None
    
    def test_import_tools(self):
        from hanzo_tools.computer import TOOLS
        assert len(TOOLS) > 0
    
    def test_import_computer_tool(self):
        from hanzo_tools.computer import ComputerTool
        assert ComputerTool.name == "computer"


class TestComputerTool:
    """Tests for ComputerTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.computer import ComputerTool
        return ComputerTool()
    
    def test_has_description(self, tool):
        assert tool.description
