"""MCP management tools for Hanzo AI.

Tools:
- mcp: MCP server management
- mcp_add: Add MCP servers
- mcp_remove: Remove MCP servers
- mcp_stats: MCP statistics
- proxy: Dynamic MCP proxy for external servers (platform, github, cloudflare, etc.)

Install:
    pip install hanzo-tools-mcp
"""

import logging

logger = logging.getLogger(__name__)

_tools = []

try:
    from .mcp_tool import MCPTool

    _tools.append(MCPTool)
except ImportError as e:
    logger.debug(f"MCPTool not available: {e}")
    MCPTool = None

try:
    from .mcp_add import McpAddTool

    _tools.append(McpAddTool)
except ImportError as e:
    logger.debug(f"McpAddTool not available: {e}")
    McpAddTool = None

try:
    from .mcp_remove import McpRemoveTool

    _tools.append(McpRemoveTool)
except ImportError as e:
    logger.debug(f"McpRemoveTool not available: {e}")
    McpRemoveTool = None

try:
    from .mcp_stats import McpStatsTool

    _tools.append(McpStatsTool)
except ImportError as e:
    logger.debug(f"McpStatsTool not available: {e}")
    McpStatsTool = None

try:
    from .proxy_tool import ProxyTool

    _tools.append(ProxyTool)
except ImportError as e:
    logger.debug(f"ProxyTool not available: {e}")
    ProxyTool = None

# Proxy utilities for programmatic use
try:
    from .mcp_proxy import (
        BUILTIN_SERVERS,
        ProxiedTool,
        MCPServerConfig,
        MCPProxyRegistry,
        MCPServerConnection,
        call_mcp_tool,
        enable_mcp_server,
    )
except ImportError as e:
    logger.debug(f"MCP proxy utilities not available: {e}")
    MCPProxyRegistry = None
    MCPServerConfig = None
    MCPServerConnection = None
    ProxiedTool = None
    enable_mcp_server = None
    call_mcp_tool = None
    BUILTIN_SERVERS = {}

TOOLS = _tools

__all__ = [
    "TOOLS",
    "MCPTool",
    "McpAddTool",
    "McpRemoveTool",
    "McpStatsTool",
    "ProxyTool",
    # Proxy utilities
    "MCPProxyRegistry",
    "MCPServerConfig",
    "MCPServerConnection",
    "ProxiedTool",
    "enable_mcp_server",
    "call_mcp_tool",
    "BUILTIN_SERVERS",
    "register_tools",
]


def register_tools(mcp_server, enabled_tools: dict[str, bool] | None = None):
    """Register MCP tools with MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []

    for tool_class in TOOLS:
        if tool_class is None:
            continue
        tool_name = getattr(tool_class, "name", tool_class.__name__.lower())
        if enabled.get(tool_name, True):
            try:
                tool = tool_class()
                ToolRegistry.register_tool(mcp_server, tool)
                registered.append(tool)
            except Exception as e:
                logger.warning(f"Failed to register {tool_name}: {e}")

    return registered
