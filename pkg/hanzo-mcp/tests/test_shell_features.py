"""Test shell features including auto-backgrounding and shell detection."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hanzo_mcp.tools.shell.bash_tool import BashTool
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.shell.base_process import ProcessManager
from hanzo_mcp.tools.shell.process_tool import ProcessTool


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
def process_tool():
    """Create a process tool instance."""
    return ProcessTool()


class TestShellDetection:
    """Test shell detection functionality."""

    def test_default_shell(self, tool_helper, bash_tool):
        """Test default shell is bash."""
        with patch.dict(os.environ, {}, clear=True):
            interpreter = bash_tool.get_interpreter()
            assert interpreter == "bash"

    def test_zsh_detection_with_zshrc(self, tool_helper, bash_tool, tmp_path):
        """Test zsh is detected when .zshrc exists."""
        # Create fake .zshrc
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        zshrc = fake_home / ".zshrc"
        zshrc.touch()

        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("pathlib.Path.home", return_value=fake_home):
                interpreter = bash_tool.get_interpreter()
                assert interpreter == "/bin/zsh"

    def test_zsh_fallback_to_bash(self, tool_helper, bash_tool, tmp_path):
        """Test fallback to bash when zsh set but no .zshrc."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("pathlib.Path.home", return_value=fake_home):
                interpreter = bash_tool.get_interpreter()
                assert interpreter == "bash"

    def test_fish_detection_with_config(self, tool_helper, bash_tool, tmp_path):
        """Test fish is detected when config exists."""
        # Create fake fish config
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        fish_config_dir = fake_home / ".config" / "fish"
        fish_config_dir.mkdir(parents=True)
        fish_config = fish_config_dir / "config.fish"
        fish_config.touch()

        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            with patch("pathlib.Path.home", return_value=fake_home):
                interpreter = bash_tool.get_interpreter()
                assert interpreter == "/usr/bin/fish"

    def test_tool_name_reflects_shell(self, tool_helper, bash_tool):
        """Test tool name reflects the actual shell being used."""
        with patch.object(bash_tool, "get_interpreter", return_value="/bin/zsh"):
            assert bash_tool.get_tool_name() == "zsh"

        with patch.object(bash_tool, "get_interpreter", return_value="/usr/bin/fish"):
            assert bash_tool.get_tool_name() == "fish"

        with patch.object(bash_tool, "get_interpreter", return_value="bash"):
            assert bash_tool.get_tool_name() == "bash"


class TestAutoBackgrounding:
    """Test auto-backgrounding functionality."""

    @pytest.mark.asyncio
    async def test_quick_command_completes(self, tool_helper, bash_tool, mock_ctx):
        """Test that quick commands complete normally."""
        result = await bash_tool.call(mock_ctx, command="echo 'Hello World'")
        tool_helper.assert_in_result("Hello World", result)
        assert "backgrounded" not in result.lower()

    @pytest.mark.asyncio
    @patch("hanzo_mcp.tools.shell.auto_background.AutoBackgroundExecutor.execute_with_auto_background")
    async def test_long_command_backgrounds(self, tool_helper, mock_execute, bash_tool, mock_ctx):
        """Test that long-running commands are backgrounded."""
        # Simulate backgrounding
        mock_execute.return_value = (
            "Command automatically backgrounded after 2 minutes.\nProcess ID: test_123",
            True,
            "test_123",
        )

        result = await bash_tool.call(mock_ctx, command="sleep 300")
        tool_helper.assert_in_result("backgrounded", result)
        tool_helper.assert_in_result("test_123", result)

    @pytest.mark.asyncio
    async def test_command_with_timeout_ignored(self, tool_helper, bash_tool, mock_ctx):
        """Test that timeout parameter is ignored (auto-backgrounding takes precedence)."""
        # Should not fail even with short timeout
        result = await bash_tool.call(
            mock_ctx,
            command="echo 'Quick test'",
            timeout=1,  # This should be ignored
        )
        tool_helper.assert_in_result("Quick test", result)


class TestProcessManagement:
    """Test process management functionality."""

    @pytest.fixture
    def process_manager(self):
        """Get process manager instance."""
        return ProcessManager()

    def test_process_tracking(self, tool_helper, process_manager):
        """Test process tracking functionality."""
        # Create mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running

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
    async def test_process_list_command(self, tool_helper, process_tool, mock_ctx):
        """Test process list command."""
        # Add a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None

        process_tool.process_manager.add_process("test_123", mock_process, "/tmp/test.log")

        result = await process_tool.call(mock_ctx, action="list")
        tool_helper.assert_in_result("test_123", result)
        tool_helper.assert_in_result("12345", result)
        tool_helper.assert_in_result("running", result)

    @pytest.mark.asyncio
    async def test_process_kill_command(self, tool_helper, process_tool, mock_ctx):
        """Test process kill command."""
        # Add a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.send_signal = MagicMock()

        process_tool.process_manager.add_process("test_123", mock_process, "/tmp/test.log")

        result = await process_tool.call(mock_ctx, action="kill", id="test_123", signal_type="TERM")

        tool_helper.assert_in_result("Sent TERM signal", result)
        tool_helper.assert_in_result("12345", result)
        mock_process.send_signal.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_logs_command(self, tool_helper, process_tool, mock_ctx, tmp_path):
        """Test process logs command."""
        # Create log file
        log_file = tmp_path / "test.log"
        log_file.write_text("Line 1\nLine 2\nLine 3\n")

        # Add process with log file
        mock_process = MagicMock()
        process_tool.process_manager.add_process("test_123", mock_process, str(log_file))

        result = await process_tool.call(mock_ctx, action="logs", id="test_123", lines=2)

        tool_helper.assert_in_result("Line 2", result)
        tool_helper.assert_in_result("Line 3", result)
        assert "Line 1" not in result  # Only last 2 lines


class TestIntegration:
    """Integration tests for shell features."""

    @pytest.mark.asyncio
    async def test_bash_and_process_integration(self, bash_tool, process_tool, mock_ctx):
        """Test bash and process tools work together."""
        # Execute a command that would be backgrounded
        with patch.object(
            bash_tool.auto_background_executor,
            "execute_with_auto_background",
            return_value=(
                "Command backgrounded. Process ID: bash_abc123",
                True,
                "bash_abc123",
            ),
        ):
            bash_result = await bash_tool.call(mock_ctx, command="python long_running_script.py")
            assert "backgrounded" in bash_result
            assert "bash_abc123" in bash_result

        # Now check process list (would need real process tracking)
        # This is more of a structural test
        process_result = await process_tool.call(mock_ctx, action="list")
        assert isinstance(process_result, str)

    @pytest.mark.asyncio
    async def test_shell_specific_commands(self, tool_helper, bash_tool, mock_ctx):
        """Test shell-specific command execution."""
        # Test with different shells
        shells = [
            ("bash", "echo $BASH_VERSION"),
            ("zsh", "echo $ZSH_VERSION"),
            ("fish", "echo $FISH_VERSION"),
        ]

        for shell_name, _command in shells:
            with patch.object(bash_tool, "get_interpreter", return_value=f"/bin/{shell_name}"):
                # This would execute the command with the specific shell
                tool_name = bash_tool.get_tool_name()
                assert tool_name == shell_name


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow with real commands."""
    # This would be an integration test that:
    # 1. Runs a long command
    # 2. Verifies it gets backgrounded
    # 3. Checks process list
    # 4. Views logs
    # 5. Kills the process

    # For now, just ensure the structure is correct
    pm = PermissionManager()
    pm.add_allowed_path("/tmp")

    bash = BashTool()
    bash.permission_manager = pm

    process = ProcessTool()

    assert bash.name == "bash"
    assert process.name == "process"
    assert bash.get_tool_name() in ["bash", "zsh", "fish", "shell"]
