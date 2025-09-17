"""Test suite for CLI tools in batch operations."""

import os
import time
import asyncio
from typing import Any, Dict
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest
from hanzo_mcp.tools.agent.cli_tools import (
    GrokCLITool,
    AiderCLITool,
    ClineCLITool,
    CodexCLITool,
    ClaudeCLITool,
    GeminiCLITool,
    HanzoDevCLITool,
    OpenHandsCLITool,
    ClaudeCodeCLITool,
    OpenHandsShortCLITool,
)
from hanzo_mcp.tools.common.batch_tool import BatchTool


class TestCLITools:
    """Test CLI tool implementations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        context = MagicMock()
        context.session = MagicMock()
        context.session.send_log_message = AsyncMock()
        context.session.send_progress = AsyncMock()
        return context

    @pytest.fixture
    def mock_permission_manager(self):
        """Create a mock permission manager."""
        pm = MagicMock()
        pm.check_permission = Mock(return_value=True)
        return pm

    @pytest.mark.asyncio
    async def test_claude_cli_tool(self, mock_context, mock_permission_manager):
        """Test Claude CLI tool execution."""
        tool = ClaudeCLITool(mock_permission_manager)

        # Test name and description
        assert tool.name == "claude"
        assert "Claude CLI" in tool.description

        # Mock subprocess execution
        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Claude response"

            result = await tool.call(mock_context, prompt="Test prompt", model="claude-3-opus-20240229", timeout=300)

            assert result == "Claude response"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_claude_code_alias(self, mock_context, mock_permission_manager):
        """Test Claude Code (cc) alias tool."""
        tool = ClaudeCodeCLITool(mock_permission_manager)

        # Test alias name
        assert tool.name == "cc"
        assert "Claude Code" in tool.description

    @pytest.mark.asyncio
    async def test_codex_cli_tool(self, mock_context, mock_permission_manager):
        """Test Codex/GPT-4 CLI tool execution."""
        tool = CodexCLITool(mock_permission_manager)

        assert tool.name == "codex"
        assert "OpenAI" in tool.description or "GPT" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "GPT-4 response"

            result = await tool.call(mock_context, prompt="Generate code", model="gpt-4-turbo")

            assert result == "GPT-4 response"

    @pytest.mark.asyncio
    async def test_gemini_cli_tool(self, mock_context, mock_permission_manager):
        """Test Gemini CLI tool execution."""
        tool = GeminiCLITool(mock_permission_manager)

        assert tool.name == "gemini"
        assert "Gemini" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Gemini response"

            result = await tool.call(mock_context, prompt="Analyze image", model="gemini-1.5-pro")

            assert result == "Gemini response"

    @pytest.mark.asyncio
    async def test_grok_cli_tool(self, mock_context, mock_permission_manager):
        """Test Grok CLI tool execution."""
        tool = GrokCLITool(mock_permission_manager)

        assert tool.name == "grok"
        assert "Grok" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Grok response"

            result = await tool.call(mock_context, prompt="Real-time analysis", model="grok-2")

            assert result == "Grok response"

    @pytest.mark.asyncio
    async def test_openhands_cli_tool(self, mock_context, mock_permission_manager):
        """Test OpenHands CLI tool execution."""
        tool = OpenHandsCLITool(mock_permission_manager)

        assert tool.name == "openhands"
        assert "OpenHands" in tool.description or "OpenDevin" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "OpenHands execution complete"

            result = await tool.call(mock_context, prompt="Build feature", working_dir="/project")

            assert result == "OpenHands execution complete"

    @pytest.mark.asyncio
    async def test_openhands_alias(self, mock_context, mock_permission_manager):
        """Test OpenHands (oh) alias tool."""
        tool = OpenHandsShortCLITool(mock_permission_manager)

        assert tool.name == "oh"
        assert "OpenHands" in tool.description

    @pytest.mark.asyncio
    async def test_hanzo_dev_cli_tool(self, mock_context, mock_permission_manager):
        """Test Hanzo Dev CLI tool execution."""
        tool = OpenHandsCLITool(mock_permission_manager)

        assert tool.name == "hanzo_dev"
        assert "Hanzo Dev" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Hanzo Dev completed task"

            result = await tool.call(mock_context, prompt="Implement feature", model="claude-3-5-sonnet-20241022")

            assert result == "Hanzo Dev completed task"

    @pytest.mark.asyncio
    async def test_cline_cli_tool(self, mock_context, mock_permission_manager):
        """Test Cline CLI tool execution."""
        tool = ClineCLITool(mock_permission_manager)

        assert tool.name == "cline"
        assert "Cline" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Cline autonomous coding complete"

            result = await tool.call(mock_context, prompt="Fix bugs", working_dir="/src")

            assert result == "Cline autonomous coding complete"

    @pytest.mark.asyncio
    async def test_aider_cli_tool(self, mock_context, mock_permission_manager):
        """Test Aider CLI tool execution."""
        tool = AiderCLITool(mock_permission_manager)

        assert tool.name == "aider"
        assert "Aider" in tool.description

        with patch.object(tool, "execute_cli", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Aider pair programming complete"

            result = await tool.call(mock_context, prompt="Refactor module", model="gpt-4-turbo")

            assert result == "Aider pair programming complete"

    @pytest.mark.asyncio
    async def test_cli_tool_auth_env(self, mock_permission_manager):
        """Test that CLI tools properly set authentication environment."""
        # Test Claude with Anthropic key
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-anthropic-key"}):
            tool = ClaudeCLITool(mock_permission_manager)
            env = tool.get_auth_env()
            assert env["ANTHROPIC_API_KEY"] == "test-anthropic-key"

        # Test Codex with OpenAI key
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            tool = CodexCLITool(mock_permission_manager)
            env = tool.get_auth_env()
            assert env["OPENAI_API_KEY"] == "test-openai-key"

        # Test unified Hanzo auth
        with patch.dict("os.environ", {"HANZO_API_KEY": "test-hanzo-key"}):
            tool = OpenHandsCLITool(mock_permission_manager)
            env = tool.get_auth_env()
            assert env["HANZO_API_KEY"] == "test-hanzo-key"

    @pytest.mark.asyncio
    async def test_cli_tool_timeout(self, mock_context, mock_permission_manager):
        """Test CLI tool timeout handling."""
        tool = ClaudeCLITool(mock_permission_manager)

        # Mock a timeout
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
            mock_subprocess.return_value = mock_process

            result = await tool.call(mock_context, prompt="Long task", timeout=1)

            assert "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_cli_tool_error_handling(self, mock_context, mock_permission_manager):
        """Test CLI tool error handling."""
        tool = CodexCLITool(mock_permission_manager)

        # Mock a subprocess error
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error: API key not found"))
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            result = await tool.call(mock_context, prompt="Generate code")

            assert "Error" in result
            assert "API key" in result


class TestBatchWithCLITools:
    """Test batch tool with CLI tools."""

    @pytest.fixture
    def mock_permission_manager(self):
        """Create a mock permission manager."""
        pm = MagicMock()
        pm.check_permission = Mock(return_value=True)
        return pm

    @pytest.fixture
    def mock_tools(self, mock_permission_manager):
        """Create mock CLI tools for batch testing."""
        tools = {
            "claude": ClaudeCLITool(mock_permission_manager),
            "cc": ClaudeCodeCLITool(mock_permission_manager),
            "codex": CodexCLITool(mock_permission_manager),
            "gemini": GeminiCLITool(mock_permission_manager),
            "grok": GrokCLITool(mock_permission_manager),
            "openhands": OpenHandsCLITool(mock_permission_manager),
            "oh": OpenHandsShortCLITool(mock_permission_manager),
            "cline": ClineCLITool(mock_permission_manager),
            "aider": AiderCLITool(mock_permission_manager),
        }

        # Mock execute_cli for all tools
        for tool in tools.values():
            tool.execute_cli = AsyncMock(return_value=f"{tool.name} response")

        return tools

    @pytest.fixture
    def batch_tool(self, mock_tools):
        """Create batch tool with CLI tools."""
        return BatchTool(mock_tools)

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        context = MagicMock()
        context.session = MagicMock()
        context.session.send_log_message = AsyncMock()
        context.session.send_progress = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_batch_with_multiple_cli_tools(self, batch_tool, mock_context):
        """Test batch execution with multiple CLI tools."""
        invocations = [
            {"tool_name": "claude", "input": {"prompt": "Analyze architecture"}},
            {"tool_name": "codex", "input": {"prompt": "Generate implementation"}},
            {"tool_name": "gemini", "input": {"prompt": "Review code"}},
        ]

        result = await batch_tool.call(mock_context, description="Multi-AI analysis", invocations=invocations)

        # Check that all tools were called
        assert "claude response" in result
        assert "codex response" in result
        assert "gemini response" in result

    @pytest.mark.asyncio
    async def test_batch_with_cli_aliases(self, batch_tool, mock_context):
        """Test batch execution with CLI tool aliases."""
        invocations = [
            {
                "tool_name": "cc",  # Claude Code alias
                "input": {"prompt": "Quick analysis"},
            },
            {
                "tool_name": "oh",  # OpenHands alias
                "input": {"prompt": "Build feature"},
            },
        ]

        result = await batch_tool.call(mock_context, description="Test aliases", invocations=invocations)

        assert "cc response" in result
        assert "oh response" in result

    @pytest.mark.asyncio
    async def test_batch_cli_tools_parallel_execution(self, batch_tool, mock_context):
        """Test that CLI tools execute in parallel in batch."""
        import time

        # Add delay to mock executions
        for tool in batch_tool.tools.values():

            async def delayed_response(cmd, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return f"{tool.name} response"

            tool.execute_cli = delayed_response

        invocations = [
            {"tool_name": "claude", "input": {"prompt": "Task 1"}},
            {"tool_name": "codex", "input": {"prompt": "Task 2"}},
            {"tool_name": "gemini", "input": {"prompt": "Task 3"}},
            {"tool_name": "grok", "input": {"prompt": "Task 4"}},
        ]

        start = time.time()
        result = await batch_tool.call(mock_context, description="Parallel test", invocations=invocations)
        duration = time.time() - start

        # If executed in parallel, should take ~100ms, not 400ms
        assert duration < 0.3  # Allow some overhead
        assert all(tool in result for tool in ["claude", "codex", "gemini", "grok"])


# Integration test marker for tests requiring API keys
@pytest.mark.integration
class TestCLIToolsIntegration:
    """Integration tests for CLI tools (requires API keys)."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        context = MagicMock()
        context.session = MagicMock()
        context.session.send_log_message = AsyncMock()
        context.session.send_progress = AsyncMock()
        return context

    @pytest.fixture
    def mock_permission_manager(self):
        """Create a mock permission manager."""
        pm = MagicMock()
        pm.check_permission = Mock(return_value=True)
        return pm

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY")
    @pytest.mark.asyncio
    async def test_claude_integration(self, mock_context, mock_permission_manager):
        """Test real Claude CLI integration."""
        tool = ClaudeCLITool(mock_permission_manager)

        result = await tool.call(
            mock_context,
            prompt="Say 'Hello from Claude test'",
            model="claude-3-haiku-20240307",  # Use cheaper model for tests
        )

        assert "Hello from Claude test" in result

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
    @pytest.mark.asyncio
    async def test_codex_integration(self, mock_context, mock_permission_manager):
        """Test real OpenAI CLI integration."""
        tool = CodexCLITool(mock_permission_manager)

        result = await tool.call(
            mock_context,
            prompt="Say 'Hello from GPT test'",
            model="gpt-3.5-turbo",  # Use cheaper model for tests
        )

        assert "Hello from GPT test" in result
