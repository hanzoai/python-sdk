"""Shell tools package for Hanzo AI.

Minimal, orthogonal shell execution.

Core tools:
- zsh: Primary shell with full DAG support (serial, parallel, graph)
- ps: Process management (list, kill, logs)
- shell: Smart shell alias (zsh > bash fallback)

HTTP/Data tools:
- curl: HTTP client without shell escaping issues
- jq: JSON processor without shell escaping issues
- wget: File/site downloads with mirroring support

Convenience tools:
- npx: Node package execution with auto-backgrounding
- uvx: Python package execution with auto-backgrounding
- open: Open files/URLs in system apps

Note: 'dag' is now merged into 'zsh'. Use zsh(["cmd1", "cmd2"]) for serial,
zsh([...], parallel=True) for parallel, and full DAG syntax is supported.
DagTool kept for backwards compatibility.
"""

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry, PermissionManager
from hanzo_tools.shell.ps_tool import PsTool, ps_tool

# Core tools
from hanzo_tools.shell.dag_tool import DagTool, create_dag_tool
from hanzo_tools.shell.npx_tool import NpxTool, npx_tool
from hanzo_tools.shell.truncate import truncate_lines, estimate_tokens, truncate_response
from hanzo_tools.shell.uvx_tool import UvxTool, uvx_tool
from hanzo_tools.shell.zsh_tool import ZshTool, ShellTool, BashTool, zsh_tool, shell_tool, bash_tool
from hanzo_tools.shell.shellflow import parse as parse_shellflow, compile as compile_shellflow

# Convenience tools
from hanzo_tools.shell.open_tool import OpenTool, open_tool

# HTTP/Data tools (no shell escaping issues)
from hanzo_tools.shell.curl_tool import CurlTool
from hanzo_tools.shell.jq_tool import JqTool
from hanzo_tools.shell.wget_tool import WgetTool

# Base classes
from hanzo_tools.shell.base_process import (
    BaseBinaryTool,
    BaseScriptTool,
    ProcessManager,
    BaseProcessTool,
    AutoBackgroundExecutor,
)

# Tools list for entry point discovery
# Note: ZshTool now includes full DAG functionality. DagTool kept for backwards compatibility.
# BashTool available for bash-specific scripts.
TOOLS = [ZshTool, BashTool, ShellTool, PsTool, NpxTool, UvxTool, OpenTool, CurlTool, JqTool, WgetTool]

__all__ = [
    # Base classes
    "ProcessManager",
    "AutoBackgroundExecutor",
    "BaseProcessTool",
    "BaseBinaryTool",
    "BaseScriptTool",
    # Utilities
    "truncate_response",
    "truncate_lines",
    "estimate_tokens",
    # Core tools
    "DagTool",
    "create_dag_tool",
    "PsTool",
    "ps_tool",
    "ZshTool",
    "zsh_tool",
    "ShellTool",
    "shell_tool",
    "BashTool",
    "bash_tool",
    # Convenience tools
    "OpenTool",
    "open_tool",
    "NpxTool",
    "npx_tool",
    "UvxTool",
    "uvx_tool",
    # HTTP/Data tools
    "CurlTool",
    "JqTool",
    "WgetTool",
    # Registration
    "TOOLS",
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
        all_tools: Dict of all registered tools (for zsh tool invocations)

    Returns:
        List of shell tool instances
    """
    # Create zsh tool with access to other tools (for DAG tool invocations)
    zsh = ZshTool(tools=all_tools or {})

    # Set permission manager for convenience tools
    npx_tool.permission_manager = permission_manager
    uvx_tool.permission_manager = permission_manager

    return [
        zsh,  # Primary shell with DAG support
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


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all shell tools with the MCP server.

    This is the standard entry point called by the tool discovery system.
    """
    from hanzo_tools.core import PermissionManager

    permission_manager = kwargs.get("permission_manager") or PermissionManager()
    all_tools = kwargs.get("all_tools")
    return register_shell_tools(mcp_server, permission_manager, all_tools)
