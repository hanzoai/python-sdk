"""Tests for hanzo-tools-browser."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import browser
        assert browser is not None
    
    def test_import_tools(self):
        from hanzo_tools.browser import TOOLS
        assert len(TOOLS) > 0
    
    def test_import_browser_tool(self):
        from hanzo_tools.browser import BrowserTool
        assert BrowserTool.name == "browser"


class TestBrowserTool:
    """Tests for BrowserTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.browser import BrowserTool
        return BrowserTool()
    
    def test_has_description(self, tool):
        assert tool.description
        assert "browser" in tool.description.lower() or "playwright" in tool.description.lower()
