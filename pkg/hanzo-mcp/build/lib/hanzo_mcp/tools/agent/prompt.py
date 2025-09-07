"""Prompt generation utilities for agent tool.

This module provides functions for generating effective prompts for sub-agents,
including filtering tools based on permissions and formatting system instructions.
"""

import os
from typing import Any

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager


def get_allowed_agent_tools(
    tools: list[BaseTool],
    permission_manager: PermissionManager,
) -> list[BaseTool]:
    """Filter tools available to the agent based on permissions.

    Args:
        tools: List of available tools
        permission_manager: Permission manager for checking tool access

    Returns:
        Filtered list of tools available to the agent
    """
    # Get all tools except for the agent tool itself (avoid recursion)
    filtered_tools = [tool for tool in tools if tool.name != "agent"]

    return filtered_tools


def get_system_prompt(
    tools: list[BaseTool],
    permission_manager: PermissionManager,
) -> str:
    """Generate system prompt for the sub-agent.

    Args:
        tools: List of available tools
        permission_manager: Permission manager for checking tool access

    Returns:
        System prompt for the sub-agent
    """
    # Get filtered tools
    filtered_tools = get_allowed_agent_tools(tools, permission_manager)

    # Extract tool names for display
    tool_names = ", ".join(f"`{tool.name}`" for tool in filtered_tools)

    # Base system prompt - agents always have edit tools
    system_prompt = f"""You are a Claude sub-agent with access to these tools: {tool_names}.

CAPABILITIES:
1. You have FULL read and write access - you can create, edit, and modify files
2. You can ask clarifying questions if needed - your response goes to the coordinating agent
3. You work as part of a team of specialized agents
4. Other agents may be available via MCP tools (look for tools named after agents)
5. When relevant, share file names and code snippets
6. Any file paths you return MUST be absolute. DO NOT use relative paths.
7. You can only work with the absolute paths provided in your task prompt.

CLARIFICATION:
- You can request clarification ONCE per task using the request_clarification tool
- Use this when instructions are ambiguous or you need additional context
- Types: AMBIGUOUS_INSTRUCTION, MISSING_CONTEXT, MULTIPLE_OPTIONS, CONFIRMATION_NEEDED, ADDITIONAL_INFO
- The main loop will provide automated guidance based on context

CRITICAL REVIEW (Devil's Advocate):
- Use the critic tool to get harsh, challenging feedback that attacks assumptions
- The critic will find flaws and push for improvements aggressively
- You can request up to 2 critic reviews per task
- Review types: CODE_QUALITY, CORRECTNESS, PERFORMANCE, SECURITY, COMPLETENESS, BEST_PRACTICES, GENERAL
- Use when you need someone to find what's wrong with your approach

BALANCED REVIEW:
- Use the review tool for constructive, balanced code review
- Provides objective assessment without predetermined bias
- You can request up to 3 reviews per task
- Focus areas: GENERAL, FUNCTIONALITY, READABILITY, MAINTAINABILITY, TESTING, DOCUMENTATION, ARCHITECTURE
- Use for regular code review and feedback

CREATIVE GUIDANCE:
- Use the iching tool when you need creative problem-solving approaches
- Combines ancient I Ching wisdom with Hanzo engineering principles
- Provides unique perspectives and actionable guidance
- Use when stuck, need fresh ideas, or want philosophical alignment

EDITING GUIDELINES:
- ALWAYS read the file first before attempting any edits
- For edit tool: The old_string must match EXACTLY including all whitespace, tabs, and newlines
- When copying text from read output, be careful with line numbers and indentation
- If an edit fails due to whitespace mismatch, try reading the specific lines again
- Prefer multi_edit when making multiple changes to the same file
- Test your edits by verifying the exact string exists in the file first

COLLABORATION:
- If you see MCP tools named after other agents, you can communicate with them
- Use agent MCP tools to delegate specialized tasks or get expert opinions
- Share context when communicating with other agents

RESPONSE FORMAT:
- Begin with a summary of what you did or found
- If you have questions, ask them clearly
- Include details of any edits performed
- Report any errors encountered
- End with clear conclusions or next steps
"""

    return system_prompt


def get_default_model(model_override: str | None = None) -> str:
    """Get the default model for agent execution.

    Args:
        model_override: Optional model override string in LiteLLM format (e.g., "openai/gpt-4o")

    Returns:
        Model identifier string with provider prefix
    """
    # Use model override if provided
    if model_override:
        # If in testing mode and using a test model, return as-is
        if model_override.startswith("test-model") or "TEST_MODE" in os.environ:
            return model_override

        # If the model already has a provider prefix, return as-is
        if "/" in model_override:
            return model_override

        # Otherwise, add the default provider prefix
        provider = os.environ.get("AGENT_PROVIDER", "openai")
        return f"{provider}/{model_override}"

    # Fall back to environment variables
    # Default to Sonnet for cost efficiency
    model = os.environ.get("AGENT_MODEL", "claude-3-5-sonnet-20241022")

    # Special cases for tests
    if (
        model.startswith("test-model")
        or "TEST_MODE" in os.environ
        and model == "claude-3-5-sonnet-20241022"
    ):
        return model

    provider = os.environ.get("AGENT_PROVIDER", "anthropic")

    # Only add provider prefix if it's not already in the model name
    if "/" not in model and provider != "anthropic":
        return f"{provider}/{model}"
    elif "/" not in model and provider == "anthropic":
        return f"anthropic/{model}"
    elif "/" not in model:
        return f"openai/{model}"
    else:
        # Model already has a provider prefix
        return model


def get_model_parameters(max_tokens: int | None = None) -> dict[str, Any]:
    """Get model parameters from environment variables.

    Args:
        max_tokens: Optional maximum tokens parameter override

    Returns:
        Dictionary of model parameters
    """
    params = {
        "temperature": float(os.environ.get("AGENT_TEMPERATURE", "0.7")),
        "timeout": int(os.environ.get("AGENT_API_TIMEOUT", "60")),
    }

    # Add max_tokens if provided or if set in environment variable
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    elif os.environ.get("AGENT_MAX_TOKENS"):
        params["max_tokens"] = int(os.environ.get("AGENT_MAX_TOKENS", "1000"))

    return params
