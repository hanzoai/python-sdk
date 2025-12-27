"""Tests for hanzo-tools-todo."""
import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_package(self):
        from hanzo_tools import todo
        assert todo is not None
    
    def test_import_tools(self):
        from hanzo_tools.todo import TOOLS
        assert len(TOOLS) > 0
    
    def test_import_todo_tool(self):
        from hanzo_tools.todo import TodoTool
        assert TodoTool.name == "todo"


class TestTodoTool:
    """Tests for TodoTool."""
    
    @pytest.fixture
    def tool(self):
        from hanzo_tools.todo import TodoTool
        return TodoTool()
    
    def test_has_description(self, tool):
        assert tool.description
        assert "todo" in tool.description.lower()
