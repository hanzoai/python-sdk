"""Test utilities specific to memory tests."""

from unittest.mock import Mock, AsyncMock, patch

from hanzo_mcp.tools.common.context import ToolContext


def create_memory_mock_ctx():
    """Create a mock context that works with memory tools."""
    mock_ctx = Mock()
    mock_ctx.request_id = "test-request-id"
    mock_ctx.client_id = "test-client-id"

    # Create a mock that returns a proper tool context
    mock_tool_ctx = Mock(spec=ToolContext)
    mock_tool_ctx.set_tool_info = AsyncMock()
    mock_tool_ctx.info = AsyncMock()
    mock_tool_ctx.debug = AsyncMock()
    mock_tool_ctx.warning = AsyncMock()
    mock_tool_ctx.error = AsyncMock()
    mock_tool_ctx.send_completion_ping = AsyncMock()

    # Patch create_tool_context to return our mock
    with patch(
        "hanzo_mcp.tools.memory.memory_tools.create_tool_context",
        return_value=mock_tool_ctx,
    ):
        yield mock_ctx, mock_tool_ctx
