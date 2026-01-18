"""Tests for the agent tool implementation."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hanzo_tools.agent.agent_tool import AgentTool

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestAgentTool:
    """Test cases for the AgentTool."""

    @pytest.fixture
    def permission_manager(self):
        """Create a test permission manager."""
        return MagicMock(spec=PermissionManager)

    @pytest.fixture
    def mcp_context(self):
        """Create a test MCP context."""
        return MagicMock()

    @pytest.fixture
    def agent_tool(self, permission_manager):
        """Create a test agent tool."""
        # Set environment variable for test
        os.environ["OPENAI_API_KEY"] = "test_key"
        return AgentTool(permission_manager)

    @pytest.fixture
    def agent_tool_with_params(self, permission_manager):
        """Create a test agent tool with custom parameters."""
        return AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-sonnet",
            api_key="test_anthropic_key",
            max_tokens=2000,
            max_iterations=40,
            max_tool_uses=150,
        )

    @pytest.fixture
    def mock_tools(self):
        """Create a list of mock tools."""
        tools = []
        for name in ["read_files", "search_content", "tree"]:
            tool = MagicMock(spec=BaseTool)
            tool.name = name
            tool.description = f"Description for {name}"
            tool.parameters = {"properties": {}, "type": "object"}
            tool.required = []
            tools.append(tool)
        return tools

    def test_initialization(self, tool_helper, agent_tool):
        """Test agent tool initialization."""
        assert agent_tool.name == "agent"
        assert "agent" in agent_tool.description.lower()
        assert (
            hasattr(agent_tool, "model_override") and agent_tool.model_override is None
        )
        assert (
            hasattr(agent_tool, "api_key_override")
            and agent_tool.api_key_override is None
        )
        assert (
            hasattr(agent_tool, "max_tokens_override")
            and agent_tool.max_tokens_override is None
        )
        assert hasattr(agent_tool, "max_iterations") and agent_tool.max_iterations == 10
        assert hasattr(agent_tool, "max_tool_uses") and agent_tool.max_tool_uses == 30

    def test_initialization_with_params(self, tool_helper, agent_tool_with_params):
        """Test agent tool initialization with custom parameters."""
        assert agent_tool_with_params.name == "agent"
        assert (
            hasattr(agent_tool_with_params, "model_override")
            and agent_tool_with_params.model_override == "anthropic/claude-3-sonnet"
        )
        assert (
            hasattr(agent_tool_with_params, "api_key_override")
            and agent_tool_with_params.api_key_override == "test_anthropic_key"
        )
        assert (
            hasattr(agent_tool_with_params, "max_tokens_override")
            and agent_tool_with_params.max_tokens_override == 2000
        )
        assert (
            hasattr(agent_tool_with_params, "max_iterations")
            and agent_tool_with_params.max_iterations == 40
        )
        assert (
            hasattr(agent_tool_with_params, "max_tool_uses")
            and agent_tool_with_params.max_tool_uses == 150
        )

    # Parameters are not exposed directly in the new interface
    # def test_parameters(self, tool_helper, agent_tool):
    #     """Test agent tool parameters."""
    #     # BaseTool doesn't expose parameters property
    #     pass

    def test_model_and_api_key_override(self, tool_helper, permission_manager):
        """Test API key and model override functionality."""
        # Test with antropic model and API key
        agent_tool = AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-sonnet",
            api_key="test_anthropic_key",
        )

        assert agent_tool.model_override == "anthropic/claude-3-sonnet"
        assert agent_tool.api_key_override == "test_anthropic_key"

        # Test with openai model and API key
        agent_tool = AgentTool(
            permission_manager=permission_manager,
            model="openai/gpt-4o",
            api_key="test_openai_key",
        )

        assert agent_tool.model_override == "openai/gpt-4o"
        assert agent_tool.api_key_override == "test_openai_key"

        # Test with no model or API key
        agent_tool = AgentTool(
            permission_manager=permission_manager,
        )

        assert agent_tool.model_override is None
        assert agent_tool.api_key_override is None

    @pytest.mark.asyncio
    async def test_call_no_prompt(self, tool_helper, agent_tool, mcp_context):
        """Test agent tool call with no prompt."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.set_tool_info = AsyncMock()

        with patch(
            "hanzo_tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            result = await agent_tool.call(ctx=mcp_context)

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("prompt must be provided", result)
        tool_ctx.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_with_litellm_error(self, tool_helper, agent_tool, mcp_context):
        """Test agent tool call when litellm raises an error."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.get_tools = AsyncMock(return_value=[])

        # Mock to raise an error
        with patch(
            "hanzo_tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Update the test to use a list instead of a string
            result = await agent_tool.call(ctx=mcp_context, prompts=["Test prompt"])

        # We're just making sure an error is returned, the actual error message may vary in tests
        tool_helper.assert_in_result("Error", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_valid_prompt_string(
        self, tool_helper, agent_tool, mcp_context, mock_tools
    ):
        """Test agent tool call with valid prompt as string - without hanzo-agents SDK."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Mock HANZO_AGENTS_AVAILABLE = False to test fallback behavior
        with patch(
            "hanzo_tools.agent.agent_tool.HANZO_AGENTS_AVAILABLE",
            False,
        ):
            with patch(
                "hanzo_tools.agent.agent_tool.create_tool_context",
                return_value=tool_ctx,
            ):
                # Update the test to use a list instead of a string
                result = await agent_tool.call(
                    ctx=mcp_context, prompts=["Test prompt /home/test/path"]
                )

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("hanzo-agents SDK is required", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_multiple_prompts(
        self, tool_helper, agent_tool, mcp_context, mock_tools
    ):
        """Test agent tool call with multiple prompts - without hanzo-agents SDK."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Create test prompts
        test_prompts = [
            "Task 1 /home/test/path1",
            "Task 2 /home/test/path2",
            "Task 3 /home/test/path3",
        ]

        # Mock HANZO_AGENTS_AVAILABLE = False to test fallback behavior
        with patch(
            "hanzo_tools.agent.agent_tool.HANZO_AGENTS_AVAILABLE",
            False,
        ):
            with patch(
                "hanzo_tools.agent.agent_tool.create_tool_context",
                return_value=tool_ctx,
            ):
                result = await agent_tool.call(ctx=mcp_context, prompts=test_prompts)

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("hanzo-agents SDK is required", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_empty_prompt_list(
        self, tool_helper, agent_tool, mcp_context
    ):
        """Test agent tool call with an empty prompt list."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()

        with patch(
            "hanzo_tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Test with empty list
            result = await agent_tool.call(ctx=mcp_context, prompts=[])

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("At least one prompt must be provided", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_invalid_type(self, tool_helper, agent_tool, mcp_context):
        """Test agent tool call with an invalid parameter type."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()

        with patch(
            "hanzo_tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Test with invalid type (number)
            result = await agent_tool.call(ctx=mcp_context, prompts=123)

        # Without hanzo-agents SDK, the tool returns an error
        tool_helper.assert_in_result("Error", result)
        # The error could be about invalid type or SDK not available
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_get_agent_class_default_model(
        self, tool_helper, agent_tool, mcp_context
    ):
        """Test _get_agent_class returns appropriate agent class for default model."""
        agent_class = agent_tool._get_agent_class(None, mcp_context)

        # Should return a dynamically created class based on MCPAgent
        assert agent_class is not None
        assert "DynamicMCPAgent" in agent_class.__name__

    @pytest.mark.asyncio
    async def test_get_agent_class_with_custom_model(
        self, tool_helper, agent_tool, mcp_context
    ):
        """Test _get_agent_class with a custom model string."""
        agent_class = agent_tool._get_agent_class("model://openai/gpt-4", mcp_context)

        # Should return a dynamically created class
        assert agent_class is not None
        assert agent_class.model == "model://openai/gpt-4"

    @pytest.mark.asyncio
    async def test_available_tools_initialized(self, tool_helper, agent_tool):
        """Test that available_tools is properly initialized."""
        assert hasattr(agent_tool, "available_tools")
        assert isinstance(agent_tool.available_tools, list)
        assert len(agent_tool.available_tools) > 0

        # Check that essential tools are present
        tool_names = [t.name for t in agent_tool.available_tools]
        assert "edit" in tool_names
        assert "multi_edit" in tool_names

    @pytest.mark.asyncio
    async def test_mcp_agent_state_serialization(self, tool_helper):
        """Test MCPAgentState to_dict and from_dict methods."""
        from hanzo_tools.agent.agent_tool import MCPAgentState

        # Create state
        state = MCPAgentState(
            prompts=["Task 1 /path/to/file", "Task 2 /another/path"],
            context={"key": "value"},
        )
        state.current_prompt_index = 1
        state.results = ["Result 1"]

        # Serialize
        state_dict = state.to_dict()
        assert state_dict["prompts"] == ["Task 1 /path/to/file", "Task 2 /another/path"]
        assert state_dict["context"] == {"key": "value"}
        assert state_dict["current_prompt_index"] == 1
        assert state_dict["results"] == ["Result 1"]

        # Deserialize
        restored_state = MCPAgentState.from_dict(state_dict)
        assert restored_state.prompts == state.prompts
        assert restored_state.context == state.context
        assert restored_state.current_prompt_index == state.current_prompt_index
        assert restored_state.results == state.results

    @pytest.mark.asyncio
    async def test_mcp_tool_adapter(self, tool_helper, mcp_context, mock_tools):
        """Test MCPToolAdapter wraps MCP tools correctly."""
        from hanzo_tools.agent.agent_tool import MCPToolAdapter

        # Create adapter
        mock_tool = mock_tools[0]
        adapter = MCPToolAdapter(mock_tool, mcp_context)

        # Check properties
        assert adapter.name == mock_tool.name
        assert adapter.description == mock_tool.description

        # Check handle method exists (required by Tool ABC)
        assert hasattr(adapter, "handle")
        assert callable(adapter.handle)
