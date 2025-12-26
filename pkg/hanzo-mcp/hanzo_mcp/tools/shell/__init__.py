"""Shell tools package for Hanzo AI.

Minimal, orthogonal shell execution.

Core tools:
- dag: Execute commands/tools with DAG flow control (serial, parallel, graph)
- ps: Process management (list, kill, logs)

Convenience tools (optional):
- npx: Node package execution with auto-backgrounding
- uvx: Python package execution with auto-backgrounding
- open: Open files/URLs in system apps
"""

from mcp.server import FastMCP

# Convenience tools
from hanzo_mcp.tools.shell.open import open_tool
from hanzo_mcp.tools.common.base import BaseTool, ToolRegistry
from hanzo_mcp.tools.shell.ps_tool import PsTool, ps_tool

# Core tools
from hanzo_mcp.tools.shell.dag_tool import DagTool, create_dag_tool
from hanzo_mcp.tools.shell.npx_tool import npx_tool
from hanzo_mcp.tools.shell.uvx_tool import uvx_tool
from hanzo_mcp.tools.shell.zsh_tool import ZshTool, zsh_tool
from hanzo_mcp.tools.common.permissions import PermissionManager

__all__ = [
    "DagTool",
    "PsTool",
    "ZshTool",
    "create_dag_tool",
    "ps_tool",
    "zsh_tool",
    "get_shell_tools",
    "register_shell_tools",
]


def get_shell_tools(
    permission_manager: PermissionManager,
    all_tools: dict[str, BaseTool] | None = None,
) -> list[BaseTool]:
    """Create instances of shell tools.

    Args:
        permission_manager: Permission manager for access control
        all_tools: Dict of all registered tools (for dag tool invocations)

    Returns:
        List of shell tool instances
    """
    # Create dag tool with access to other tools
    dag = create_dag_tool(tools=all_tools or {})

    # Set permission manager for convenience tools
    npx_tool.permission_manager = permission_manager
    uvx_tool.permission_manager = permission_manager

    return [
        dag,  # DAG execution for complex workflows
        zsh_tool,  # Simple single-command zsh (with auto-backgrounding)
        ps_tool,  # Process management
        npx_tool,  # Node packages
        uvx_tool,  # Python packages
        open_tool,  # Open files/URLs
    ]


def register_shell_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    all_tools: dict[str, BaseTool] | None = None,
) -> list[BaseTool]:
    """Register shell tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        all_tools: Dict of all registered tools (for dag tool invocations)

    Returns:
        List of registered tools
    """
    tools = get_shell_tools(permission_manager, all_tools)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools
