"""Test all hanzo-tools-* packages import and register correctly."""

import asyncio
import time
import pytest


class TestToolPackages:
    """Test that all tool packages import correctly."""

    def test_core_imports(self):
        """Test hanzo-tools-core imports."""
        from hanzo_tools.core import BaseTool, ToolContext
        from hanzo_tools.core.permissions import PermissionManager
        from hanzo_tools.core.decorators import auto_timeout
        assert BaseTool is not None
        assert ToolContext is not None
        assert PermissionManager is not None
        assert auto_timeout is not None

    def test_filesystem_tools(self):
        """Test hanzo-tools-filesystem has 7 tools."""
        from hanzo_tools.filesystem import TOOLS
        assert len(TOOLS) == 7
        names = {t.name for t in TOOLS}
        expected = {'read', 'write', 'edit', 'tree', 'find', 'search', 'ast'}
        assert names == expected

    def test_shell_tools(self):
        """Test hanzo-tools-shell has 7 tools."""
        from hanzo_tools.shell import TOOLS
        assert len(TOOLS) == 7
        names = {t.name for t in TOOLS}
        expected = {'dag', 'ps', 'zsh', 'shell', 'npx', 'uvx', 'open'}
        assert names == expected

    def test_memory_tools(self):
        """Test hanzo-tools-memory has 9 tools."""
        from hanzo_tools.memory import TOOLS
        assert len(TOOLS) == 9

    def test_todo_tools(self):
        """Test hanzo-tools-todo has 1 tool."""
        from hanzo_tools.todo import TOOLS
        assert len(TOOLS) == 1
        assert TOOLS[0].name == 'todo'

    def test_reasoning_tools(self):
        """Test hanzo-tools-reasoning has 2 tools."""
        from hanzo_tools.reasoning import TOOLS
        assert len(TOOLS) == 2
        names = {t.name for t in TOOLS}
        assert names == {'think', 'critic'}

    def test_lsp_tools(self):
        """Test hanzo-tools-lsp has 1 tool."""
        from hanzo_tools.lsp import TOOLS
        assert len(TOOLS) == 1
        assert TOOLS[0].name == 'lsp'

    def test_refactor_tools(self):
        """Test hanzo-tools-refactor has 1 tool."""
        from hanzo_tools.refactor import TOOLS
        assert len(TOOLS) == 1
        assert TOOLS[0].name == 'refactor'

    def test_database_tools(self):
        """Test hanzo-tools-database has 8 tools."""
        from hanzo_tools.database import TOOLS
        assert len(TOOLS) == 8

    def test_agent_tools(self):
        """Test hanzo-tools-agent has 12 tools."""
        from hanzo_tools.agent import TOOLS
        assert len(TOOLS) == 12

    def test_jupyter_tools(self):
        """Test hanzo-tools-jupyter has 1 tool."""
        from hanzo_tools.jupyter import TOOLS
        assert len(TOOLS) == 1

    def test_editor_tools(self):
        """Test hanzo-tools-editor has 3 tools."""
        from hanzo_tools.editor import TOOLS
        assert len(TOOLS) == 3

    def test_browser_tools(self):
        """Test hanzo-tools-browser has 1 tool."""
        from hanzo_tools.browser import TOOLS
        assert len(TOOLS) == 1


class TestToolImportSpeed:
    """Test that tool imports are fast (no blocking)."""

    @pytest.mark.parametrize("module,max_time", [
        ("hanzo_tools.core", 1.0),
        ("hanzo_tools.filesystem", 1.0),
        ("hanzo_tools.shell", 1.0),
        ("hanzo_tools.memory", 1.0),
        ("hanzo_tools.todo", 1.0),
        ("hanzo_tools.reasoning", 1.0),
        ("hanzo_tools.lsp", 1.0),
        ("hanzo_tools.refactor", 1.0),
        ("hanzo_tools.database", 1.0),
        ("hanzo_tools.jupyter", 1.0),
        ("hanzo_tools.editor", 1.0),
        ("hanzo_tools.browser", 1.0),
        ("hanzo_tools.agent", 2.0),  # Agent has litellm, allow more time
    ])
    def test_import_speed(self, module, max_time):
        """Test that imports complete quickly."""
        import importlib
        start = time.time()
        importlib.import_module(module)
        elapsed = time.time() - start
        assert elapsed < max_time, f"{module} took {elapsed:.2f}s (max {max_time}s)"


class TestToolAsync:
    """Test that all tools have async call methods."""

    def test_all_tools_async(self):
        """Verify all tool .call() methods are async."""
        packages = [
            'hanzo_tools.filesystem',
            'hanzo_tools.shell',
            'hanzo_tools.memory',
            'hanzo_tools.todo',
            'hanzo_tools.reasoning',
            'hanzo_tools.lsp',
            'hanzo_tools.refactor',
            'hanzo_tools.database',
            'hanzo_tools.agent',
            'hanzo_tools.jupyter',
            'hanzo_tools.editor',
            'hanzo_tools.browser',
        ]
        
        for pkg_name in packages:
            import importlib
            pkg = importlib.import_module(pkg_name)
            tools = getattr(pkg, 'TOOLS', [])
            for tool in tools:
                if hasattr(tool, 'call'):
                    assert asyncio.iscoroutinefunction(tool.call), \
                        f"{pkg_name}.{tool.name}.call() is not async"


class TestTotalToolCount:
    """Test total tool count across all packages."""

    def test_total_53_tools(self):
        """Verify we have exactly 53 tools across all packages."""
        packages = [
            ('hanzo_tools.filesystem', 7),
            ('hanzo_tools.shell', 7),
            ('hanzo_tools.browser', 1),
            ('hanzo_tools.memory', 9),
            ('hanzo_tools.todo', 1),
            ('hanzo_tools.reasoning', 2),
            ('hanzo_tools.lsp', 1),
            ('hanzo_tools.refactor', 1),
            ('hanzo_tools.database', 8),
            ('hanzo_tools.agent', 12),
            ('hanzo_tools.jupyter', 1),
            ('hanzo_tools.editor', 3),
        ]
        
        total = 0
        for pkg_name, expected_count in packages:
            import importlib
            pkg = importlib.import_module(pkg_name)
            tools = getattr(pkg, 'TOOLS', [])
            actual = len(tools)
            assert actual == expected_count, \
                f"{pkg_name}: expected {expected_count} tools, got {actual}"
            total += actual
        
        assert total == 53, f"Expected 53 total tools, got {total}"
