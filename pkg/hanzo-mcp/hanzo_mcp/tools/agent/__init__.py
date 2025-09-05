"""Agent tools for Hanzo AI.

This module provides tools that allow Claude to delegate tasks to sub-agents,
enabling concurrent execution of multiple operations and specialized processing.
"""

from mcp.server import FastMCP

from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry

# Import the main implementations (using hanzo-agents SDK)
from hanzo_mcp.tools.agent.agent_tool import AgentTool
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.agent.network_tool import NetworkTool
from hanzo_mcp.tools.common.permissions import PermissionManager
# Import unified CLI tools (single source of truth)
from hanzo_mcp.tools.agent.cli_tools import (
    ClaudeCLITool,
    ClaudeCodeCLITool,  # cc alias
    CodexCLITool,
    GeminiCLITool,
    GrokCLITool,
    OpenHandsCLITool,
    OpenHandsShortCLITool,  # oh alias
    HanzoDevCLITool,
    ClineCLITool,
    AiderCLITool,
    register_cli_tools,
)
from hanzo_mcp.tools.agent.code_auth_tool import CodeAuthTool


def register_agent_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    agent_model: str | None = None,
    agent_max_tokens: int | None = None,
    agent_api_key: str | None = None,
    agent_base_url: str | None = None,
    agent_max_iterations: int = 10,
    agent_max_tool_uses: int = 30,
) -> list[BaseTool]:
    """Register agent tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance

        permission_manager: Permission manager for access control
        agent_model: Optional model name for agent tool in LiteLLM format
        agent_max_tokens: Optional maximum tokens for agent responses
        agent_api_key: Optional API key for the LLM provider
        agent_base_url: Optional base URL for the LLM provider API endpoint
        agent_max_iterations: Maximum number of iterations for agent (default: 10)
        agent_max_tool_uses: Maximum number of total tool uses for agent (default: 30)

    Returns:
        List of registered tools
    """
    # Create agent tool
    agent_tool = AgentTool(
        permission_manager=permission_manager,
        model=agent_model,
        api_key=agent_api_key,
        base_url=agent_base_url,
        max_tokens=agent_max_tokens,
        max_iterations=agent_max_iterations,
        max_tool_uses=agent_max_tool_uses,
    )

    # Create swarm tool
    swarm_tool = SwarmTool(
        permission_manager=permission_manager,
        model=agent_model,
        api_key=agent_api_key,
        base_url=agent_base_url,
        max_tokens=agent_max_tokens,
        agent_max_iterations=agent_max_iterations,
        agent_max_tool_uses=agent_max_tool_uses,
    )

    # Create auth management tool
    code_auth_tool = CodeAuthTool()

    # Create network tool
    network_tool = NetworkTool(
        permission_manager=permission_manager,
        default_mode="hybrid",  # Prefer local, fallback to cloud
    )

    # Register core agent tools
    ToolRegistry.register_tool(mcp_server, agent_tool)
    ToolRegistry.register_tool(mcp_server, swarm_tool)
    ToolRegistry.register_tool(mcp_server, network_tool)
    ToolRegistry.register_tool(mcp_server, code_auth_tool)

    # Register all CLI tools (includes claude, codex, gemini, grok, etc.)
    cli_tools = register_cli_tools(mcp_server, permission_manager)
    
    # Return list of registered tools
    return [
        agent_tool,
        swarm_tool,
        network_tool,
        code_auth_tool,
    ] + cli_tools
