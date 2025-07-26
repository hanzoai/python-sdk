"""Test edge cases for the batch tool to prevent errors."""

import asyncio
from unittest.mock import Mock, AsyncMock, patch

import pytest
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.batch_tool import BatchTool


class TestBatchToolEdgeCases:
    """Test edge cases for the batch tool."""
    
    @pytest.fixture
    def mock_ctx(self):
        """Create a mock MCP context."""
        ctx = Mock(spec=MCPContext)
        ctx.meta = {"tool_manager": Mock()}
        return ctx
    
    @pytest.fixture
    def batch_tool(self):
        """Create a batch tool instance."""
        return BatchTool()
    
    @pytest.mark.asyncio
    async def test_empty_invocations_error(self, batch_tool, mock_ctx):
        """Test that empty invocations list raises an error."""
        with pytest.raises(Exception):
            await batch_tool.call(
                ctx=mock_ctx,
                description="Test batch",
                invocations=[]  # Empty list should fail
            )
    
    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, batch_tool, mock_ctx):
        """Test handling of invalid tool names."""
        # Mock tool manager to return None for invalid tool
        mock_ctx.meta["tool_manager"].get_tool = Mock(return_value=None)
        
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Test invalid tool",
            invocations=[{
                "tool_name": "nonexistent_tool",
                "input": {}
            }]
        )
        
        # Should handle gracefully
        assert "results" in result
        assert len(result["results"]) == 1
        assert "error" in result["results"][0]
    
    @pytest.mark.asyncio
    async def test_tool_execution_error(self, batch_tool, mock_ctx):
        """Test handling of tool execution errors."""
        # Mock a tool that raises an exception
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.call.side_effect = Exception("Tool execution failed")
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(return_value=mock_tool)
        
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Test error handling",
            invocations=[{
                "tool_name": "test_tool",
                "input": {"param": "value"}
            }]
        )
        
        # Should capture the error
        assert "results" in result
        assert len(result["results"]) == 1
        assert "error" in result["results"][0]
        assert "Tool execution failed" in result["results"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self, batch_tool, mock_ctx):
        """Test batch with both successful and failing tools."""
        # Mock tools
        success_tool = AsyncMock()
        success_tool.name = "success_tool"
        success_tool.call.return_value = {"result": "success"}
        
        fail_tool = AsyncMock()
        fail_tool.name = "fail_tool"
        fail_tool.call.side_effect = Exception("Failed")
        
        def get_tool(name):
            if name == "success_tool":
                return success_tool
            elif name == "fail_tool":
                return fail_tool
            return None
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(side_effect=get_tool)
        
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Mixed results",
            invocations=[
                {"tool_name": "success_tool", "input": {}},
                {"tool_name": "fail_tool", "input": {}},
                {"tool_name": "success_tool", "input": {"param": "2"}},
            ]
        )
        
        assert "results" in result
        assert len(result["results"]) == 3
        
        # First should succeed
        assert result["results"][0]["tool_name"] == "success_tool"
        assert "error" not in result["results"][0]
        
        # Second should fail
        assert result["results"][1]["tool_name"] == "fail_tool"
        assert "error" in result["results"][1]
        
        # Third should succeed
        assert result["results"][2]["tool_name"] == "success_tool"
        assert "error" not in result["results"][2]
    
    @pytest.mark.asyncio
    async def test_large_batch_pagination(self, batch_tool, mock_ctx):
        """Test pagination with large batch results."""
        # Mock a tool that returns large output
        mock_tool = AsyncMock()
        mock_tool.name = "large_output_tool"
        mock_tool.call.return_value = "X" * 100000  # 100KB output
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(return_value=mock_tool)
        
        # Create many invocations
        invocations = [
            {"tool_name": "large_output_tool", "input": {"id": i}}
            for i in range(50)
        ]
        
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Large batch",
            invocations=invocations
        )
        
        # Should handle pagination
        assert "results" in result
        # May have pagination info if output is too large
        if "_pagination" in result:
            assert "cursor" in result["_pagination"]
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_limit(self, batch_tool, mock_ctx):
        """Test that concurrent execution respects limits."""
        execution_times = []
        
        async def slow_tool_call(*args, **kwargs):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # Simulate work
            execution_times.append(start)
            return {"result": "done"}
        
        mock_tool = AsyncMock()
        mock_tool.name = "slow_tool"
        mock_tool.call = slow_tool_call
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(return_value=mock_tool)
        
        # Create many invocations
        invocations = [
            {"tool_name": "slow_tool", "input": {"id": i}}
            for i in range(20)
        ]
        
        start_time = asyncio.get_event_loop().time()
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Concurrent test",
            invocations=invocations
        )
        end_time = asyncio.get_event_loop().time()
        
        # Check that execution was concurrent but limited
        total_time = end_time - start_time
        
        # If all ran sequentially, would take 2 seconds (20 * 0.1)
        # If all ran in parallel with no limit, would take ~0.1 seconds
        # With concurrency limit, should be somewhere in between
        assert total_time < 2.0  # Confirms some parallelism
        assert total_time > 0.2  # Confirms concurrency limit
    
    @pytest.mark.asyncio
    async def test_invalid_input_types(self, batch_tool, mock_ctx):
        """Test handling of invalid input types."""
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.call.return_value = {"result": "ok"}
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(return_value=mock_tool)
        
        # Test with various invalid input types
        test_cases = [
            # String instead of dict
            {"tool_name": "test_tool", "input": "not a dict"},
            # List instead of dict
            {"tool_name": "test_tool", "input": ["not", "a", "dict"]},
            # None input
            {"tool_name": "test_tool", "input": None},
        ]
        
        for invalid_invocation in test_cases:
            # Should handle gracefully or convert
            result = await batch_tool.call(
                ctx=mock_ctx,
                description="Invalid input test",
                invocations=[invalid_invocation]
            )
            
            assert "results" in result
            # Either handles it or returns error
    
    @pytest.mark.asyncio
    async def test_tool_name_normalization(self, batch_tool, mock_ctx):
        """Test that tool names are normalized properly."""
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.call.return_value = {"result": "ok"}
        
        def get_tool(name):
            # Normalize name
            normalized = name.lower().strip()
            if normalized == "test_tool":
                return mock_tool
            return None
        
        mock_ctx.meta["tool_manager"].get_tool = Mock(side_effect=get_tool)
        
        # Test with various name formats
        invocations = [
            {"tool_name": "TEST_TOOL", "input": {}},
            {"tool_name": " test_tool ", "input": {}},
            {"tool_name": "Test_Tool", "input": {}},
        ]
        
        result = await batch_tool.call(
            ctx=mock_ctx,
            description="Name normalization",
            invocations=invocations
        )
        
        # Should handle all variations
        assert "results" in result
        for r in result["results"]:
            if "error" not in r:
                assert r["output"]["result"] == "ok"