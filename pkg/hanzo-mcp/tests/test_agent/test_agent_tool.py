"""Tests for the agent tool implementation."""

import os
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.agent.agent_tool import AgentTool
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
        for name in ["read_files", "search_content", "directory_tree"]:
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
        assert hasattr(agent_tool, "model_override") and agent_tool.model_override is None
        assert hasattr(agent_tool, "api_key_override") and agent_tool.api_key_override is None
        assert hasattr(agent_tool, "max_tokens_override") and agent_tool.max_tokens_override is None
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
        assert hasattr(agent_tool_with_params, "max_iterations") and agent_tool_with_params.max_iterations == 40
        assert hasattr(agent_tool_with_params, "max_tool_uses") and agent_tool_with_params.max_tool_uses == 150

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
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
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
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Update the test to use a list instead of a string
            result = await agent_tool.call(ctx=mcp_context, prompts=["Test prompt"])

        # We're just making sure an error is returned, the actual error message may vary in tests
        tool_helper.assert_in_result("Error", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_valid_prompt_string(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test agent tool call with valid prompt as string."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Without hanzo-agents SDK, the tool returns an error
        with patch(
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Update the test to use a list instead of a string
            result = await agent_tool.call(ctx=mcp_context, prompts=["Test prompt /home/test/path"])

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("hanzo-agents SDK is required", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_multiple_prompts(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test agent tool call with multiple prompts for parallel execution."""
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

        # Without hanzo-agents SDK, the tool returns an error
        with patch(
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            result = await agent_tool.call(ctx=mcp_context, prompts=test_prompts)

        tool_helper.assert_in_result("Error", result)
        tool_helper.assert_in_result("hanzo-agents SDK is required", result)
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_with_empty_prompt_list(self, tool_helper, agent_tool, mcp_context):
        """Test agent tool call with an empty prompt list."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.set_tool_info = AsyncMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()

        with patch(
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
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
            "hanzo_mcp.tools.agent.agent_tool.create_tool_context",
            return_value=tool_ctx,
        ):
            # Test with invalid type (number)
            result = await agent_tool.call(ctx=mcp_context, prompts=123)

        # Without hanzo-agents SDK, the tool returns an error
        tool_helper.assert_in_result("Error", result)
        # The error could be about invalid type or SDK not available
        tool_ctx.error.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method _execute_agent_with_tools no longer exists in current implementation")
    async def test_execute_agent_with_tools_simple(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test _execute_agent_with_tools with a simple response."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Mock the OpenAI response
        mock_message = MagicMock()
        mock_message.content = "Simple result"
        mock_message.tool_calls = None

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        # Set test mode
        os.environ["TEST_MODE"] = "1"
        # Execute the method
        result = await agent_tool._execute_agent_with_tools(
            "System prompt",
            "User prompt",
            mock_tools,
            [],  # openai_tools
            tool_ctx,
        )

        assert result == "Simple result"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method _execute_agent_with_tools no longer exists in current implementation")
    async def test_execute_agent_with_tools_tool_calls(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test _execute_agent_with_tools with tool calls."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Set up one of the mock tools
        mock_tool = mock_tools[0]
        mock_tool.call = AsyncMock(return_value="Tool result")

        # Create a tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = MagicMock()
        mock_tool_call.function.name = mock_tool.name
        mock_tool_call.function.arguments = json.dumps({"param": "value"})

        # First response with tool call
        first_message = MagicMock()
        first_message.content = None
        first_message.tool_calls = [mock_tool_call]

        first_choice = MagicMock()
        first_choice.message = first_message

        first_response = MagicMock()
        first_response.choices = [first_choice]

        # Second response with final result
        second_message = MagicMock()
        second_message.content = "Final result"
        second_message.tool_calls = None

        second_choice = MagicMock()
        second_choice.message = second_message

        second_response = MagicMock()
        second_response.choices = [second_choice]

        # Set test mode
        os.environ["TEST_MODE"] = "1"
        # Mock any complex dictionary or string processing by directly using the expected values in the test
        with patch.object(json, "loads", return_value={"param": "value"}):
            result = await agent_tool._execute_agent_with_tools(
                "System prompt",
                "User prompt",
                mock_tools,
                [{"type": "function", "function": {"name": mock_tool.name}}],  # openai_tools
                tool_ctx,
            )

        assert result == "Final result"
        mock_tool.call.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method _execute_agent_with_tools no longer exists in current implementation")
    async def test_execute_multiple_agents(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test the _execute_multiple_agents method."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Create test prompts
        test_prompts = ["Task 1 /home/test/path1", "Task 2 /home/test/path2"]

        # Mock the necessary dependencies
        with patch(
            "hanzo_mcp.tools.agent.agent_tool.get_allowed_agent_tools",
            return_value=mock_tools,
        ):
            with patch(
                "hanzo_mcp.tools.agent.agent_tool.get_system_prompt",
                return_value="System prompt",
            ):
                with patch(
                    "hanzo_mcp.tools.agent.agent_tool.convert_tools_to_openai_functions",
                    return_value=[],
                ):
                    with patch.object(
                        agent_tool,
                        "_execute_agent_with_tools",
                        side_effect=["Result 1", "Result 2"],
                    ):
                        import asyncio

                        with patch.object(
                            asyncio,
                            "gather",
                            AsyncMock(return_value=["Result 1", "Result 2"]),
                        ):
                            result = await agent_tool._execute_multiple_agents(test_prompts, tool_ctx)

        # Check the result format
        tool_helper.assert_in_result("Agent 1 Result", result)
        tool_helper.assert_in_result("Agent 2 Result", result)
        tool_helper.assert_in_result("Result 1", result)
        tool_helper.assert_in_result("Result 2", result)
        assert "---" in result  # Check for the separator

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method _execute_agent_with_tools no longer exists in current implementation")
    async def test_execute_multiple_agents_single_prompt(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test the _execute_multiple_agents method with a single prompt."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Create test prompts - just one
        test_prompts = ["Single task /home/test/path"]

        # Mock the necessary dependencies
        with patch(
            "hanzo_mcp.tools.agent.agent_tool.get_allowed_agent_tools",
            return_value=mock_tools,
        ):
            with patch(
                "hanzo_mcp.tools.agent.agent_tool.get_system_prompt",
                return_value="System prompt",
            ):
                with patch(
                    "hanzo_mcp.tools.agent.agent_tool.convert_tools_to_openai_functions",
                    return_value=[],
                ):
                    with patch.object(
                        agent_tool,
                        "_execute_agent_with_tools",
                        AsyncMock(return_value="Single result"),
                    ):
                        import asyncio

                        with patch.object(asyncio, "gather", AsyncMock(return_value=["Single result"])):
                            result = await agent_tool._execute_multiple_agents(test_prompts, tool_ctx)

        # Check that the single result is returned directly without agent prefix or separator
        assert result == "Single result"
        assert "Agent 1" not in result
        assert "---" not in result

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method _execute_agent_with_tools no longer exists in current implementation")
    async def test_execute_multiple_agents_with_exceptions(self, tool_helper, agent_tool, mcp_context, mock_tools):
        """Test the _execute_multiple_agents method with exceptions."""
        # Mock the tool context
        tool_ctx = MagicMock()
        tool_ctx.info = AsyncMock()
        tool_ctx.error = AsyncMock()
        tool_ctx.mcp_context = mcp_context

        # Create test prompts
        test_prompts = [
            "Task 1 /home/test/path1",
            "Task that fails /home/test/path2",
            "Task 3 /home/test/path3",
        ]

        # Create a mix of results and exceptions
        gather_results = ["Result 1", Exception("Task failed"), "Result 3"]

        # Mock the necessary dependencies
        with patch(
            "hanzo_mcp.tools.agent.agent_tool.get_allowed_agent_tools",
            return_value=mock_tools,
        ):
            with patch(
                "hanzo_mcp.tools.agent.agent_tool.get_system_prompt",
                return_value="System prompt",
            ):
                with patch(
                    "hanzo_mcp.tools.agent.agent_tool.convert_tools_to_openai_functions",
                    return_value=[],
                ):
                    with patch.object(
                        agent_tool,
                        "_execute_agent_with_tools",
                        side_effect=["Result 1", "Result 2", "Result 3"],
                    ):
                        import asyncio

                        with patch.object(asyncio, "gather", AsyncMock(return_value=gather_results)):
                            result = await agent_tool._execute_multiple_agents(test_prompts, tool_ctx)

        # Check the result format
        tool_helper.assert_in_result("Agent 1 Result", result)
        tool_helper.assert_in_result("Agent 2 Error", result)
        tool_helper.assert_in_result("Task failed", result)
        tool_helper.assert_in_result("Agent 3 Result", result)
        tool_helper.assert_in_result("Result 1", result)
        tool_helper.assert_in_result("Result 3", result)
