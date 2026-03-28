"""UI component registry tools for Hanzo AI (HIP-0300).

Local-first: when ~/work/hanzo/ui exists, reads directly from disk.
Falls back to GitHub API for remote registries.

Tools:
- ui: Unified UI component tool
  - list_components: List available components
  - get_component: Get component source code
  - get_demo: Get component demo/example
  - get_metadata: Get component metadata
  - list_blocks: List UI blocks
  - get_block: Get block implementation
  - search: Search components
  - get_structure: Browse repository structure
  - install: Install component via CLI
  - set_framework: Switch active framework
  - get_framework: Show current and available frameworks
  - create_composition: Scaffold from components
  - list_packages: List all local UI packages
  - read_file: Read any file from the UI repo

Frameworks: hanzo (default), shadcn, react, svelte, vue, react-native

Install:
    pip install hanzo-tools-ui

Usage:
    from hanzo_tools.ui import register_tools, TOOLS
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .github_api import (
    FRAMEWORK_CONFIGS,
    FRAMEWORK_NAMES,
    GitHubAPIClient,
)
from .local_client import LocalUIClient
from .ui_tool import UiTool, ui_tool

TOOLS = [UiTool]

__all__ = [
    "UiTool",
    "ui_tool",
    "FRAMEWORK_CONFIGS",
    "FRAMEWORK_NAMES",
    "GitHubAPIClient",
    "LocalUIClient",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register UI tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance

    Returns:
        List of registered tool instances
    """
    tool = UiTool()
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
