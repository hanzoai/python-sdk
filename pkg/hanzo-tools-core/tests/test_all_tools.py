"""Test all hanzo-tools-* packages import and register correctly."""

import sys
import time
import asyncio

import pytest


def _module_installed(module_name: str) -> bool:
    """Check if a module is installed."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


class TestToolPackages:
    """Test that all tool packages import correctly."""

    def test_core_imports(self):
        """Test hanzo-tools-core imports."""
        from hanzo_tools.core import BaseTool, ToolContext
        from hanzo_tools.core.decorators import auto_timeout
        from hanzo_tools.core.permissions import PermissionManager

        assert BaseTool is not None
        assert ToolContext is not None
        assert PermissionManager is not None
        assert auto_timeout is not None

    def test_fs_tools(self):
        """Test hanzo-tools-fs has 7 tools."""
        from hanzo_tools.fs import TOOLS

        assert len(TOOLS) == 7
        names = {t.name for t in TOOLS}
        expected = {"read", "write", "edit", "tree", "find", "search", "ast"}
        assert names == expected

    def test_shell_tools(self):
        """Test hanzo-tools-shell has 11 tools."""
        from hanzo_tools.shell import TOOLS

        assert len(TOOLS) == 11
        names = {t.name for t in TOOLS}
        expected = {"dag", "ps", "zsh", "bash", "shell", "npx", "uvx", "open", "curl", "jq", "wget"}
        assert names == expected

    def test_memory_tools(self):
        """Test hanzo-tools-memory has 9 tools."""
        from hanzo_tools.memory import TOOLS

        assert len(TOOLS) == 9

    def test_todo_tools(self):
        """Test hanzo-tools-todo has 1 tool."""
        from hanzo_tools.todo import TOOLS

        assert len(TOOLS) == 1
        assert TOOLS[0].name == "todo"

    def test_reasoning_tools(self):
        """Test hanzo-tools-reasoning has 2 tools."""
        from hanzo_tools.reasoning import TOOLS

        assert len(TOOLS) == 2
        names = {t.name for t in TOOLS}
        assert names == {"think", "critic"}

    def test_lsp_tools(self):
        """Test hanzo-tools-lsp has 1 tool."""
        from hanzo_tools.lsp import TOOLS

        assert len(TOOLS) == 1
        assert TOOLS[0].name == "lsp"

    def test_refactor_tools(self):
        """Test hanzo-tools-refactor has 1 tool."""
        from hanzo_tools.refactor import TOOLS

        assert len(TOOLS) == 1
        assert TOOLS[0].name == "refactor"

    def test_database_tools(self):
        """Test hanzo-tools-database has 8 tools."""
        from hanzo_tools.database import TOOLS

        assert len(TOOLS) == 8

    def test_agent_tools(self):
        """Test hanzo-tools-agent has 3 tools.

        Core tools: AgentTool, IChingTool, ReviewTool
        """
        from hanzo_tools.agent import TOOLS

        assert len(TOOLS) == 3, f"Expected 3 agent tools, got {len(TOOLS)}"
        names = {t.name for t in TOOLS}
        assert names == {"agent", "iching", "review"}

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

    @pytest.mark.skipif(
        not _module_installed("hanzo_tools.config"),
        reason="hanzo-tools-config not installed",
    )
    def test_config_tools(self):
        """Test hanzo-tools-config has 2 tools."""
        from hanzo_tools.config import TOOLS

        assert len(TOOLS) == 2

    @pytest.mark.skipif(
        not _module_installed("hanzo_tools.mcp_tools"),
        reason="hanzo-tools-mcp not installed",
    )
    def test_mcp_tools(self):
        """Test hanzo-tools-mcp has 4 tools."""
        from hanzo_tools.mcp_tools import TOOLS

        assert len(TOOLS) == 4

    @pytest.mark.skipif(
        not _module_installed("hanzo_tools.llm"),
        reason="hanzo-tools-llm not installed",
    )
    def test_llm_tools(self):
        """Test hanzo-tools-llm imports (tools depend on litellm)."""
        from hanzo_tools.llm import TOOLS, LLM_AVAILABLE

        # LLM tools are optional, depend on litellm
        if LLM_AVAILABLE:
            assert len(TOOLS) >= 1
        else:
            assert len(TOOLS) == 0

    @pytest.mark.skipif(
        not _module_installed("hanzo_tools.vector"),
        reason="hanzo-tools-vector not installed",
    )
    def test_vector_tools(self):
        """Test hanzo-tools-vector imports (tools depend on heavy deps)."""
        from hanzo_tools.vector import TOOLS, VECTOR_AVAILABLE

        # Vector tools are optional, depend on faiss/qdrant
        if VECTOR_AVAILABLE:
            assert len(TOOLS) >= 1
        else:
            assert len(TOOLS) == 0


# Required packages for import speed tests
REQUIRED_IMPORT_MODULES = [
    ("hanzo_tools.core", 1.0),
    ("hanzo_tools.fs", 1.0),
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
]

# Optional packages that may not be installed
OPTIONAL_IMPORT_MODULES = [
    ("hanzo_tools.config", 1.0),
    ("hanzo_tools.mcp_tools", 1.0),
    ("hanzo_tools.llm", 2.0),  # LLM has litellm, allow more time
    ("hanzo_tools.vector", 2.0),  # Vector has heavy deps
]


class TestToolImportSpeed:
    """Test that tool imports are fast (no blocking)."""

    @pytest.mark.parametrize("module,max_time", REQUIRED_IMPORT_MODULES)
    def test_import_speed_required(self, module, max_time):
        """Test that required imports complete quickly."""
        import importlib

        start = time.time()
        importlib.import_module(module)
        elapsed = time.time() - start
        assert elapsed < max_time, f"{module} took {elapsed:.2f}s (max {max_time}s)"

    @pytest.mark.parametrize("module,max_time", OPTIONAL_IMPORT_MODULES)
    def test_import_speed_optional(self, module, max_time):
        """Test that optional imports complete quickly (if installed)."""
        if not _module_installed(module):
            pytest.skip(f"{module} not installed")
        import importlib

        start = time.time()
        importlib.import_module(module)
        elapsed = time.time() - start
        assert elapsed < max_time, f"{module} took {elapsed:.2f}s (max {max_time}s)"


# Packages that must always be testable
REQUIRED_PACKAGES = [
    "hanzo_tools.fs",
    "hanzo_tools.shell",
    "hanzo_tools.memory",
    "hanzo_tools.todo",
    "hanzo_tools.reasoning",
    "hanzo_tools.lsp",
    "hanzo_tools.refactor",
    "hanzo_tools.database",
    "hanzo_tools.agent",
    "hanzo_tools.jupyter",
    "hanzo_tools.editor",
    "hanzo_tools.browser",
]

# Optional packages
OPTIONAL_PACKAGES = [
    "hanzo_tools.config",
    "hanzo_tools.mcp_tools",
    "hanzo_tools.llm",
    "hanzo_tools.vector",
]


class TestToolAsync:
    """Test that all tools have async call methods."""

    def test_all_tools_async(self):
        """Verify all tool .call() methods are async."""
        import importlib

        all_packages = REQUIRED_PACKAGES + [
            p for p in OPTIONAL_PACKAGES if _module_installed(p)
        ]

        for pkg_name in all_packages:
            pkg = importlib.import_module(pkg_name)
            tools = getattr(pkg, "TOOLS", [])
            for tool in tools:
                if hasattr(tool, "call"):
                    assert asyncio.iscoroutinefunction(
                        tool.call
                    ), f"{pkg_name}.{tool.name}.call() is not async"


class TestTotalToolCount:
    """Test total tool count across all packages."""

    def test_required_tool_count(self):
        """Verify we have the expected tools in required packages.

        Required packages must have exact counts.
        """
        # Required packages with exact counts
        required_packages = [
            ("hanzo_tools.fs", 7),
            ("hanzo_tools.shell", 11),
            ("hanzo_tools.browser", 1),
            ("hanzo_tools.memory", 9),
            ("hanzo_tools.todo", 1),
            ("hanzo_tools.reasoning", 2),
            ("hanzo_tools.lsp", 1),
            ("hanzo_tools.refactor", 1),
            ("hanzo_tools.database", 8),
            ("hanzo_tools.jupyter", 1),
            ("hanzo_tools.editor", 3),
            ("hanzo_tools.agent", 3),
        ]

        total = 0
        import importlib

        # Check required packages (exact counts)
        for pkg_name, expected_count in required_packages:
            pkg = importlib.import_module(pkg_name)
            tools = getattr(pkg, "TOOLS", [])
            actual = len(tools)
            assert (
                actual == expected_count
            ), f"{pkg_name}: expected {expected_count} tools, got {actual}"
            total += actual

        # Required tools: 48 (7+11+1+9+1+2+1+1+8+1+3+3)
        assert total == 48, f"Expected 48 required tools, got {total}"
