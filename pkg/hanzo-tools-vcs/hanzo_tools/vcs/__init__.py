"""Version control tools for Hanzo AI (HIP-0300).

Tools:
- vcs: Unified version control tool (HIP-0300)
  - status: Working tree status
  - diff: Show differences (unified patch format)
  - apply: Apply patch
  - commit: Create commit
  - branch: Branch operations (list, create, delete)
  - checkout: Switch branches
  - log: Commit history

Outputs diffs in unified patch format for use with fs.apply_patch.

Install:
    pip install hanzo-tools-vcs

Usage:
    from hanzo_tools.vcs import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access the unified tool
    from hanzo_tools.vcs import VcsTool
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .vcs_tool import VcsTool, vcs_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [VcsTool]

__all__ = [
    "VcsTool",
    "vcs_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register vcs tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional options (cwd, etc.)

    Returns:
        List of registered tool instances
    """
    cwd = kwargs.get("cwd")
    tool = VcsTool(cwd=cwd)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
