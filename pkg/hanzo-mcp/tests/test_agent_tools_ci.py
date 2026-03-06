"""CI tests for unified agent tools."""

from unittest.mock import Mock

import pytest
from hanzo_tools.agent import TOOLS, register_tools
from hanzo_tools.agent.agent_tool import AgentTool
from hanzo_tools.agent.review_tool import ReviewTool
from hanzo_tools.agent.zen_tool import ZenTool


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server."""
    server = Mock()
    server.tool = Mock(return_value=lambda f: f)
    return server


class TestAgentTools:
    """Test unified agent tools work correctly."""

    def test_tools_export(self):
        """Test TOOLS exports the correct tools."""
        tool_classes = [t.__name__ for t in TOOLS]
        assert "AgentTool" in tool_classes
        assert "ZenTool" in tool_classes
        assert "ReviewTool" in tool_classes
        assert len(TOOLS) == 3

    def test_agent_tool_creation(self):
        """Test AgentTool can be created."""
        tool = AgentTool()
        assert tool.name == "agent"
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_zen_tool_creation(self):
        """Test ZenTool can be created."""
        tool = ZenTool()
        assert tool.name == "zen"
        desc_lower = tool.description.lower()
        assert "zen" in desc_lower or "64" in desc_lower or "guidance" in desc_lower

    def test_review_tool_creation(self):
        """Test ReviewTool can be created."""
        tool = ReviewTool()
        assert tool.name == "review"
        assert "review" in tool.description.lower()

    def test_all_tools_register(self, mock_mcp_server):
        """Test all agent tools register correctly."""
        tools = register_tools(mcp_server=mock_mcp_server)

        # Should return list of registered tools
        assert len(tools) == 3

        # Check tool names
        tool_names = [t.name for t in tools]
        assert "agent" in tool_names
        assert "zen" in tool_names
        assert "review" in tool_names

    def test_tool_naming_consistency(self):
        """Ensure tool naming is consistent."""
        agent = AgentTool()
        zen = ZenTool()
        review = ReviewTool()

        assert agent.name == "agent"
        assert zen.name == "zen"
        assert review.name == "review"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
