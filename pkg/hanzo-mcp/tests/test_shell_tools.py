"""Test suite for shell tools including zsh and smart shell selection."""

import os
import sys
import shutil
import asyncio
import platform
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hanzo_mcp.tools.shell.zsh_tool import ZshTool, ShellTool
from hanzo_mcp.tools.shell.bash_tool import BashTool


class MockContext:
    """Mock MCP context for testing."""

    pass


class TestBashTool:
    """Test bash tool functionality."""

    def test_bash_tool_properties(self):
        """Test bash tool basic properties."""
        tool = BashTool()

        assert tool.name == "bash"
        assert tool.get_tool_name() == "bash"
        assert "bash" in tool.description.lower()

        # On Unix-like systems, should always return bash
        if platform.system() != "Windows":
            assert tool.get_interpreter() == "bash"

    @pytest.mark.asyncio
    async def test_bash_execution(self):
        """Test bash command execution."""
        tool = BashTool()
        ctx = MockContext()

        # Mock execute_sync to avoid actual command execution
        with patch.object(tool, "execute_sync", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "test output"

            result = await tool.run(ctx, "echo test")

            assert result == "test output"
            mock_exec.assert_called_once()

    def test_bash_flags(self):
        """Test bash interpreter flags."""
        tool = BashTool()

        if platform.system() == "Windows":
            # On Windows, might be /c or -c depending on shell
            flags = tool.get_script_flags()
            assert flags in [["/c"], ["-c"]]
        else:
            assert tool.get_script_flags() == ["-c"]


class TestZshTool:
    """Test zsh tool functionality."""

    def test_zsh_tool_properties(self):
        """Test zsh tool basic properties."""
        tool = ZshTool()

        assert tool.name == "zsh"
        assert tool.get_tool_name() == "zsh"
        assert "zsh" in tool.description.lower()
        assert "enhanced features" in tool.description.lower()

    def test_zsh_interpreter_detection(self):
        """Test zsh interpreter detection."""
        tool = ZshTool()

        if platform.system() != "Windows":
            # Check if zsh is available
            if shutil.which("zsh"):
                interpreter = tool.get_interpreter()
                assert "zsh" in interpreter or interpreter == "bash"
            else:
                # Should fall back to bash if zsh not found
                assert tool.get_interpreter() == "bash"

    @pytest.mark.asyncio
    async def test_zsh_execution(self):
        """Test zsh command execution."""
        tool = ZshTool()
        ctx = MockContext()

        # Mock execute_sync
        with patch.object(tool, "execute_sync", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "zsh output"

            result = await tool.run(ctx, "echo $ZSH_VERSION")

            assert result == "zsh output"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_zsh_not_installed(self):
        """Test error when zsh is not installed."""
        tool = ZshTool()
        ctx = MockContext()

        # Mock shutil.which to return None (zsh not found)
        with patch("shutil.which", return_value=None):
            if platform.system() != "Windows":
                result = await tool.run(ctx, "echo test")
                assert "not installed" in result.lower()


class TestShellTool:
    """Test smart shell tool functionality."""

    def test_shell_tool_properties(self):
        """Test shell tool basic properties."""
        tool = ShellTool()

        assert tool.name == "shell"
        assert tool.get_tool_name() == "shell"
        assert "best available shell" in tool.description.lower()

    def test_shell_detection(self):
        """Test smart shell detection."""
        tool = ShellTool()

        # Should have detected a shell
        assert tool._best_shell is not None
        assert tool._best_shell in ["zsh", "bash"] or Path(tool._best_shell).exists()

    def test_shell_preference_order(self):
        """Test shell preference order."""
        # Test with fresh instance each time

        # Mock different scenarios
        with patch("shutil.which") as mock_which:
            with patch.object(Path, "exists") as mock_exists:
                # Scenario 1: zsh available with .zshrc
                mock_which.return_value = "/usr/bin/zsh"
                mock_exists.return_value = True
                tool = ShellTool()
                assert "zsh" in tool._best_shell

                # Scenario 2: zsh not available, use bash
                mock_which.return_value = None
                mock_exists.return_value = False
                tool = ShellTool()
                assert tool._best_shell == "bash"

    @pytest.mark.asyncio
    async def test_shell_execution_with_info(self):
        """Test shell execution with shell info."""
        tool = ShellTool()
        ctx = MockContext()

        # Mock execute_sync
        with patch.object(tool, "execute_sync", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = ""  # Empty output

            result = await tool.run(ctx, "true")  # Command with no output

            # Should mention which shell was used
            assert "completed successfully" in result.lower()
            if "zsh" in tool._best_shell:
                assert "zsh" in result.lower()
            else:
                assert "bash" in result.lower() or "shell" in result.lower()

    def test_shell_description_dynamic(self):
        """Test that shell description shows current shell."""
        tool = ShellTool()

        description = tool.description
        shell_name = os.path.basename(tool._best_shell)

        # Description should mention the current shell
        assert f"currently: {shell_name}" in description.lower()


class TestShellIntegration:
    """Integration tests for shell tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_shell_execution(self):
        """Test real shell execution (integration test)."""
        # This test actually runs commands - skip in CI
        if os.environ.get("CI"):
            pytest.skip("Skipping real shell execution in CI")

        ctx = MockContext()

        # Test each tool
        bash_tool = BashTool()
        result = await bash_tool.run(ctx, "echo 'bash works'")
        assert "bash works" in result

        # Test zsh if available
        if shutil.which("zsh"):
            zsh_tool = ZshTool()
            result = await zsh_tool.run(ctx, "echo 'zsh works'")
            assert "zsh works" in result

        # Test smart shell
        shell_tool = ShellTool()
        result = await shell_tool.run(ctx, "echo 'shell works'")
        assert "shell works" in result or "completed successfully" in result

    @pytest.mark.asyncio
    async def test_shell_tools_registration(self):
        """Test that shell tools can be registered."""
        from hanzo_mcp.tools.shell import get_shell_tools
        from hanzo_mcp.tools.common.permissions import PermissionManager

        pm = PermissionManager()
        tools = get_shell_tools(pm)

        # Should have our shell tools
        tool_names = [tool.name for tool in tools]
        assert "bash" in tool_names
        assert "zsh" in tool_names
        assert "shell" in tool_names

        # Shell should be first (preferred)
        assert tools[0].name == "shell"

    def test_shell_tool_ordering(self):
        """Test that shell tools are returned in correct order."""
        from hanzo_mcp.tools.shell import get_shell_tools
        from hanzo_mcp.tools.common.permissions import PermissionManager

        pm = PermissionManager()
        tools = get_shell_tools(pm)

        # Find shell tools
        shell_tools = [t for t in tools if t.name in ["shell", "zsh", "bash"]]

        # Order should be: shell (smart), zsh, bash
        assert shell_tools[0].name == "shell"
        assert shell_tools[1].name == "zsh"
        assert shell_tools[2].name == "bash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
