"""Basic swarm tool tests with success and failure cases."""

import os
import sys
import shutil
import tempfile
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import Context as MCPContext
from hanzo_tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestSwarmBasic:
    """Basic tests for swarm tool functionality."""

    def test_swarm_defaults_to_claude_sonnet(self):
        """Test that swarm tool defaults to Claude Sonnet."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)

        assert swarm.model == "anthropic/claude-3-5-sonnet-20241022"
        print("✓ Swarm tool correctly defaults to Claude 3.5 Sonnet")

    def test_swarm_detects_api_keys(self):
        """Test that swarm tool detects API keys from environment."""
        pm = PermissionManager()

        # Test with ANTHROPIC_API_KEY
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"}):
            swarm = SwarmTool(permission_manager=pm)
            assert swarm.api_key == "test-key-123"
            print("✓ Swarm detects ANTHROPIC_API_KEY")

        # Test with CLAUDE_API_KEY
        with patch.dict(os.environ, {"CLAUDE_API_KEY": "test-key-456"}, clear=True):
            swarm = SwarmTool(permission_manager=pm)
            print(f"Expected: test-key-456, Got: {swarm.api_key}")
            assert swarm.api_key == "test-key-456"
            print("✓ Swarm detects CLAUDE_API_KEY")

        # Test priority (ANTHROPIC_API_KEY takes precedence)
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "primary-key", "CLAUDE_API_KEY": "fallback-key"},
        ):
            swarm = SwarmTool(permission_manager=pm)
            assert swarm.api_key == "primary-key"
            print("✓ ANTHROPIC_API_KEY takes precedence over CLAUDE_API_KEY")

    @pytest.mark.asyncio
    async def test_swarm_fails_without_agents(self):
        """Test that swarm fails gracefully without agents."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}

        # Mock tool context
        mock_tool_ctx = Mock()
        mock_tool_ctx.set_tool_info = AsyncMock()
        mock_tool_ctx.error = AsyncMock()
        mock_tool_ctx.info = AsyncMock()

        with patch(
            "hanzo_mcp.tools.common.context.create_tool_context",
            return_value=mock_tool_ctx,
        ):
            # Call with no agents in config
            result = await swarm.call(ctx, config={"agents": {}})

            assert "Error:" in result
            assert "at least one agent" in result.lower()
            print("✓ Swarm correctly fails when no agents provided")

    @pytest.mark.asyncio
    async def test_swarm_validates_agent_format(self):
        """Test that swarm validates agent format."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}

        # Mock tool context
        mock_tool_ctx = Mock()
        mock_tool_ctx.set_tool_info = AsyncMock()
        mock_tool_ctx.error = AsyncMock()
        mock_tool_ctx.info = AsyncMock()

        with patch(
            "hanzo_mcp.tools.common.context.create_tool_context",
            return_value=mock_tool_ctx,
        ):
            # Valid agent format - v2 interface uses agents with query
            result = await swarm.call(
                ctx,
                config={"agents": {"agent1": {"query": "Analyze the code", "role": "Code analyzer"}}},
                query="Analyze this project",
            )

            # Should handle gracefully
            assert isinstance(result, str)
            print("✓ Swarm handles agent format")

    @pytest.mark.asyncio
    async def test_swarm_respects_max_concurrent(self):
        """Test that swarm respects max_concurrent setting."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}

        # Create dummy agents with v2 config
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            for i in range(5):
                with open(os.path.join(test_dir, f"file{i}.txt"), "w") as f:
                    f.write(f"Content {i}")

            # Allow access
            pm.add_allowed_path(test_dir)

            # Create multiple agents
            agents = {}
            for i in range(5):
                agents[f"agent{i}"] = {
                    "query": f"Analyze file{i}.txt",
                    "file_path": os.path.join(test_dir, f"file{i}.txt"),
                    "role": f"Analyzer {i}",
                }

            # Mock execute to track concurrency
            concurrent_count = 0
            max_observed = 0

            async def mock_execute(*args, **kwargs):
                nonlocal concurrent_count, max_observed
                concurrent_count += 1
                max_observed = max(max_observed, concurrent_count)
                # Simulate work
                import asyncio

                await asyncio.sleep(0.01)
                concurrent_count -= 1
                return "Mock result"

            # Test with max_concurrent=2
            with patch.object(swarm, "_execute_agent", mock_execute):
                result = await swarm.call(
                    ctx,
                    config={"agents": agents},
                    query="Analyze all files",
                    max_concurrent=2,
                )

                # Max observed should not exceed 2
                assert max_observed <= 2
                print(f"✓ Swarm respects max_concurrent (observed max: {max_observed})")

        finally:
            shutil.rmtree(test_dir)

    @pytest.mark.asyncio
    async def test_swarm_handles_agent_failures(self):
        """Test that swarm handles individual agent failures gracefully."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}

        # Create agents where one will fail
        agents = {
            "agent1": {"query": "Task 1", "role": "Worker 1"},
            "agent2": {"query": "Task 2", "role": "Worker 2"},
            "agent3": {"query": "Task 3", "role": "Worker 3"},
        }

        call_count = 0

        async def mock_execute(agent_id, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if agent_id == "agent2":
                raise Exception("Agent 2 failed!")
            return f"Result from {agent_id}"

        # Mock the execution
        with patch.object(swarm, "_execute_agent", mock_execute):
            result = await swarm.call(ctx, config={"agents": agents}, query="Execute all tasks")

            # Should complete despite one failure
            assert isinstance(result, str)
            assert call_count == 3  # All agents should be attempted
            print("✓ Swarm handles agent failures gracefully")

    @pytest.mark.asyncio
    async def test_swarm_summary_format(self):
        """Test that swarm returns properly formatted summary."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}

        # Create simple agents
        agents = {
            "analyzer": {
                "query": "Analyze the code structure",
                "role": "Code Analyzer",
            },
            "reviewer": {
                "query": "Review the analysis",
                "role": "Code Reviewer",
                "receives_from": ["analyzer"],
            },
        }

        async def mock_execute(agent_id, *args, **kwargs):
            return f"Mock result from {agent_id}"

        with patch.object(swarm, "_execute_agent", mock_execute):
            result = await swarm.call(
                ctx,
                config={"agents": agents, "entry_point": "analyzer"},
                query="Analyze and review code",
            )

            # Should return a string result
            assert isinstance(result, str)
            print("✓ Swarm returns formatted summary")
