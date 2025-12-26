"""Common utilities for Hanzo AI tools.

Core thinking tools:
- think: Structured reasoning
- critic: Critical analysis

Dynamic tool management:
- tool_install: Install, update, reload tools dynamically
- tool_enable/tool_disable: Enable/disable tools at runtime

Note: batch tool is DEPRECATED in 1.0.0 - use `dag` from shell tools instead.
"""

import warnings
from mcp.server import FastMCP

from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.common.critic_tool import CriticTool
from hanzo_mcp.tools.common.thinking_tool import ThinkingTool
from hanzo_mcp.tools.common.tool_install import ToolInstallTool, register_tool_install


def register_thinking_tool(mcp_server: FastMCP) -> list[BaseTool]:
    """Register thinking tool with the MCP server."""
    thinking_tool = ThinkingTool()
    ToolRegistry.register_tool(mcp_server, thinking_tool)
    return [thinking_tool]


def register_critic_tool(mcp_server: FastMCP) -> list[BaseTool]:
    """Register critic tool with the MCP server."""
    critic_tool = CriticTool()
    ToolRegistry.register_tool(mcp_server, critic_tool)
    return [critic_tool]


def register_batch_tool(mcp_server: FastMCP, tools: dict[str, BaseTool]) -> None:
    """DEPRECATED: Use `dag` tool from shell package instead.
    
    The dag tool provides DAG execution with serial, parallel, and mixed modes.
    It can invoke any tool, not just shell commands.
    
    Migration:
        # Old (batch)
        batch(invocations=[{"tool_name": "read", "input": {...}}])
        
        # New (dag)  
        dag([{"tool": "read", "input": {...}}], parallel=True)
    """
    warnings.warn(
        "batch tool is deprecated in 1.0.0. Use 'dag' from shell tools instead. "
        "dag([{\"tool\": \"name\", \"input\": {...}}], parallel=True)",
        DeprecationWarning,
        stacklevel=2,
    )
    # Still register for backward compatibility
    from hanzo_mcp.tools.common.batch_tool import BatchTool
    batch_tool = BatchTool(tools)
    ToolRegistry.register_tool(mcp_server, batch_tool)
