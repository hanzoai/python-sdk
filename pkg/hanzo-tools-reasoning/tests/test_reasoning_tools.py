"""Tests for hanzo-tools-reasoning."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import reasoning
        assert reasoning is not None
    
    def test_import_tools(self):
        from hanzo_tools.reasoning import TOOLS
        assert len(TOOLS) >= 2  # think, critic
    
    def test_import_think_tool(self):
        from hanzo_tools.reasoning import ThinkTool
        assert ThinkTool.name == "think"
    
    def test_import_critic_tool(self):
        from hanzo_tools.reasoning import CriticTool
        assert CriticTool.name == "critic"


class TestThinkTool:
    """Tests for ThinkTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.reasoning import ThinkTool
        return ThinkTool()
    
    def test_has_description(self, tool):
        assert tool.description
        assert "think" in tool.description.lower()


class TestCriticTool:
    """Tests for CriticTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.reasoning import CriticTool
        return CriticTool()
    
    def test_has_description(self, tool):
        assert tool.description
        assert "critic" in tool.description.lower()
