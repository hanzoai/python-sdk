"""Base test class for memory-related tests to reduce redundancy."""

from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import pytest
from fastmcp import FastMCP
from conftest import ToolTestHelper, create_mock_ctx
from hanzo_memory.models import Memory
from hanzo_mcp.tools.memory import (
    CreateMemoriesTool,
    DeleteMemoriesTool,
    RecallMemoriesTool,
    UpdateMemoriesTool,
    register_memory_tools,
)


class MemoryTestBase:
    """Base class for memory test cases with common fixtures and utilities."""

    @pytest.fixture
    def tool_helper(self):
        """Provide ToolTestHelper for tests."""
        return ToolTestHelper

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context for tool calls."""
        return create_mock_ctx()

    @pytest.fixture
    def mock_memory(self):
        """Create a standard mock memory object."""
        return Memory(
            memory_id="test_123",
            user_id="test_user",
            project_id="test_project",
            content="Test memory content",
            metadata={"type": "statement"},
            importance=1.0,
            created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00"),
            embedding=[0.1] * 1536,
        )

    @pytest.fixture
    def mock_memory_service(self):
        """Create a mock memory service with standard responses."""
        with patch("hanzo_memory.services.memory.get_memory_service") as mock_get_service:
            mock_service = Mock()

            # Set up standard responses
            mock_service.create_memory.return_value = Mock(
                memory_id="mem_123",
                user_id="test_user",
                project_id="test_project",
                content="Created memory",
                metadata={},
                importance=1.0,
            )

            mock_service.update_memory.return_value = Mock(memory_id="mem_123", content="Updated memory")

            mock_service.delete_memory.return_value = None

            mock_service.search_memories.return_value = [
                Mock(
                    memory_id="mem_123",
                    content="Found memory",
                    importance=0.9,
                    metadata={},
                )
            ]

            mock_get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mcp_server(self):
        """Create a FastMCP server instance."""
        return FastMCP("test-server")

    @pytest.fixture
    def permission_manager(self):
        """Create a permission manager with /tmp allowed."""
        from hanzo_mcp.security.permissions import PermissionManager

        pm = PermissionManager()
        pm.add_allowed_path("/tmp")
        return pm

    def assert_tool_registration(self, tools, expected_count=9):
        """Assert that the expected number of memory tools are registered."""
        assert len(tools) == expected_count
        tool_types = {type(tool) for tool in tools}
        expected_types = {
            CreateMemoriesTool,
            UpdateMemoriesTool,
            DeleteMemoriesTool,
            RecallMemoriesTool,
        }
        # Check that at least the core tools are present
        assert expected_types.issubset(tool_types)

    def create_memory_tool_params(self, **overrides):
        """Create standard parameters for memory tool calls."""
        params = {
            "user_id": "test_user",
            "project_id": "test_project",
            "content": "Test content",
            "metadata": {"type": "test"},
            "importance": 1.0,
        }
        params.update(overrides)
        return params
