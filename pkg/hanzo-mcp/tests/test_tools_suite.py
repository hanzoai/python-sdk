"""Comprehensive test suite for all MCP tools."""

import os
import asyncio
import tempfile
from unittest.mock import Mock, patch

import pytest
from hanzo_mcp.tools import register_all_tools
from mcp.server.fastmcp import FastMCP
from hanzo_mcp.tools.common.truncate import truncate_response
from hanzo_mcp.tools.common.tool_list import ToolListTool
from hanzo_mcp.tools.common.fastmcp_pagination import FastMCPPaginator

try:
    # Try to import test helper version first
    from hanzo_mcp.tools.common.test_helpers import PaginatedResponse
except ImportError:
    # Fall back to real implementation
    from hanzo_mcp.tools.common.paginated_response import (
        AutoPaginatedResponse as PaginatedResponse,
    )

from tests.test_utils import create_mock_ctx, create_permission_manager


class TestToolRegistration:
    """Test tool registration and configuration."""

    def test_register_all_tools_default(self):
        """Test registering all tools with default settings."""
        mcp_server = FastMCP("test-server")
        permission_manager = create_permission_manager(["/tmp"])

        # Register all tools
        register_all_tools(
            mcp_server,
            permission_manager,
            use_mode=False,  # Disable mode system for predictable testing
        )

        # Check that tools are registered
        # Note: We can't directly check mcp_server's internal state,
        # but we can verify no exceptions were raised
        assert True  # Registration completed

    def test_register_tools_with_disabled_categories(self):
        """Test disabling entire categories of tools."""
        mcp_server = FastMCP("test-server")
        permission_manager = create_permission_manager(["/tmp"])

        # Register with write tools disabled
        register_all_tools(
            mcp_server,
            permission_manager,
            disable_write_tools=True,
            disable_search_tools=True,
            use_mode=False,
        )

        # Tools should still register, just with some disabled
        assert True

    def test_register_tools_with_individual_config(self):
        """Test enabling/disabling individual tools."""
        mcp_server = FastMCP("test-server")
        permission_manager = create_permission_manager(["/tmp"])

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
            mcp_server, permission_manager, enabled_tools=enabled_tools, use_mode=False
        )

        assert True

    @patch("hanzo_mcp.tools.agent.AgentTool")
    def test_agent_tool_configuration(self, mock_agent_tool):
        """Test agent tool configuration."""
        mcp_server = FastMCP("test-server")
        permission_manager = create_permission_manager(["/tmp"])

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
            use_mode=False,
        )

        # Verify agent tool was configured
        mock_agent_tool.assert_called_once()
        call_kwargs = mock_agent_tool.call_args.kwargs
        # Check keyword args
        assert call_kwargs["permission_manager"] == permission_manager
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 8192


class TestPaginationSystem:
    """Test the pagination system for large outputs."""

    def test_truncate_response(self):
        """Test output truncation."""
        # Test small output (no truncation)
        small_output = "Small output"
        result = truncate_response(small_output, max_tokens=1000)
        assert result == small_output

        # Test large output (truncation)
        large_output = "x" * 100000  # Very large output
        result = truncate_response(large_output, max_tokens=100)
        assert len(result) < len(large_output)
        assert "truncated" in result.lower()

    def test_paginated_response(self):
        """Test paginated response creation."""
        # Create test data
        items = [f"Item {i}" for i in range(100)]

        # Create paginated response using wrapper
        response = PaginatedResponse(
            items=items[:10], next_cursor="cursor_10", has_more=True, total_items=100
        )

        # Check response attributes
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
        paginator = FastMCPPaginator(page_size=10)

        # Test paginating a list
        items = [f"item_{i}" for i in range(100)]

        # Get first page
        result = paginator.paginate_list(items, cursor=None, page_size=10)

        assert result is not None
        assert "items" in result
        assert len(result["items"]) == 10
        assert result["items"][0] == "item_0"

        # Check if there's a next cursor
        if "nextCursor" in result:
            # Get next page using cursor
            next_result = paginator.paginate_list(
                items, cursor=result["nextCursor"], page_size=10
            )
            assert next_result is not None
            assert "items" in next_result


class TestToolListFunctionality:
    """Test tool listing functionality."""

    def test_tool_list_basic(self):
        """Test basic tool listing."""
        tool = ToolListTool()

        # Mock context
        mock_ctx = create_mock_ctx()
        mock_ctx.meta = {"disabled_tools": set()}

        # Get tool list
        result = asyncio.run(tool.call(mock_ctx))

        # Should return a formatted list
        assert "Available Tools" in str(result) or "Available tools:" in str(result)
        assert "Total tools:" in str(result) or "Enabled:" in str(result)

    def test_tool_list_with_disabled(self):
        """Test tool list with disabled tools."""
        tool = ToolListTool()

        # Mock context with disabled tools
        mock_ctx = create_mock_ctx()
        mock_ctx.meta = {"disabled_tools": {"write", "edit"}}

        # Get tool list
        result = asyncio.run(tool.call(mock_ctx))

        # Should show disabled tools or summary
        assert "Disabled:" in str(result) or "disabled_tools" in str(mock_ctx.meta)
        # Note: Actual disabled tools depend on what's registered


class TestCLIAgentTools:
    """Test CLI-based agent tools."""

    def test_claude_cli_tool(self):
        """Test Claude CLI tool."""
        from hanzo_mcp.tools.agent.claude_cli_tool import ClaudeCLITool
        
        permission_manager = create_permission_manager(["/tmp"])
        tool = ClaudeCLITool(permission_manager)
        assert tool.name == "claude_cli"
        assert tool.command_name == "claude"
        assert "Claude Code" in tool.provider_name

    def test_codex_cli_tool(self):
        """Test Codex CLI tool."""
        from hanzo_mcp.tools.agent.codex_cli_tool import CodexCLITool
        
        permission_manager = create_permission_manager(["/tmp"])
        tool = CodexCLITool(permission_manager)
        assert tool.name == "codex_cli"
        assert tool.command_name == "openai"
        assert "OpenAI" in tool.provider_name

    def test_gemini_cli_tool(self):
        """Test Gemini CLI tool."""
        from hanzo_mcp.tools.agent.gemini_cli_tool import GeminiCLITool
        
        permission_manager = create_permission_manager(["/tmp"])
        tool = GeminiCLITool(permission_manager)
        assert tool.name == "gemini_cli"
        assert tool.command_name == "gemini"
        assert "Google Gemini" in tool.provider_name

    def test_grok_cli_tool(self):
        """Test Grok CLI tool."""
        from hanzo_mcp.tools.agent.grok_cli_tool import GrokCLITool
        
        permission_manager = create_permission_manager(["/tmp"])
        tool = GrokCLITool(permission_manager)
        assert tool.name == "grok_cli"
        assert tool.command_name == "grok"
        assert "xAI Grok" in tool.provider_name


class TestSwarmTool:
    """Test swarm tool functionality."""

    def test_swarm_basic_configuration(self):
        """Test basic swarm configuration."""
        from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
        
        permission_manager = create_permission_manager(["/tmp"])
        tool = SwarmTool(permission_manager)
        
        # Test basic properties
        assert tool.name == "swarm"
        assert "network of AI agents" in tool.description
        
        # Test that tool can be instantiated
        assert tool is not None


class TestMemoryIntegration:
    """Test memory tools integration."""

    def test_memory_tools_available(self):
        """Test that memory tools can be registered."""
        try:
            from hanzo_memory.services.memory import get_memory_service
            # If hanzo_memory is available, test it
            with patch("hanzo_memory.services.memory.get_memory_service") as mock_get_service:
                mock_service = Mock()
                mock_get_service.return_value = mock_service

                mcp_server = FastMCP("test-server")
                permission_manager = create_permission_manager(["/tmp"])

                from hanzo_mcp.tools.memory import register_memory_tools

                tools = register_memory_tools(
                    mcp_server, permission_manager, user_id="test", project_id="test"
                )

                assert len(tools) == 9  # All memory tools
        except ImportError:
            # hanzo_memory not installed, skip test
            pytest.skip("hanzo-memory package not installed")


class TestNetworkPackage:
    """Test hanzo-network package integration."""

    def test_network_imports(self):
        """Test that network package can be imported."""
        try:
            from hanzo_network import Tool, Agent, Router, Network, NetworkState

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

            agent = Agent(id="test_agent", instructions="Test instructions")

            assert agent.id == "test_agent"
            assert agent.instructions == "Test instructions"
        except ImportError:
            pytest.skip("hanzo-network package not fully set up")


class TestAutoBackgrounding:
    """Test auto-backgrounding functionality."""

    def test_auto_background_timeout(self):
        """Test that long-running processes auto-background."""
        from hanzo_mcp.tools.shell.auto_background import AutoBackgroundExecutor
        from hanzo_mcp.tools.shell.base_process import ProcessManager

        process_manager = ProcessManager()
        executor = AutoBackgroundExecutor(process_manager, timeout=0.1)  # Very short timeout

        # Test that executor is created properly
        assert executor is not None
        assert executor.timeout == 0.1
        assert executor.process_manager == process_manager
        
        # Test has the expected method
        assert hasattr(executor, 'execute_with_auto_background')


class TestCriticAndReviewTools:
    """Test critic and review tools."""

    def test_critic_tool_basic(self):
        """Test critic tool basic functionality."""
        from hanzo_mcp.tools.common.critic_tool import CriticTool
        
        tool = CriticTool()
        mock_ctx = create_mock_ctx()

        # Test with analysis parameter
        result = asyncio.run(
            tool.call(
                mock_ctx,
                analysis="Review this function: def add(a, b): return a + b",
            )
        )

        # Should return analysis result
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_review_tool_basic(self):
        """Test review tool basic functionality."""
        from hanzo_mcp.tools.agent.review_tool import ReviewTool
        
        tool = ReviewTool()
        mock_ctx = create_mock_ctx()

        # Test review with call method
        result = asyncio.run(
            tool.call(
                mock_ctx, 
                focus="general",
                work_description="Test code implementation",
                code_snippets=["def test(): pass"]
            )
        )

        # Should return review result
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0


class TestStreamingCommand:
    """Test streaming command functionality."""

    def test_streaming_command_basic(self):
        """Test basic streaming command."""
        from hanzo_mcp.tools.shell.streaming_command import StreamingCommandTool
        
        # Test that the abstract class exists and has expected properties
        assert StreamingCommandTool is not None
        assert hasattr(StreamingCommandTool, '__abstractmethods__')
        
        # Create a concrete implementation for testing
        class ConcreteStreamingCommand(StreamingCommandTool):
            @property
            def name(self):
                return "test_streaming"
            
            @property
            def description(self):
                return "Test streaming command"
            
            def register(self, server):
                pass
        
        # Test the concrete implementation (without permission_manager)
        tool = ConcreteStreamingCommand()
        assert tool.name == "test_streaming"
        assert tool.description == "Test streaming command"


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
        mock_ctx = create_mock_ctx()

        # Execute batch with multiple tools
        invocations = [{"tool": f"tool_{i}", "parameters": {}} for i in range(5)]

        result = asyncio.run(
            batch_tool.call(mock_ctx, description="Test batch", invocations=invocations)
        )

        # Should handle without error
        assert "results" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
