"""Tests for CLI."""

from unittest.mock import patch

from click.testing import CliRunner

from hanzo_memory.cli import cli, main


class TestCLI:
    """Test CLI commands."""

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Hanzo Memory Service" in result.output

    @patch("hanzo_memory.cli.run_server")
    def test_server_command_default(self, mock_run):
        """Test server command with default options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["server"])
        assert result.exit_code == 0
        assert "Starting Hanzo Memory Service on 0.0.0.0:4000" in result.output
        mock_run.assert_called_once()

    @patch("hanzo_memory.cli.run_server")
    def test_server_command_custom(self, mock_run):
        """Test server command with custom host and port."""
        runner = CliRunner()
        result = runner.invoke(cli, ["server", "--host", "127.0.0.1", "--port", "8080"])
        assert result.exit_code == 0
        assert "Starting Hanzo Memory Service on 127.0.0.1:8080" in result.output
        mock_run.assert_called_once()

    @patch("hanzo_memory.cli.settings")
    def test_info_command(self, mock_settings):
        """Test info command."""
        # Mock settings
        mock_settings.infinity_db_path = "/test/path"
        mock_settings.embedding_model = "test-model"
        mock_settings.llm_model = "gpt-test"
        mock_settings.disable_auth = False

        runner = CliRunner()
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Hanzo Memory Service" in result.output
        assert "Version: 0.1.0" in result.output
        assert "/test/path" in result.output
        assert "test-model" in result.output
        assert "gpt-test" in result.output
        assert "False" in result.output

    @patch("hanzo_memory.cli.cli")
    def test_main_entry_point(self, mock_cli):
        """Test main entry point."""
        main()
        mock_cli.assert_called_once()
