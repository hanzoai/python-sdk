"""Plan orchestration tools for Hanzo AI (HIP-0300).

Tools:
- plan: Unified orchestration tool (HIP-0300)
  - intent: Parse NL → IntentIR
  - route: IntentIR → Plan (canonical chain)
  - compose: Plan → ExecGraph
  - chains: List available canonical chains

This is the "permissive input → strict output" layer.
Turns natural language into canonical operator chains.

Effect lattice position: PURE
All operations are safe to cache and parallelize.

Install:
    pip install hanzo-tools-plan

Usage:
    from hanzo_tools.plan import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access the unified tool
    from hanzo_tools.plan import PlanTool
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .plan_tool import PlanTool, plan_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [PlanTool]

__all__ = [
    "PlanTool",
    "plan_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register plan tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional options

    Returns:
        List of registered tool instances
    """
    tool = PlanTool()
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
