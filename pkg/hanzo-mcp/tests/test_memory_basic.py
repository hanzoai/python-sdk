"""Basic memory test to debug issues."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch


def test_basic_memory():
    """Basic test without pytest complexity."""
    with patch("hanzo_memory.services.memory.get_memory_service") as mock_get_service:
        with patch(
            "hanzo_mcp.tools.memory.memory_tools.create_tool_context"
        ) as mock_create_tool_context:
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
            mock_ctx = Mock()
            mock_ctx.request_id = "test-request-id"

            # Call the tool
            result = asyncio.run(
                tool.call(
                    mock_ctx,
                    statements=["This is a test memory", "This is another test"],
                )
            )

            print(f"Result: {result}")
            print(
                f"create_memory called: {mock_service.create_memory.call_count} times"
            )

            # Check result
            assert "Successfully created 2 new memories" in str(result)
            assert mock_service.create_memory.call_count == 2

            print("Test passed!")


if __name__ == "__main__":
    test_basic_memory()
