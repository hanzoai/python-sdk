"""CI tests for unified agent tools."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from hanzo_tools.agent import TOOLS, register_tools
from hanzo_tools.agent.iching_tool import IChingTool
from hanzo_tools.agent.review_tool import ReviewTool
from hanzo_tools.agent.unified_agent_tool import UnifiedAgentTool


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server."""
    server = Mock()
    server.tool = Mock(return_value=lambda f: f)
    return server


class TestUnifiedAgentTools:
    """Test unified agent tools work correctly."""

    def test_tools_export(self):
        """Test TOOLS exports the correct tools."""
        tool_classes = [t.__name__ for t in TOOLS]
        assert "UnifiedAgentTool" in tool_classes
        assert "IChingTool" in tool_classes
        assert "ReviewTool" in tool_classes
        assert len(TOOLS) == 3

    def test_unified_agent_tool_creation(self):
        """Test UnifiedAgentTool can be created."""
        tool = UnifiedAgentTool()
        assert tool.name == "agent"
        assert "claude" in tool.description.lower() or "agent" in tool.description.lower()

    def test_unified_agent_tool_agents(self):
        """Test UnifiedAgentTool has expected agents."""
        tool = UnifiedAgentTool()
        # Core agents
        assert "claude" in tool.AGENTS
        assert "codex" in tool.AGENTS
        assert "gemini" in tool.AGENTS
        assert "grok" in tool.AGENTS
        # Extended agents
        assert "qwen" in tool.AGENTS
        assert "vibe" in tool.AGENTS
        assert "code" in tool.AGENTS
        assert "dev" in tool.AGENTS
        # Total 8 agents
        assert len(tool.AGENTS) == 8

    def test_unified_agent_tool_list_agents(self):
        """Test agent listing."""
        tool = UnifiedAgentTool()
        result = tool._list_agents()
        assert "Available agents:" in result
        assert "claude" in result
        assert "codex" in result

    def test_iching_tool_creation(self):
        """Test IChingTool can be created."""
        tool = IChingTool()
        assert tool.name == "iching"
        desc_lower = tool.description.lower()
        assert "i ching" in desc_lower or "wisdom" in desc_lower or "hexagram" in desc_lower

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
        assert "iching" in tool_names
        assert "review" in tool_names

    def test_tool_naming_consistency(self):
        """Ensure tool naming is consistent."""
        agent = UnifiedAgentTool()
        iching = IChingTool()
        review = ReviewTool()

        assert agent.name == "agent"
        assert iching.name == "iching"
        assert review.name == "review"

    def test_agent_config_sharing(self):
        """Test agent shares MCP config with spawned agents."""
        tool = UnifiedAgentTool()
        config = tool._mcp_config
        # Config is a dict
        assert isinstance(config, dict)

    def test_claude_env_detection(self):
        """Test Claude Code environment detection."""
        tool = UnifiedAgentTool()
        env = tool._claude_env
        # Should have expected keys
        assert "running_in_claude" in env
        assert "session_id" in env
        assert "auth_token" in env
        assert "api_key" in env

    def test_default_agent_selection(self):
        """Test default agent selection logic."""
        tool = UnifiedAgentTool()
        default = tool._get_default_agent()
        # Should return a valid agent name
        assert default in tool.AGENTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
