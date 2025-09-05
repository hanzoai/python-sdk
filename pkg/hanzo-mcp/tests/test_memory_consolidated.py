"""Consolidated memory tests using parametrization to reduce redundancy."""

from unittest.mock import Mock, AsyncMock, patch

import pytest
from test_memory_base import MemoryTestBase
from hanzo_mcp.tools.memory import (
    CreateMemoriesTool,
    DeleteMemoriesTool,
    RecallMemoriesTool,
    UpdateMemoriesTool,
)


class TestMemoryToolsConsolidated(MemoryTestBase):
    """Consolidated memory tool tests using parametrization."""

    @pytest.mark.parametrize(
        "tool_class,method_name,params,expected_result",
        [
            (
                CreateMemoriesTool,
                "create_memory",
                {
                    "content": "Test memory content",
                    "metadata": {"type": "test"},
                    "importance": 1.0,
                },
                "Successfully created memory mem_123",
            ),
            (
                UpdateMemoriesTool,
                "update_memory",
                {
                    "memory_id": "mem_123",
                    "content": "Updated content",
                    "metadata": {"type": "updated"},
                },
                "Would update memory mem_123",
            ),
            (
                DeleteMemoriesTool,
                "delete_memory",
                {"memory_id": "mem_123"},
                "Successfully deleted memory mem_123",
            ),
            (
                RecallMemoriesTool,
                "search_memories",
                {"query": "test query", "limit": 5},
                "Found 1 relevant memories",
            ),
        ],
    )
    async def test_memory_operations(
        self,
        tool_class,
        method_name,
        params,
        expected_result,
        mock_memory_service,
        mock_ctx,
        tool_helper,
    ):
        """Test various memory operations with parametrization."""
        # Create tool instance
        tool = tool_class(user_id="test_user", project_id="test_project")

        # Execute tool
        result = await tool_helper.run_tool(tool, params, mock_ctx)

        # Verify service method was called
        service_method = getattr(mock_memory_service, method_name)
        assert service_method.called

        # Verify result contains expected message
        assert expected_result in str(result)

    @pytest.mark.parametrize(
        "error_type,error_message,params",
        [
            (
                ValueError,
                "Memory not found",
                {"memory_id": "nonexistent", "content": "update"},
            ),
            (
                ConnectionError,
                "Database connection failed",
                {"content": "test", "metadata": {}},
            ),
            (
                PermissionError,
                "Insufficient permissions",
                {"memory_id": "protected", "content": "hack"},
            ),
        ],
    )
    async def test_memory_error_handling(
        self,
        error_type,
        error_message,
        params,
        mock_memory_service,
        mock_ctx,
        tool_helper,
    ):
        """Test error handling for memory operations."""
        # Configure service to raise error
        mock_memory_service.update_memory.side_effect = error_type(error_message)
        mock_memory_service.create_memory.side_effect = error_type(error_message)

        # Create tool (use UpdateMemoriesTool as example)
        tool = UpdateMemoriesTool(user_id="test_user", project_id="test_project")

        # Execute and expect error
        with pytest.raises(error_type, match=error_message):
            await tool_helper.run_tool(tool, params, mock_ctx)

    def test_memory_tools_registration(self, mcp_server, permission_manager):
        """Test that all memory tools are properly registered."""
        tools = register_memory_tools(
            mcp_server,
            permission_manager,
            user_id="test_user",
            project_id="test_project",
        )

        # Verify tools are registered
        self.assert_tool_registration(tools)

        # Verify each tool has correct configuration
        for tool in tools:
            if isinstance(
                tool,
                (
                    CreateMemoriesTool,
                    UpdateMemoriesTool,
                    DeleteMemoriesTool,
                    RecallMemoriesTool,
                ),
            ):
                assert tool.user_id == "test_user"
                assert tool.project_id == "test_project"

    @pytest.mark.parametrize(
        "batch_size,expected_calls",
        [
            (1, 1),
            (5, 5),
            (10, 10),
        ],
    )
    async def test_batch_memory_operations(
        self,
        batch_size,
        expected_calls,
        mock_memory_service,
        mock_ctx,
        tool_helper,
    ):
        """Test batch memory operations with different sizes."""
        tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")

        # Execute multiple operations
        for i in range(batch_size):
            params = {
                "content": f"Batch memory {i}",
                "metadata": {"index": i},
                "importance": 0.5 + (i * 0.1),
            }
            await tool_helper.run_tool(tool, params, mock_ctx)

        # Verify correct number of service calls
        assert mock_memory_service.create_memory.call_count == expected_calls

    @pytest.mark.parametrize(
        "memory_type,metadata,importance",
        [
            ("statement", {"type": "statement", "source": "user"}, 1.0),
            ("question", {"type": "question", "context": "test"}, 0.5),
            ("fact", {"type": "fact", "verified": True}, 0.9),
            ("emotion", {"type": "emotion", "sentiment": "positive"}, 0.7),
        ],
    )
    async def test_memory_types(
        self,
        memory_type,
        metadata,
        importance,
        mock_memory_service,
        mock_ctx,
        tool_helper,
    ):
        """Test different memory types and metadata."""
        tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")

        params = {
            "content": f"Test {memory_type} memory",
            "metadata": metadata,
            "importance": importance,
        }

        result = await tool_helper.run_tool(tool, params, mock_ctx)

        # Verify service was called with correct parameters
        mock_memory_service.create_memory.assert_called_once()
        call_args = mock_memory_service.create_memory.call_args[1]
        assert call_args["metadata"] == metadata
        assert call_args["importance"] == importance
