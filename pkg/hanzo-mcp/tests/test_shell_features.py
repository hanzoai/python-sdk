"""Test shell features including auto-backgrounding and shell detection."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hanzo_tools.shell.ps_tool import PsTool
from hanzo_tools.shell.shell_tools import ZshTool, BashTool, DashTool, FishTool, ShellTool
from hanzo_tools.shell.base_process import ProcessManager
from hanzo_tools.shell.shell_detect import (
    SUPPORTED_SHELLS,
    detect_shells,
    get_active_shell,
    clear_shell_cache,
    get_shell_tool_class,
    get_cached_active_shell,
)
from hanzo_mcp.tools.common.permissions import PermissionManager


@pytest.fixture
def mock_ctx():
    """Create a mock MCP context."""
    ctx = MagicMock()
    return ctx


@pytest.fixture
def permission_manager():
    """Create a permission manager."""
    pm = PermissionManager()
    pm.add_allowed_path("/tmp")
    pm.add_allowed_path(str(Path.home()))
    return pm


@pytest.fixture
def bash_tool(permission_manager):
    """Create a bash tool instance."""
    tool = BashTool()
    tool.permission_manager = permission_manager
    return tool


@pytest.fixture
def zsh_tool(permission_manager):
    """Create a zsh tool instance."""
    tool = ZshTool()
    tool.permission_manager = permission_manager
    return tool


@pytest.fixture
def shell_tool(permission_manager):
    """Create a shell tool instance (smart shell detection)."""
    tool = ShellTool()
    tool.permission_manager = permission_manager
    return tool


@pytest.fixture
def ps_tool_instance():
    """Create a ps tool instance."""
    return PsTool()


class TestShellDetection:
    """Test shell detection functionality."""

    def test_detect_shells_returns_shell_info(self):
        """Test detect_shells returns proper ShellInfo."""
        info = detect_shells()
        assert hasattr(info, "login_shell")
        assert hasattr(info, "invoking_shell")
        assert hasattr(info, "env_shell")
        assert hasattr(info, "evidence")

    def test_get_active_shell_returns_tuple(self):
        """Test get_active_shell returns (name, path) tuple."""
        name, path = get_active_shell()
        assert isinstance(name, str)
        assert isinstance(path, str)
        assert name in SUPPORTED_SHELLS or name == "sh"

    def test_supported_shells_contains_expected(self):
        """Test SUPPORTED_SHELLS contains expected shells."""
        assert "zsh" in SUPPORTED_SHELLS
        assert "bash" in SUPPORTED_SHELLS
        assert "fish" in SUPPORTED_SHELLS
        assert "dash" in SUPPORTED_SHELLS

    def test_get_shell_tool_class_returns_correct_class(self):
        """Test get_shell_tool_class returns the right tool class."""
        assert get_shell_tool_class("zsh") == ZshTool
        assert get_shell_tool_class("bash") == BashTool
        assert get_shell_tool_class("fish") == FishTool
        assert get_shell_tool_class("dash") == DashTool
        assert get_shell_tool_class("unknown") is None

    def test_shell_env_override(self):
        """Test HANZO_MCP_SHELL environment variable override."""
        clear_shell_cache()
        with patch.dict(os.environ, {"HANZO_MCP_SHELL": "bash"}, clear=False):
            name, path = get_active_shell()
            assert name == "bash"
        clear_shell_cache()

    def test_force_shell_path_override(self):
        """Test HANZO_MCP_FORCE_SHELL environment variable override."""
        clear_shell_cache()
        with patch.dict(os.environ, {"HANZO_MCP_FORCE_SHELL": "/bin/bash"}, clear=False):
            name, path = get_active_shell()
            assert name == "bash"
            assert path == "/bin/bash"
        clear_shell_cache()

    def test_bash_tool_name(self, bash_tool):
        """Test BashTool has correct name."""
        assert bash_tool.name == "bash"

    def test_zsh_tool_name(self, zsh_tool):
        """Test ZshTool has correct name."""
        assert zsh_tool.name == "zsh"

    def test_shell_tool_name(self, shell_tool):
        """Test ShellTool has correct name."""
        assert shell_tool.name == "shell"


class TestAutoBackgrounding:
    """Test auto-backgrounding functionality."""

    @pytest.mark.asyncio
    async def test_quick_command_completes(self, bash_tool, mock_ctx):
        """Test that quick commands complete normally."""
        result = await bash_tool.call(mock_ctx, command="echo 'Hello World'")
        assert "Hello World" in result
        assert "backgrounded" not in result.lower()

    @pytest.mark.asyncio
    async def test_command_output(self, zsh_tool, mock_ctx):
        """Test command output is captured."""
        result = await zsh_tool.call(mock_ctx, command="echo 'test output'")
        assert "test output" in result


class TestProcessManagement:
    """Test process management functionality."""

    @pytest.fixture
    def process_manager(self):
        """Get process manager instance."""
        return ProcessManager()

    def test_process_tracking(self, process_manager):
        """Test process tracking functionality."""
        # Create mock process (asyncio.subprocess.Process uses returncode, not poll())
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.returncode = None  # Still running (asyncio.subprocess.Process style)

        # Add process
        process_manager.add_process("test_123", mock_process, "/tmp/test.log")

        # Check it's tracked
        assert process_manager.get_process("test_123") == mock_process

        # List processes
        processes = process_manager.list_processes()
        assert "test_123" in processes
        assert processes["test_123"]["pid"] == 12345
        assert processes["test_123"]["running"] is True

    @pytest.mark.asyncio
    async def test_ps_list_command(self, ps_tool_instance, mock_ctx):
        """Test ps list command."""
        result = await ps_tool_instance.call(mock_ctx)
        assert isinstance(result, str)


class TestToolsListWithShellDetection:
    """Test that TOOLS list respects shell detection."""

    def test_default_tools_list_has_one_shell(self):
        """Test default TOOLS list only includes detected shell."""
        clear_shell_cache()
        # Re-import to get fresh TOOLS list
        from hanzo_tools.shell import TOOLS, get_cached_active_shell

        shell_name, _ = get_cached_active_shell()

        # Count shell tools
        shell_tools = [t for t in TOOLS if hasattr(t, "name") and t.name in SUPPORTED_SHELLS]

        # Should have exactly one shell tool (the detected one)
        assert len(shell_tools) == 1
        assert shell_tools[0].name == shell_name

    def test_all_shells_mode(self):
        """Test HANZO_MCP_ALL_SHELLS=1 exposes all shells."""
        clear_shell_cache()
        with patch.dict(os.environ, {"HANZO_MCP_ALL_SHELLS": "1"}, clear=False):
            # Re-import to get fresh TOOLS list
            import importlib

            import hanzo_tools.shell

            importlib.reload(hanzo_tools.shell)
            from hanzo_tools.shell import TOOLS

            # Count shell tools
            shell_tools = [t for t in TOOLS if hasattr(t, "name") and t.name in SUPPORTED_SHELLS]

            # Should have all 4 shell tools
            assert len(shell_tools) == 4
            shell_names = {t.name for t in shell_tools}
            assert shell_names == SUPPORTED_SHELLS

        # Cleanup
        clear_shell_cache()
        if "HANZO_MCP_ALL_SHELLS" in os.environ:
            del os.environ["HANZO_MCP_ALL_SHELLS"]
        import importlib

        import hanzo_tools.shell

        importlib.reload(hanzo_tools.shell)


class TestIntegration:
    """Integration tests for shell features."""

    @pytest.mark.asyncio
    async def test_bash_command_execution(self, bash_tool, mock_ctx):
        """Test bash command execution."""
        result = await bash_tool.call(mock_ctx, command="echo 'integration test'")
        assert "integration test" in result

    @pytest.mark.asyncio
    async def test_zsh_command_execution(self, zsh_tool, mock_ctx):
        """Test zsh command execution."""
        result = await zsh_tool.call(mock_ctx, command="echo 'zsh test'")
        assert "zsh test" in result

    def test_tool_names_are_correct(self, bash_tool, zsh_tool, shell_tool):
        """Test all shell tools have correct names."""
        assert bash_tool.name == "bash"
        assert zsh_tool.name == "zsh"
        assert shell_tool.name == "shell"


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow with real commands."""
    pm = PermissionManager()
    pm.add_allowed_path("/tmp")

    bash = BashTool()
    bash.permission_manager = pm

    ps = PsTool()

    assert bash.name == "bash"
    assert ps.name == "ps"
