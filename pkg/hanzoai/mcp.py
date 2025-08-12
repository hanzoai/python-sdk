"""Hanzo AI MCP (Model Context Protocol) module.

This module provides access to the hanzo-mcp SDK for building
MCP servers and clients with extensive tool support.
"""

try:
    # Try to import hanzo-mcp if installed
    from hanzo_mcp import (
        # Base classes
        BaseTool,
        ToolRegistry,
        # Server creation
        HanzoMCPServer,
        # Permissions
        PermissionManager,
        # Version
        __version__ as mcp_version,
        create_server,
        get_git_tools,
        get_agent_tools,
        get_shell_tools,
        get_memory_tools,
        get_search_tools,
        get_jupyter_tools,
        # Tool registration
        register_all_tools,
        # Tool categories
        get_filesystem_tools,
        register_all_prompts,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    # Provide a helpful error message
    def _mcp_not_installed(*args, **kwargs):
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    # Create placeholder classes/functions
    HanzoMCPServer = create_server = _mcp_not_installed
    register_all_tools = register_all_prompts = _mcp_not_installed
    get_filesystem_tools = get_shell_tools = get_agent_tools = _mcp_not_installed
    get_search_tools = get_jupyter_tools = get_git_tools = _mcp_not_installed
    get_memory_tools = _mcp_not_installed
    BaseTool = ToolRegistry = _mcp_not_installed
    PermissionManager = _mcp_not_installed
    mcp_version = "not installed"


def create_mcp_server(name: str = "hanzo-mcp", allowed_paths: list = None, **kwargs):
    """Create a new MCP server.

    Args:
        name: Name of the server
        allowed_paths: List of allowed file paths
        **kwargs: Additional server options

    Returns:
        HanzoMCPServer instance
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    return create_server(name=name, allowed_paths=allowed_paths, **kwargs)


def run_mcp_server(name: str = "hanzo-mcp", transport: str = "stdio", **kwargs):
    """Run an MCP server.

    Args:
        name: Name of the server
        transport: Transport protocol ("stdio" or "sse")
        **kwargs: Additional server options
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
        )

    server = create_server(name=name, **kwargs)
    server.run(transport=transport)


class MCPClient:
    """MCP client for connecting to MCP servers."""

    def __init__(self, server_command: list[str] = None):
        """Initialize MCP client.

        Args:
            server_command: Command to start the server (e.g., ["python", "-m", "hanzo_mcp"])
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "hanzo-mcp is not installed. Install it with: pip install hanzo-mcp"
            )

        self.server_command = server_command or ["python", "-m", "hanzo_mcp"]
        self._client = None

    async def connect(self):
        """Connect to the MCP server."""
        # This would use the MCP client SDK when available
        raise NotImplementedError("MCP client SDK integration pending")

    async def call_tool(self, tool_name: str, **kwargs):
        """Call a tool on the server.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        if not self._client:
            await self.connect()

        # This would use the MCP client SDK when available
        raise NotImplementedError("MCP client SDK integration pending")

    async def disconnect(self):
        """Disconnect from the server."""
        if self._client:
            # Cleanup would go here
            self._client = None


__all__ = [
    # Server
    "HanzoMCPServer",
    "create_server",
    "create_mcp_server",
    "run_mcp_server",
    # Tools
    "register_all_tools",
    "register_all_prompts",
    "get_filesystem_tools",
    "get_shell_tools",
    "get_agent_tools",
    "get_search_tools",
    "get_jupyter_tools",
    "get_git_tools",
    "get_memory_tools",
    # Base classes
    "BaseTool",
    "ToolRegistry",
    # Permissions
    "PermissionManager",
    # Client
    "MCPClient",
    # Status
    "MCP_AVAILABLE",
    "mcp_version",
]
