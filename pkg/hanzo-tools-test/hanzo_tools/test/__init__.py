"""Test and validation tools for Hanzo AI (HIP-0300).

Tools:
- test: Unified test/validation tool (HIP-0300)
  - run: Execute test/lint/typecheck
  - detect: Auto-detect available tools

Kinds: test | lint | typecheck

Effect lattice position: NONDETERMINISTIC_EFFECT
Wraps process execution with structured Report output.

Install:
    pip install hanzo-tools-test

Usage:
    from hanzo_tools.test import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access the unified tool
    from hanzo_tools.test import TestTool
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .test_tool import TestTool, test_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [TestTool]

__all__ = [
    "TestTool",
    "test_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register test tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional options (cwd, etc.)

    Returns:
        List of registered tool instances
    """
    cwd = kwargs.get("cwd")
    tool = TestTool(cwd=cwd)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
