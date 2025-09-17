"""Consolidated CLI agent tests using parametrization."""

from unittest.mock import Mock, AsyncMock, patch

import pytest
from hanzo_mcp.tools.cli_agents import (
    GrokCLI,
    CodexCLI,
    ClaudeCLI,
    GeminiCLI,
)


class TestCLIAgentsConsolidated:
    """Consolidated tests for all CLI agents using parametrization."""

    @pytest.mark.parametrize(
        "cli_class,model_name,expected_provider",
        [
            (ClaudeCLI, "claude-3-opus", "anthropic"),
            (CodexCLI, "gpt-4", "openai"),
            (GeminiCLI, "gemini-pro", "google"),
            (GrokCLI, "grok-beta", "xai"),
        ],
    )
    def test_cli_initialization(self, cli_class, model_name, expected_provider):
        """Test CLI agent initialization for different models."""
        with patch(f"hanzo_mcp.tools.cli_agents.{expected_provider}_client"):
            cli = cli_class()

            # Verify basic initialization
            assert cli is not None
            assert hasattr(cli, "run")

            # Verify model configuration
            if hasattr(cli, "model"):
                assert model_name in str(cli.model).lower() or expected_provider in str(cli.model).lower()

    @pytest.mark.parametrize(
        "cli_class,command,expected_output",
        [
            (ClaudeCLI, "help", "Available commands"),
            (CodexCLI, "status", "System status"),
            (GeminiCLI, "version", "Version"),
            (GrokCLI, "info", "Information"),
        ],
    )
    async def test_cli_commands(self, cli_class, command, expected_output):
        """Test basic CLI commands for all agents."""
        with patch(f"hanzo_mcp.tools.cli_agents.process_command") as mock_process:
            mock_process.return_value = expected_output

            cli = cli_class()
            result = await cli.run(command)

            assert expected_output in str(result)
            mock_process.assert_called_once_with(command)

    @pytest.mark.parametrize(
        "cli_class,error_type,error_message",
        [
            (ClaudeCLI, ValueError, "Invalid command"),
            (CodexCLI, ConnectionError, "API connection failed"),
            (GeminiCLI, PermissionError, "Insufficient permissions"),
            (GrokCLI, RuntimeError, "Runtime error occurred"),
        ],
    )
    async def test_cli_error_handling(self, cli_class, error_type, error_message):
        """Test error handling for CLI agents."""
        with patch(f"hanzo_mcp.tools.cli_agents.process_command") as mock_process:
            mock_process.side_effect = error_type(error_message)

            cli = cli_class()

            with pytest.raises(error_type, match=error_message):
                await cli.run("test_command")

    @pytest.mark.parametrize("cli_class", [ClaudeCLI, CodexCLI, GeminiCLI, GrokCLI])
    async def test_cli_streaming(self, cli_class):
        """Test streaming capabilities for all CLI agents."""
        with patch(f"hanzo_mcp.tools.cli_agents.stream_response") as mock_stream:
            mock_stream.return_value = AsyncMock()
            mock_stream.return_value.__aiter__.return_value = [
                "chunk1",
                "chunk2",
                "chunk3",
            ]

            cli = cli_class()

            if hasattr(cli, "stream"):
                chunks = []
                async for chunk in cli.stream("test prompt"):
                    chunks.append(chunk)

                assert len(chunks) == 3
                assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.parametrize(
        "cli_class,config_key,config_value",
        [
            (ClaudeCLI, "max_tokens", 4096),
            (CodexCLI, "temperature", 0.7),
            (GeminiCLI, "top_p", 0.9),
            (GrokCLI, "presence_penalty", 0.1),
        ],
    )
    def test_cli_configuration(self, cli_class, config_key, config_value):
        """Test configuration options for CLI agents."""
        config = {config_key: config_value}

        with patch(f"hanzo_mcp.tools.cli_agents.load_config") as mock_config:
            mock_config.return_value = config

            cli = cli_class(**config)

            if hasattr(cli, config_key):
                assert getattr(cli, config_key) == config_value
