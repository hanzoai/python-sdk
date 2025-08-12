"""Test CLI agent tools."""

import os
from unittest.mock import Mock, patch

import pytest
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.grok_cli_tool import GrokCLITool
from hanzo_mcp.tools.agent.codex_cli_tool import CodexCLITool
from hanzo_mcp.tools.agent.claude_cli_tool import ClaudeCLITool
from hanzo_mcp.tools.agent.gemini_cli_tool import GeminiCLITool


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    return Mock()


@pytest.fixture
def permission_manager():
    """Create a permission manager."""
    pm = PermissionManager()
    pm.add_allowed_path("/test")
    return pm


class TestClaudeCLI:
    """Test Claude CLI tool."""

    def test_initialization(self, tool_helper, permission_manager):
        """Test tool initialization."""
        tool = ClaudeCLITool(permission_manager)
        assert tool.name == "claude_cli"
        assert tool.command_name == "claude"
        assert tool.provider_name == "Claude Code"
        assert "claude-3-5-sonnet" in tool.default_model

    def test_cli_args(self, tool_helper, permission_manager):
        """Test CLI argument generation."""
        tool = ClaudeCLITool(permission_manager)

        # Basic prompt - now includes default model
        args = tool.get_cli_args("Fix the bug")
        assert args == ["--model", tool.default_model, "Fix the bug"]

        # With model
        args = tool.get_cli_args("Fix the bug", model="claude-3-opus")
        assert args == ["--model", "claude-3-opus", "Fix the bug"]

        # With all options
        args = tool.get_cli_args(
            "Fix the bug", model="claude-3-opus", temperature=0.7, max_tokens=2000
        )
        assert args == [
            "--model",
            "claude-3-opus",
            "--temperature",
            "0.7",
            "--max-tokens",
            "2000",
            "Fix the bug",
        ]

    @pytest.mark.asyncio
    async def test_not_installed(self, tool_helper, mock_context, permission_manager):
        """Test error when CLI not installed."""
        tool = ClaudeCLITool(permission_manager)

        with patch("shutil.which", return_value=None):
            result = await tool.call(mock_context, prompts="Test")
        if isinstance(result, dict) and "output" in result:
            result = result["output"]
            tool_helper.assert_in_result("Error:", result)
            tool_helper.assert_in_result("not installed", result)

    @pytest.mark.asyncio
    async def test_no_api_key(self, tool_helper, mock_context, permission_manager):
        """Test error when no API key."""
        tool = ClaudeCLITool(permission_manager)

        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {}, clear=True):
                result = await tool.call(mock_context, prompts="Test")
                if isinstance(result, dict) and "output" in result:
                    result = result["output"]
                tool_helper.assert_in_result("Error:", result)
                tool_helper.assert_in_result("No API key", result)


class TestCodexCLI:
    """Test Codex (OpenAI) CLI tool."""

    def test_initialization(self, tool_helper, permission_manager):
        """Test tool initialization."""
        tool = CodexCLITool(permission_manager)
        assert tool.name == "codex_cli"
        assert tool.command_name == "openai"
        assert tool.provider_name == "OpenAI"
        assert tool.default_model == "gpt-4o"

    def test_cli_args(self, tool_helper, permission_manager):
        """Test CLI argument generation."""
        tool = CodexCLITool(permission_manager)

        # Basic prompt
        args = tool.get_cli_args("Generate code")
        assert args == [
            "api",
            "chat.completions.create",
            "-m",
            "gpt-4o",
            "-g",
            "Generate code",
        ]

        # With custom model
        args = tool.get_cli_args("Generate code", model="gpt-4-turbo")
        assert args == [
            "api",
            "chat.completions.create",
            "-m",
            "gpt-4-turbo",
            "-g",
            "Generate code",
        ]


class TestGeminiCLI:
    """Test Gemini CLI tool."""

    def test_initialization(self, tool_helper, permission_manager):
        """Test tool initialization."""
        tool = GeminiCLITool(permission_manager)
        assert tool.name == "gemini_cli"
        assert tool.command_name == "gemini"
        assert tool.provider_name == "Google Gemini"
        assert tool.default_model == "gemini-1.5-pro"

    def test_cli_args(self, tool_helper, permission_manager):
        """Test CLI argument generation."""
        tool = GeminiCLITool(permission_manager)

        # Basic prompt
        args = tool.get_cli_args("Analyze code")
        assert args == [
            "generate",
            "--model",
            "gemini-1.5-pro",
            "--prompt",
            "Analyze code",
        ]

        # With options
        args = tool.get_cli_args(
            "Analyze code", model="gemini-1.5-flash", temperature=0.5, max_tokens=1000
        )
        assert args == [
            "generate",
            "--model",
            "gemini-1.5-flash",
            "--temperature",
            "0.5",
            "--max-output-tokens",
            "1000",
            "--prompt",
            "Analyze code",
        ]


class TestGrokCLI:
    """Test Grok CLI tool."""

    def test_initialization(self, tool_helper, permission_manager):
        """Test tool initialization."""
        tool = GrokCLITool(permission_manager)
        assert tool.name == "grok_cli"
        assert tool.command_name == "grok"
        assert tool.provider_name == "xAI Grok"
        assert tool.default_model == "grok-2"

    def test_cli_args(self, tool_helper, permission_manager):
        """Test CLI argument generation."""
        tool = GrokCLITool(permission_manager)

        # Basic prompt
        args = tool.get_cli_args("Explain quantum computing")
        assert args == ["chat", "--model", "grok-2", "Explain quantum computing"]

        # With system prompt
        args = tool.get_cli_args(
            "Explain quantum computing",
            system_prompt="You are a helpful coding assistant",
        )
        assert args == [
            "chat",
            "--model",
            "grok-2",
            "--system",
            "You are a helpful coding assistant",
            "Explain quantum computing",
        ]


class TestCLIAgentIntegration:
    """Test CLI agents working together."""

    @pytest.mark.asyncio
    async def test_swarm_with_cli_agents(
        self, tool_helper, mock_context, permission_manager
    ):
        """Test using CLI agents in a swarm."""
        # This would test that CLI agents can be used as the underlying
        # agents in a swarm configuration

        # Mock the CLI tools being installed
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"

            # Mock environment variables
            with patch.dict(
                os.environ,
                {
                    "ANTHROPIC_API_KEY": "test-key",
                    "OPENAI_API_KEY": "test-key",
                    "GOOGLE_API_KEY": "test-key",
                    "XAI_API_KEY": "test-key",
                },
            ):
                # Create tools
                claude = ClaudeCLITool(permission_manager)
                codex = CodexCLITool(permission_manager)
                gemini = GeminiCLITool(permission_manager)
                grok = GrokCLITool(permission_manager)

                # Verify all are ready
                assert claude.is_installed()
                assert claude.has_api_key()
                assert codex.is_installed()
                assert codex.has_api_key()
                assert gemini.is_installed()
                assert gemini.has_api_key()
                assert grok.is_installed()
                assert grok.has_api_key()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
