"""Tests for hanzo-tools-agent."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import agent

        assert agent is not None

    def test_import_tools(self):
        from hanzo_tools.agent import TOOLS

        assert len(TOOLS) > 0

    def test_import_agent_tool(self):
        from hanzo_tools.agent import AgentTool

        assert AgentTool.name == "agent"


class TestAgentTool:
    """Tests for AgentTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.agent import AgentTool

        return AgentTool()

    def test_has_description(self, tool):
        assert tool.description
        assert "agent" in tool.description.lower()

    def test_has_agent_configs(self, tool):
        assert hasattr(tool, "agents") or hasattr(tool, "agent_configs")
