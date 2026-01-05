"""Shell tools package for Hanzo AI.

Minimal, orthogonal shell execution with uvloop for high performance.

Core tools:
- cmd: Unified execution graph (DAG) - RECOMMENDED
- zsh: Zsh shell (thin wrapper over cmd)
- bash: Bash shell (thin wrapper over cmd)
- fish: Fish shell (thin wrapper over cmd)
- dash: Dash shell (fast POSIX, Ubuntu's /bin/sh)
- ps: Process management (list, kill, logs)

HTTP/Data tools:
- curl: HTTP client without shell escaping issues
- jq: JSON processor without shell escaping issues
- wget: File/site downloads with mirroring support

Convenience tools:
- npx: Node package execution with auto-backgrounding
- uvx: Python package execution with auto-backgrounding
- open: Open files/URLs in system apps

Use 'cmd' for:
- Simple commands: cmd("ls -la")
- Parallel execution: cmd(["npm install", "cargo build"], parallel=True)
- Mixed DAG: cmd(["mkdir dist", {"parallel": ["cp a dist/", "cp b dist/"]}, "zip out"])
- Tool invocations: cmd([{"tool": "search", "input": {"pattern": "TODO"}}])

Auto-backgrounding: Commands exceeding timeout automatically background.
Configure via: export HANZO_AUTO_BACKGROUND_TIMEOUT=30  (default: 30s)
Use ps --logs <id> to view, ps --kill <id> to stop.

Performance: Uses uvloop on macOS/Linux for 2-4x faster async I/O.
Falls back to standard asyncio on Windows.
"""

# Use hanzo-async for unified async I/O and uvloop configuration
from hanzo_async import configure_loop, using_uvloop

# Auto-configure uvloop on import
configure_loop()
_using_uvloop = using_uvloop()

from mcp.server import FastMCP

from hanzo_tools.core import BaseTool, ToolRegistry, PermissionManager
from hanzo_tools.shell.base_process import AUTO_BACKGROUND_TIMEOUT
from hanzo_tools.shell.jq_tool import JqTool
from hanzo_tools.shell.ps_tool import PsTool, ps_tool

# Core tools
from hanzo_tools.shell.cmd_tool import CmdTool, CmdResult, CmdNode, NodeStatus, create_cmd_tool, cmd_tool
from hanzo_tools.shell.npx_tool import NpxTool, npx_tool
from hanzo_tools.shell.truncate import truncate_lines, estimate_tokens, truncate_response
from hanzo_tools.shell.uvx_tool import UvxTool, uvx_tool
from hanzo_tools.shell.shell_tools import ZshTool, BashTool, FishTool, DashTool, ShellTool, zsh_tool, bash_tool, fish_tool, dash_tool, shell_tool

# HTTP/Data tools (no shell escaping issues)
from hanzo_tools.shell.curl_tool import CurlTool

# Convenience tools
from hanzo_tools.shell.open_tool import OpenTool, open_tool
from hanzo_tools.shell.shellflow import parse as parse_shellflow, compile as compile_shellflow
from hanzo_tools.shell.wget_tool import WgetTool

# Base classes
from hanzo_tools.shell.base_process import (
    BaseBinaryTool,
    BaseScriptTool,
    ProcessManager,
    BaseProcessTool,
    AutoBackgroundExecutor,
    ShellExecutor,
    get_shell_executor,
)

# Backwards compatibility - DagTool is now CmdTool
from hanzo_tools.shell.dag_tool import DagTool, DagResult, DagNode, create_dag_tool

# Tools list for entry point discovery
# - CmdTool: Primary command execution with DAG support
# - ZshTool, BashTool, etc: Specific shell wrappers (thin shims over CmdTool)
# Note: ShellTool removed - too ambiguous, use specific shells (zsh, bash, dash, fish)
TOOLS = [CmdTool, ZshTool, BashTool, FishTool, DashTool, PsTool, NpxTool, UvxTool, OpenTool, CurlTool, JqTool, WgetTool]

__all__ = [
    # uvloop status
    "_using_uvloop",
    # Base classes
    "ProcessManager",
    "AutoBackgroundExecutor",
    "ShellExecutor",
    "get_shell_executor",
    "BaseProcessTool",
    "BaseBinaryTool",
    "BaseScriptTool",
    # Utilities
    "truncate_response",
    "truncate_lines",
    "estimate_tokens",
    # Core tools
    "CmdTool",
    "CmdResult",
    "CmdNode",
    "NodeStatus",
    "cmd_tool",
    "create_cmd_tool",
    "PsTool",
    "ps_tool",
    "ZshTool",
    "zsh_tool",
    "ShellTool",
    "shell_tool",
    "BashTool",
    "bash_tool",
    "FishTool",
    "fish_tool",
    "DashTool",
    "dash_tool",
    # Backwards compatibility
    "DagTool",
    "DagResult",
    "DagNode",
    "create_dag_tool",
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
        all_tools: Dict of all registered tools (for cmd tool invocations)

    Returns:
        List of shell tool instances
    """
    # Create cmd tool with access to other tools (for tool invocations)
    cmd = CmdTool(tools=all_tools or {})

    # Create shell wrappers with access to other tools
    zsh = ZshTool(tools=all_tools or {})
    bash = BashTool(tools=all_tools or {})

    # Set permission manager for convenience tools
    npx_tool.permission_manager = permission_manager
    uvx_tool.permission_manager = permission_manager

    return [
        cmd,  # Primary command execution with DAG support
        zsh,  # Zsh shell wrapper
        bash,  # Bash shell wrapper
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
        all_tools: Dict of all registered tools (for cmd tool invocations)

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
