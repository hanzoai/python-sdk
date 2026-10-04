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
- repo: Repositories on Hanzo git linked to GitHub (list, sync now)

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

from .git_tool import GitTool, git_tool
from .repo_tool import RepoTool

# Backward compat
VcsTool = GitTool
vcs_tool = git_tool

# Export list for tool discovery - HIP-0300 unified tools
TOOLS = [GitTool, RepoTool]

__all__ = [
    "GitTool",
    "git_tool",
    "RepoTool",
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
    tools = [VcsTool(cwd=kwargs.get("cwd")), RepoTool()]
    for tool in tools:
        ToolRegistry.register_tool(mcp_server, tool)
    return tools
