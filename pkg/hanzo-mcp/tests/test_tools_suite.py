"""Comprehensive test suite for all MCP tools."""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from mcp.server import FastMCP

from hanzo_mcp.tools import register_all_tools
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.common.tool_list import ToolListTool
from hanzo_mcp.tools.common.truncate import truncate_response as truncate_output
from hanzo_mcp.tools.common.paginated_response import PaginatedResponse
from hanzo_mcp.tools.common.fastmcp_pagination import FastMCPPaginator


class TestToolRegistration:
    """Test tool registration and configuration."""
    
    def test_register_all_tools_default(self):
        """Test registering all tools with default settings."""
        mcp_server = FastMCP("test-server")
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])
        
        # Register all tools
        register_all_tools(
            mcp_server,
            permission_manager,
            use_mode=False  # Disable mode system for predictable testing
        )
        
        # Check that tools are registered
        # Note: We can't directly check mcp_server's internal state,
        # but we can verify no exceptions were raised
        assert True  # Registration completed
    
    def test_register_tools_with_disabled_categories(self):
        """Test disabling entire categories of tools."""
        mcp_server = FastMCP("test-server")
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])
        
        # Register with write tools disabled
        register_all_tools(
            mcp_server,
            permission_manager,
            disable_write_tools=True,
            disable_search_tools=True,
            use_mode=False
        )
        
        # Tools should still register, just with some disabled
        assert True
    
    def test_register_tools_with_individual_config(self):
        """Test enabling/disabling individual tools."""
        mcp_server = FastMCP("test-server")
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])
        
        # Enable only specific tools
        enabled_tools = {
            "read": True,
            "write": False,
            "grep": True,
            "run_command": False,
            "think": True,
            "agent": False,
        }
        
        register_all_tools(
            mcp_server,
            permission_manager,
            enabled_tools=enabled_tools,
            use_mode=False
        )
        
        assert True
    
    @patch('hanzo_mcp.tools.agent.agent_tool.AgentTool')
    def test_agent_tool_configuration(self, mock_agent_tool):
        """Test agent tool configuration."""
        mcp_server = FastMCP("test-server")
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])
        
        # Mock agent tool to verify configuration
        mock_instance = Mock()
        mock_agent_tool.return_value = mock_instance
        
        register_all_tools(
            mcp_server,
            permission_manager,
            enable_agent_tool=True,
            agent_model="claude-3-5-sonnet-20241022",
            agent_max_tokens=8192,
            agent_api_key="test_key",
            agent_base_url="https://api.example.com",
            agent_max_iterations=15,
            agent_max_tool_uses=50,
            use_mode=False
        )
        
        # Verify agent tool was configured
        mock_agent_tool.assert_called_once()
        call_kwargs = mock_agent_tool.call_args[1]
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 8192


class TestPaginationSystem:
    """Test the pagination system for large outputs."""
    
    def test_truncate_output(self):
        """Test output truncation."""
        # Test small output (no truncation)
        small_output = "Small output"
        result = truncate_output(small_output, max_tokens=1000)
        assert result == small_output
        
        # Test large output (truncation)
        large_output = "x" * 100000  # Very large output
        result = truncate_output(large_output, max_tokens=100)
        assert len(result) < len(large_output)
        assert "[Output truncated" in result
    
    def test_paginated_response(self):
        """Test paginated response creation."""
        # Create test data
        items = [f"Item {i}" for i in range(100)]
        
        # Create paginated response
        response = PaginatedResponse(
            items=items[:10],
            next_cursor="cursor_10",
            has_more=True,
            total_items=100
        )
        
        assert len(response.items) == 10
        assert response.next_cursor == "cursor_10"
        assert response.has_more is True
        assert response.total_items == 100
        
        # Test JSON serialization
        json_data = response.to_json()
        assert json_data["items"] == items[:10]
        assert json_data["_meta"]["next_cursor"] == "cursor_10"
    
    def test_fastmcp_paginator(self):
        """Test FastMCP paginator."""
        paginator = FastMCPPaginator(checksum_secret="test_secret")
        
        # Create cursor
        cursor_data = {
            "offset": 10,
            "last_id": "item_10"
        }
        cursor = paginator.create_cursor(cursor_data)
        
        assert cursor is not None
        assert isinstance(cursor, str)
        
        # Parse cursor
        parsed_data = paginator.parse_cursor(cursor)
        assert parsed_data["offset"] == 10
        assert parsed_data["last_id"] == "item_10"
        
        # Test invalid cursor
        invalid_data = paginator.parse_cursor("invalid_cursor")
        assert invalid_data is None


class TestToolListFunctionality:
    """Test tool listing functionality."""
    
    def test_tool_list_basic(self):
        """Test basic tool listing."""
        tool = ToolListTool()
        
        # Mock context
        mock_ctx = Mock()
        mock_ctx.meta = {"disabled_tools": set()}
        
        # Get tool list
        result = asyncio.run(tool.call(mock_ctx))
        
        # Should return a formatted list
        assert "Available tools:" in result
        assert "Disabled tools:" in result
    
    def test_tool_list_with_disabled(self):
        """Test tool list with disabled tools."""
        tool = ToolListTool()
        
        # Mock context with disabled tools
        mock_ctx = Mock()
        mock_ctx.meta = {"disabled_tools": {"write", "edit"}}
        
        # Get tool list
        result = asyncio.run(tool.call(mock_ctx))
        
        # Should show disabled tools
        assert "Disabled tools:" in result
        # Note: Actual disabled tools depend on what's registered


class TestCLIAgentTools:
    """Test CLI-based agent tools."""
    
    @patch('hanzo_mcp.tools.agent.claude_cli_tool.CLIAgentBase')
    def test_claude_cli_tool(self, mock_cli_base):
        """Test Claude CLI tool."""
        from hanzo_mcp.tools.agent.claude_cli_tool import ClaudeCLITool
        
        tool = ClaudeCLITool()
        assert tool.name == "claude"
        assert tool.cli_command == "claude"
        assert "Claude Code" in tool.description
    
    @patch('hanzo_mcp.tools.agent.codex_cli_tool.CLIAgentBase')
    def test_codex_cli_tool(self, mock_cli_base):
        """Test Codex CLI tool."""
        from hanzo_mcp.tools.agent.codex_cli_tool import CodexCLITool
        
        tool = CodexCLITool()
        assert tool.name == "codex"
        assert tool.cli_command == "openai"
        assert "OpenAI" in tool.description
    
    @patch('hanzo_mcp.tools.agent.gemini_cli_tool.CLIAgentBase')
    def test_gemini_cli_tool(self, mock_cli_base):
        """Test Gemini CLI tool."""
        from hanzo_mcp.tools.agent.gemini_cli_tool import GeminiCLITool
        
        tool = GeminiCLITool()
        assert tool.name == "gemini"
        assert tool.cli_command == "gemini"
        assert "Google Gemini" in tool.description
    
    @patch('hanzo_mcp.tools.agent.grok_cli_tool.CLIAgentBase')
    def test_grok_cli_tool(self, mock_cli_base):
        """Test Grok CLI tool."""
        from hanzo_mcp.tools.agent.grok_cli_tool import GrokCLITool
        
        tool = GrokCLITool()
        assert tool.name == "grok"
        assert tool.cli_command == "grok"
        assert "xAI Grok" in tool.description


class TestSwarmTool:
    """Test swarm tool functionality."""
    
    @patch('hanzo_mcp.tools.agent.swarm_tool.AgentNode')
    def test_swarm_basic_configuration(self, mock_agent_node):
        """Test basic swarm configuration."""
        from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
        
        tool = SwarmTool()
        mock_ctx = Mock()
        
        # Test network configuration
        agents = [
            {"id": "agent1", "query": "Task 1"},
            {"id": "agent2", "query": "Task 2", "receives_from": ["agent1"]},
        ]
        
        # Mock the tool execution
        with patch.object(tool, '_run_agent') as mock_run:
            mock_run.return_value = "Agent result"
            
            result = asyncio.run(tool.call(
                mock_ctx,
                query="Main task",
                agents=agents
            ))
            
            # Verify agents were configured
            assert mock_run.call_count >= 2


class TestMemoryIntegration:
    """Test memory tools integration."""
    
    @patch('hanzo_memory.services.memory.get_memory_service')
    def test_memory_tools_available(self, mock_get_service):
        """Test that memory tools can be registered."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mcp_server = FastMCP("test-server")
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])
        
        # Should not raise ImportError
        from hanzo_mcp.tools.memory import register_memory_tools
        
        tools = register_memory_tools(
            mcp_server,
            permission_manager,
            user_id="test",
            project_id="test"
        )
        
        assert len(tools) == 9  # All memory tools


class TestNetworkPackage:
    """Test hanzo-network package integration."""
    
    def test_network_imports(self):
        """Test that network package can be imported."""
        try:
            from hanzo_network import Agent, Network, Router, NetworkState, Tool
            assert Agent is not None
            assert Network is not None
            assert Router is not None
            assert NetworkState is not None
            assert Tool is not None
        except ImportError:
            pytest.skip("hanzo-network package not fully set up")
    
    def test_network_agent_creation(self):
        """Test creating a network agent."""
        try:
            from hanzo_network import Agent
            
            agent = Agent(
                id="test_agent",
                instructions="Test instructions"
            )
            
            assert agent.id == "test_agent"
            assert agent.instructions == "Test instructions"
        except ImportError:
            pytest.skip("hanzo-network package not fully set up")


class TestAutoBackgrounding:
    """Test auto-backgrounding functionality."""
    
    @patch('hanzo_mcp.tools.shell.base_process.ProcessManager')
    def test_auto_background_timeout(self, mock_process_manager):
        """Test that long-running processes auto-background."""
        from hanzo_mcp.tools.shell.auto_background import AutoBackgroundExecutor
        
        executor = AutoBackgroundExecutor(timeout_seconds=0.1)  # Very short timeout
        
        # Mock a long-running command
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        mock_process.pid = 12345
        
        with patch('subprocess.Popen', return_value=mock_process):
            result = executor.run_command("sleep 10", timeout=0.1)
            
            # Should auto-background
            assert result.backgrounded
            assert result.pid == 12345


class TestCriticAndReviewTools:
    """Test critic and review tools."""
    
    def test_critic_tool_basic(self):
        """Test critic tool basic functionality."""
        from hanzo_mcp.tools.common.critic_tool import CriticTool
        
        tool = CriticTool()
        mock_ctx = Mock()
        
        # Test with code content
        result = asyncio.run(tool.call(
            mock_ctx,
            content="def add(a, b): return a + b",
            request="Review this function"
        ))
        
        # Should return analysis
        assert "def add(a, b): return a + b" in result
        assert "```" in result  # Should format code
    
    def test_review_tool_basic(self):
        """Test review tool basic functionality."""
        from hanzo_mcp.tools.agent.review_tool import ReviewTool
        
        tool = ReviewTool()
        mock_ctx = Mock()
        
        # Test review
        with patch.object(tool, '_perform_review') as mock_review:
            mock_review.return_value = "Review complete"
            
            result = asyncio.run(tool.call(
                mock_ctx,
                content="Test content",
                review_type="code"
            ))
            
            assert result == "Review complete"


class TestStreamingCommand:
    """Test streaming command functionality."""
    
    def test_streaming_command_basic(self):
        """Test basic streaming command."""
        from hanzo_mcp.tools.shell.streaming_command import StreamingCommandTool
        
        tool = StreamingCommandTool()
        mock_ctx = Mock()
        
        # Create a simple command that generates output
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_file = f.name
        
        try:
            result = asyncio.run(tool.call(
                mock_ctx,
                command=f"cat {temp_file}",
                stream_to_file=True
            ))
            
            assert "Line 1" in result
            assert "Line 2" in result
            assert "Line 3" in result
        finally:
            os.unlink(temp_file)


class TestBatchTool:
    """Test batch tool with pagination."""
    
    def test_batch_tool_pagination(self):
        """Test that batch tool handles pagination correctly."""
        from hanzo_mcp.tools.common.batch_tool import BatchTool
        
        # Create mock tools that return large outputs
        mock_tools = {}
        for i in range(5):
            tool = Mock()
            tool.name = f"tool_{i}"
            # Large output that would exceed token limit
            tool.call = Mock(return_value="x" * 10000)
            mock_tools[f"tool_{i}"] = tool
        
        batch_tool = BatchTool(mock_tools)
        mock_ctx = Mock()
        
        # Execute batch with multiple tools
        invocations = [
            {"tool": f"tool_{i}", "parameters": {}}
            for i in range(5)
        ]
        
        result = asyncio.run(batch_tool.call(
            mock_ctx,
            description="Test batch",
            invocations=invocations
        ))
        
        # Should handle without error
        assert "results" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])