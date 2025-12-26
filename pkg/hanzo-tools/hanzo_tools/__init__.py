"""Hanzo Tools - Modular tool packages for AI agents.

Installation:
    pip install hanzo-tools          # Core only
    pip install hanzo-tools[core]    # filesystem, shell, todo
    pip install hanzo-tools[dev]     # core + editor, lsp, refactor
    pip install hanzo-tools[ai]      # llm, agent, memory
    pip install hanzo-tools[all]     # Everything

Individual packages:
    pip install hanzo-tools-filesystem
    pip install hanzo-tools-shell
    pip install hanzo-tools-browser
    pip install hanzo-tools-llm
    pip install hanzo-tools-database
    pip install hanzo-tools-memory
    pip install hanzo-tools-agent
    pip install hanzo-tools-editor
    pip install hanzo-tools-jupyter
    pip install hanzo-tools-lsp
    pip install hanzo-tools-refactor
    pip install hanzo-tools-vector
    pip install hanzo-tools-todo

Usage:
    from hanzo_tools.filesystem import register_tools as register_fs
    from hanzo_tools.shell import register_tools as register_shell

    # Register with MCP server
    register_fs(mcp_server, permission_manager)
    register_shell(mcp_server)
"""

__version__ = "0.1.0"

# Namespace package
__path__ = __import__("pkgutil").extend_path(__path__, __name__)


def discover_tools():
    """Discover all installed tool packages.

    Uses entry points to find hanzo.tools plugins.

    Returns:
        Dict of package_name -> tools list
    """
    import importlib.metadata

    tools = {}

    try:
        eps = importlib.metadata.entry_points(group="hanzo.tools")
        for ep in eps:
            try:
                module = ep.load()
                if hasattr(module, "TOOLS"):
                    tools[ep.name] = module.TOOLS
            except Exception:
                pass
    except Exception:
        pass

    return tools


def register_all(mcp_server, permission_manager=None, enabled_tools=None):
    """Register all discovered tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
        permission_manager: Optional permission manager
        enabled_tools: Dict of tool_name -> enabled state

    Returns:
        List of registered tool instances
    """
    import importlib.metadata

    registered = []
    enabled = enabled_tools or {}

    try:
        eps = importlib.metadata.entry_points(group="hanzo.tools")
        for ep in eps:
            # Check if package is enabled
            if not enabled.get(ep.name, True):
                continue

            try:
                module_parent = ep.value.rsplit(":", 1)[0]
                module = __import__(module_parent, fromlist=["register_tools"])

                if hasattr(module, "register_tools"):
                    try:
                        tools = module.register_tools(
                            mcp_server,
                            permission_manager=permission_manager,
                            enabled_tools=enabled,
                        )
                    except TypeError:
                        # Some tools don't need permission_manager
                        tools = module.register_tools(mcp_server, enabled_tools=enabled)

                    if tools:
                        registered.extend(tools)
            except Exception as e:
                print(f"Failed to register {ep.name}: {e}")
    except Exception:
        pass

    return registered
