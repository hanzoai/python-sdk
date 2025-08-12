"""Test memory tools integration with hanzo-memory package."""

from unittest.mock import Mock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from hanzo_mcp.tools.common.permissions import PermissionManager

from tests.test_utils import ToolTestHelper, create_mock_ctx

# Check if hanzo-memory is available
try:
    from hanzo_mcp.tools.memory import register_memory_tools

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Skip all tests if hanzo-memory is not available
pytestmark = pytest.mark.skipif(
    not MEMORY_AVAILABLE, reason="hanzo-memory package not installed"
)


def test_memory_tools_registration():
    """Test that memory tools can be registered properly."""
    # Create mock MCP server
    mcp_server = FastMCP("test-server")

    # Create permission manager
    permission_manager = PermissionManager()
    permission_manager.add_allowed_path("/tmp")

    # Try to register memory tools
    try:
        tools = register_memory_tools(
            mcp_server,
            permission_manager,
            user_id="test_user",
            project_id="test_project",
        )

        # Should have 9 tools registered
        assert len(tools) == 9

        # Check tool names
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "recall_memories",
            "create_memories",
            "update_memories",
            "delete_memories",
            "manage_memories",
            "recall_facts",
            "store_facts",
            "summarize_to_memory",
            "manage_knowledge_bases",
        ]

        for name in expected_names:
            assert name in tool_names

    except ImportError as e:
        # Re-raise the exception to properly fail the test
        raise


def test_memory_tool_descriptions():
    """Test that memory tools have proper descriptions."""
    try:
        from hanzo_mcp.tools.memory.memory_tools import (
            CreateMemoriesTool,
            ManageMemoriesTool,
            RecallMemoriesTool,
        )
        from hanzo_mcp.tools.memory.knowledge_tools import (
            StoreFactsTool,
            RecallFactsTool,
            SummarizeToMemoryTool,
        )

        # Test memory tools
        recall_tool = RecallMemoriesTool()
        assert "recall memories" in recall_tool.description.lower()
        assert "scope" in recall_tool.description

        create_tool = CreateMemoriesTool()
        assert (
            "save" in create_tool.description.lower()
            and "memory" in create_tool.description.lower()
        )

        manage_tool = ManageMemoriesTool()
        assert (
            "create, update" in manage_tool.description.lower()
            or "atomic operation" in manage_tool.description.lower()
        )

        # Test knowledge tools
        facts_tool = RecallFactsTool()
        assert "facts" in facts_tool.description.lower()
        assert "knowledge bases" in facts_tool.description.lower()

        store_facts = StoreFactsTool()
        assert (
            "store" in store_facts.description.lower()
            and "facts" in store_facts.description.lower()
        )

        summarize_tool = SummarizeToMemoryTool()
        assert "summarize" in summarize_tool.description.lower()

    except ImportError as e:
        # Re-raise the exception to properly fail the test
        raise


@patch("hanzo_mcp.tools.memory.memory_tools.create_tool_context")
@patch("hanzo_memory.services.memory.get_memory_service")
def test_memory_tool_usage(mock_get_service, mock_create_tool_context):
    """Test basic memory tool usage."""
    # Mock the tool context
    mock_tool_ctx = Mock()
    mock_tool_ctx.set_tool_info = AsyncMock()
    mock_tool_ctx.info = AsyncMock()
    mock_tool_ctx.send_completion_ping = AsyncMock()
    mock_create_tool_context.return_value = mock_tool_ctx

    # Mock the memory service
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mock memory creation
    from datetime import datetime

    from hanzo_memory.models.memory import Memory

    mock_memory = Memory(
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
    mock_service.create_memory.return_value = mock_memory

    # Create and test the tool
    from hanzo_mcp.tools.memory.memory_tools import CreateMemoriesTool

    tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")

    # Mock context
    mock_ctx = create_mock_ctx()

    # Call the tool
    import asyncio

    result = asyncio.run(
        tool.call(
            mock_ctx, statements=["This is a test memory", "This is another test"]
        )
    )

    print(f"DEBUG: Result = {result}")

    # Verify result
    ToolTestHelper.assert_in_result("Successfully created 2 new memories", result)

    # Verify service was called correctly
    assert mock_service.create_memory.call_count == 2


@patch("hanzo_mcp.tools.memory.knowledge_tools.create_tool_context")
@patch("hanzo_memory.services.memory.get_memory_service")
def test_knowledge_tool_usage(mock_get_service, mock_create_tool_context):
    """Test knowledge tool usage."""
    # Mock the tool context
    mock_tool_ctx = Mock()
    mock_tool_ctx.set_tool_info = AsyncMock()
    mock_tool_ctx.info = AsyncMock()
    mock_tool_ctx.send_completion_ping = AsyncMock()
    mock_create_tool_context.return_value = mock_tool_ctx

    # Mock the memory service
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mock memory creation for facts
    from datetime import datetime

    from hanzo_memory.models.memory import Memory

    mock_memory = Memory(
        memory_id="fact_123",
        user_id="test_user",
        project_id="test_project",
        content="fact: Python uses indentation",
        metadata={"type": "fact", "kb_name": "python_basics"},
        importance=1.5,
        created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2024-01-01T00:00:00"),
        embedding=[0.1] * 1536,
    )
    mock_service.create_memory.return_value = mock_memory

    # Create and test the tool
    from hanzo_mcp.tools.memory.knowledge_tools import StoreFactsTool

    tool = StoreFactsTool(user_id="test_user", project_id="test_project")

    # Mock context
    mock_ctx = create_mock_ctx()

    # Call the tool
    import asyncio

    result = asyncio.run(
        tool.call(
            mock_ctx,
            facts=["Python uses indentation for blocks"],
            kb_name="python_basics",
            scope="project",
        )
    )

    # Verify result
    ToolTestHelper.assert_in_result(
        "Successfully stored 1 facts in python_basics", result
    )

    # Verify service was called with correct metadata
    mock_service.create_memory.assert_called_with(
        user_id="test_user",
        project_id="test_project",
        content="fact: Python uses indentation for blocks",
        metadata={"type": "fact", "kb_name": "python_basics"},
        importance=1.5,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
