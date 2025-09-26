"""Tool adapters for converting between MCP tools and OpenAI tools.

This module handles conversion between MCP tool formats and OpenAI function
formats, making MCP tools available to the OpenAI API, and processing tool inputs
and outputs for agent execution.
"""

# Import litellm with warnings suppressed
import warnings

from openai.types import FunctionParameters
from openai.types.chat import ChatCompletionToolParam

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)

from hanzo_mcp.tools.common.base import BaseTool


def convert_tools_to_openai_functions(
    tools: list[BaseTool],
) -> list[ChatCompletionToolParam]:
    """Convert MCP tools to OpenAI function format.

    Args:
        tools: List of MCP tools

    Returns:
        List of tools formatted for OpenAI API
    """
    openai_tools: list[ChatCompletionToolParam] = []
    for tool in tools:
        openai_tool: ChatCompletionToolParam = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": convert_tool_parameters(tool),
            },
        }
        openai_tools.append(openai_tool)
    return openai_tools


def convert_tool_parameters(tool: BaseTool) -> FunctionParameters:
    """Convert tool parameters to OpenAI format.

    Args:
        tool: MCP tool

    Returns:
        Parameter schema in OpenAI format
    """
    # Start with a copy of the parameters
    params = tool.parameters.copy()

    # Ensure the schema has the right format for OpenAI
    if "properties" not in params:
        params["properties"] = {}

    if "type" not in params:
        params["type"] = "object"

    if "required" not in params:
        params["required"] = tool.required

    return params


def supports_parallel_function_calling(model: str) -> bool:
    """Check if a model supports parallel function calling.

    Args:
        model: Model identifier in LiteLLM format (e.g., "openai/gpt-4-turbo-preview")

    Returns:
        True if the model supports parallel function calling, False otherwise
    """
    # Since litellm doesn't have this function, we'll implement a simple check
    # based on known models that support parallel function calling
    parallel_capable_models = {
        # OpenAI models that support parallel function calling
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4-turbo-2024-04-09",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-2024-05-13",
        "gpt-4o-2024-08-06",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        # Anthropic models with tool support
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3-5-sonnet",
        "claude-3-5-sonnet-20241022",
    }

    # Extract model name without provider prefix
    model_name = model.split("/")[-1] if "/" in model else model

    # Check if the base model name matches any known parallel-capable models
    for capable_model in parallel_capable_models:
        if model_name.startswith(capable_model):
            return True

    return False
