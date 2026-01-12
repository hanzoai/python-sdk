"""Shell tools package for Hanzo AI.

Minimal, orthogonal shell execution with uvloop for high performance.

SHELL DETECTION:
By default, only the user's active shell is exposed to MCP. This avoids
cluttering the tool list with shells the user doesn't use.

Detection order:
1. HANZO_MCP_SHELL env var (e.g., "zsh", "bash", "fish")
2. HANZO_MCP_FORCE_SHELL env var (e.g., "/opt/homebrew/bin/zsh")
3. --shell CLI flag (e.g., --shell=/path/to/fish)
4. Invoking shell (the shell that launched this process)
5. Login shell (from passwd/Directory Services)
6. $SHELL environment variable

On macOS with Homebrew, this will prefer /opt/homebrew/bin/zsh over /bin/zsh.
If detection fails, falls back to 'shell' tool (smart auto-detect).

Core tools:
- <detected>: Your active shell (zsh, bash, fish, or dash)
- ps: Process management (list, kill, logs)

HTTP/Data tools:
- curl: HTTP client without shell escaping issues
- jq: JSON processor without shell escaping issues
- wget: File/site downloads with mirroring support

Convenience tools:
- npx: Node package execution with auto-backgrounding
- uvx: Python package execution with auto-backgrounding
- open: Open files/URLs in system apps

Auto-backgrounding: Commands exceeding timeout automatically background.
Configure via: export HANZO_AUTO_BACKGROUND_TIMEOUT=30  (default: 30s)
              export HANZO_AUTO_BACKGROUND_TIMEOUT=0   (disabled)
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
from hanzo_tools.shell.shell_tools import (
    ZshTool, BashTool, FishTool, DashTool, KshTool, TcshTool, CshTool, ShellTool,
    zsh_tool, bash_tool, fish_tool, dash_tool, ksh_tool, tcsh_tool, csh_tool, shell_tool
)

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

# Shell detection
from hanzo_tools.shell.shell_detect import (
    ShellInfo,
    detect_shells,
    get_active_shell,
    get_cached_active_shell,
    clear_shell_cache,
    get_shell_tool_class,
    resolve_shell_path,
    SUPPORTED_SHELLS,
)


def _get_detected_shell_tools() -> list:
    """
    Get shell tools list with only the detected active shell.

    This reduces tool clutter by only exposing the user's configured shell.
    Override with:
    - HANZO_MCP_SHELL=bash (shell name)
    - HANZO_MCP_FORCE_SHELL=/path/to/shell (full path)
    - HANZO_MCP_ALL_SHELLS=1 (expose all shells)
    """
    import os

    # Allow exposing all shells via env var (for debugging/testing)
    if os.environ.get("HANZO_MCP_ALL_SHELLS", "").lower() in ("1", "true", "yes"):
        return [ZshTool, BashTool, FishTool, DashTool, KshTool, TcshTool, CshTool, PsTool, NpxTool, UvxTool, OpenTool, CurlTool, JqTool, WgetTool]

    # Detect active shell
    shell_name, shell_path = get_cached_active_shell()

    # Get the appropriate shell tool class
    shell_tool_class = get_shell_tool_class(shell_name)

    # Base tools (always included) - no cmd, just the detected shell
    tools = [PsTool, NpxTool, UvxTool, OpenTool, CurlTool, JqTool, WgetTool]

    # Add detected shell tool, or fall back to ShellTool (smart auto-detect)
    if shell_tool_class:
        tools.insert(0, shell_tool_class)  # Put detected shell first
    else:
        tools.insert(0, ShellTool)  # Fallback to smart shell

    return tools


# Tools list for entry point discovery
# Only the detected shell is included (not all 4 shell variants)
# Override with HANZO_MCP_ALL_SHELLS=1 to expose all shells
TOOLS = _get_detected_shell_tools()

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
    # Shell detection
    "ShellInfo",
    "detect_shells",
    "get_active_shell",
    "get_cached_active_shell",
    "clear_shell_cache",
    "get_shell_tool_class",
    "resolve_shell_path",
    "SUPPORTED_SHELLS",
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
    "KshTool",
    "ksh_tool",
    "TcshTool",
    "tcsh_tool",
    "CshTool",
    "csh_tool",
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
    shell_override: str | None = None,
) -> list[BaseTool]:
    """Create instances of shell tools.

    Only the user's detected/configured shell is included to reduce tool clutter.

    Args:
        permission_manager: Permission manager for access control
        all_tools: Dict of all registered tools (for tool invocations)
        shell_override: Override shell (name like "zsh" or path like "/path/to/fish")

    Returns:
        List of shell tool instances
    """
    import os

    # Set permission manager for convenience tools
    npx_tool.permission_manager = permission_manager
    uvx_tool.permission_manager = permission_manager

    # Base tools list (no cmd - just the detected shell and utilities)
    tools = [
        ps_tool,   # Process management
        npx_tool,  # Node packages
        uvx_tool,  # Python packages
        open_tool, # Open files/URLs
    ]

    # Check for all-shells mode
    if os.environ.get("HANZO_MCP_ALL_SHELLS", "").lower() in ("1", "true", "yes"):
        tools.insert(0, ZshTool(tools=all_tools or {}))
        tools.insert(1, BashTool(tools=all_tools or {}))
        tools.insert(2, FishTool(tools=all_tools or {}))
        tools.insert(3, DashTool(tools=all_tools or {}))
        tools.insert(4, KshTool(tools=all_tools or {}))
        tools.insert(5, TcshTool(tools=all_tools or {}))
        tools.insert(6, CshTool(tools=all_tools or {}))
        return tools

    # Determine which shell to expose
    if shell_override:
        # Handle path override (e.g., --shell=/opt/homebrew/bin/fish)
        if "/" in shell_override:
            shell_name = os.path.basename(shell_override)
            os.environ["HANZO_MCP_FORCE_SHELL"] = shell_override
        else:
            shell_name = shell_override.lower()
    else:
        shell_name, _ = get_cached_active_shell()

    # Create and add detected shell tool, or fall back to ShellTool
    shell_tool_class = get_shell_tool_class(shell_name)
    if shell_tool_class:
        shell_instance = shell_tool_class(tools=all_tools or {})
        tools.insert(0, shell_instance)  # Put detected shell first
    else:
        tools.insert(0, ShellTool(tools=all_tools or {}))  # Fallback to smart shell

    return tools


def register_shell_tools(
    mcp_server: FastMCP,
    permission_manager: PermissionManager,
    all_tools: dict[str, BaseTool] | None = None,
    shell_override: str | None = None,
) -> list[BaseTool]:
    """Register shell tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        all_tools: Dict of all registered tools (for cmd tool invocations)
        shell_override: Override shell (name like "zsh" or path like "/path/to/fish")

    Returns:
        List of registered tools
    """
    tools = get_shell_tools(permission_manager, all_tools, shell_override)
    ToolRegistry.register_tools(mcp_server, tools)
    return tools


def register_tools(mcp_server: FastMCP, **kwargs) -> list[BaseTool]:
    """Register all shell tools with the MCP server.

    This is the standard entry point called by the tool discovery system.

    Supports:
        - shell_override: Override detected shell (name or path)
        - permission_manager: Permission manager instance
        - all_tools: Dict of all registered tools
    """
    from hanzo_tools.core import PermissionManager

    permission_manager = kwargs.get("permission_manager") or PermissionManager()
    all_tools = kwargs.get("all_tools")
    shell_override = kwargs.get("shell_override") or kwargs.get("shell")
    return register_shell_tools(mcp_server, permission_manager, all_tools, shell_override)
