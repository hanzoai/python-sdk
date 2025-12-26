"""Entry-point based tool loader for hanzo-mcp.

Discovers and loads tools from installed hanzo-tools-* packages using
Python entry points. This enables dynamic tool loading without code duplication.

The entry point group is "hanzo.tools" and each package exports:
    [project.entry-points."hanzo.tools"]
    package_name = "hanzo_tools.package:TOOLS"

Where TOOLS is a list of BaseTool subclasses.
"""

from __future__ import annotations

import sys
import logging
from typing import TYPE_CHECKING, Any
from importlib.metadata import entry_points

if TYPE_CHECKING:
    from mcp.server import FastMCP
    from hanzo_tools.core import BaseTool, PermissionManager

logger = logging.getLogger(__name__)

# Entry point group name
TOOLS_ENTRY_POINT_GROUP = "hanzo.tools"

# Package to tool prefix mapping (for enable/disable)
PACKAGE_TOOL_PREFIXES: dict[str, list[str]] = {
    "filesystem": ["read", "write", "edit", "tree", "ast", "search", "find"],
    "shell": ["dag", "ps", "zsh", "shell", "npx", "uvx", "open", "curl", "jq", "wget"],
    "browser": ["browser"],
    "memory": ["memory"],  # Unified memory tool
    "todo": ["todo"],
    "reasoning": ["think", "critic"],
    "lsp": ["lsp"],
    "refactor": ["refactor"],
    "database": ["sql", "graph"],  # Consolidated database tools
    "agent": ["agent", "iching", "review"],  # Consolidated agent tools (critic is from reasoning)
    "jupyter": ["jupyter"],
    "editor": ["neovim_edit", "neovim_command", "neovim_session"],
    "llm": ["llm", "consensus"],  # Removed llm_manage
    "vector": ["index", "vector_index", "vector_search"],
    "config": ["config", "mode"],
    "mcp_tools": ["mcp"],  # Consolidated MCP tool
    "computer": ["computer"],
}


class EntryPointToolLoader:
    """Loads tools from hanzo-tools-* packages via entry points.

    This loader discovers installed tool packages and dynamically loads
    and registers their tools with the MCP server.
    """

    def __init__(self, permission_manager: "PermissionManager" | None = None):
        """Initialize the loader.

        Args:
            permission_manager: Optional permission manager for file tools
        """
        self.permission_manager = permission_manager
        self._discovered_packages: dict[str, Any] = {}
        self._loaded_tools: dict[str, "BaseTool"] = {}

    def _get_tool_name(self, tool_class: type) -> str:
        """Extract tool name from class, handling @property decorators.

        When 'name' is defined as a @property, we need to instantiate
        the class to get the actual value.
        """
        # Check if name is a property in the class hierarchy
        for klass in tool_class.__mro__:
            if "name" in getattr(klass, "__dict__", {}):
                attr = klass.__dict__["name"]
                if isinstance(attr, property):
                    # Need to instantiate to get property value
                    try:
                        instance = tool_class()
                        name = getattr(instance, "name", None)
                        if isinstance(name, str):
                            return name
                    except Exception:
                        pass
                    # Fall back to class name
                    return tool_class.__name__.lower().replace("tool", "")
                break

        # Try class-level attribute
        name = getattr(tool_class, "name", None)
        if isinstance(name, str):
            return name

        # Fall back to class name
        return tool_class.__name__.lower().replace("tool", "")

    def discover_packages(self) -> dict[str, list[str]]:
        """Discover installed hanzo-tools-* packages.

        Returns:
            Dict mapping package name to list of tool names
        """
        discovered = {}

        # Get entry points for hanzo.tools group
        try:
            if sys.version_info >= (3, 10):
                eps = entry_points(group=TOOLS_ENTRY_POINT_GROUP)
            else:
                # Python 3.9 compatibility
                eps = entry_points().get(TOOLS_ENTRY_POINT_GROUP, [])

            for ep in eps:
                try:
                    # Load the TOOLS list from the entry point
                    tools_list = ep.load()

                    if isinstance(tools_list, list):
                        tool_names = []
                        for tool_class in tools_list:
                            name = self._get_tool_name(tool_class)
                            tool_names.append(name)

                        discovered[ep.name] = tool_names
                        self._discovered_packages[ep.name] = tools_list
                        logger.debug(f"Discovered package '{ep.name}' with tools: {tool_names}")

                except Exception as e:
                    logger.warning(f"Failed to load entry point '{ep.name}': {e}")

        except Exception as e:
            logger.error(f"Failed to discover entry points: {e}")

        return discovered

    def load_package(
        self,
        package_name: str,
        mcp_server: "FastMCP",
        enabled_tools: dict[str, bool] | None = None,
        **kwargs: Any,
    ) -> list["BaseTool"]:
        """Load tools from a specific package.

        Args:
            package_name: Name of the package (e.g., "filesystem", "shell")
            mcp_server: The FastMCP server to register tools with
            enabled_tools: Dict of tool_name -> enabled state
            **kwargs: Additional arguments passed to tool registration

        Returns:
            List of registered BaseTool instances
        """
        if package_name not in self._discovered_packages:
            logger.warning(f"Package '{package_name}' not discovered")
            return []

        tools_list = self._discovered_packages[package_name]
        registered = []
        enabled_tools = enabled_tools or {}

        for tool_class in tools_list:
            tool_name = self._get_tool_name(tool_class)

            # Check if tool is enabled
            if not enabled_tools.get(tool_name, True):
                logger.debug(f"Skipping disabled tool: {tool_name}")
                continue

            try:
                # Try different instantiation patterns
                if self.permission_manager and hasattr(tool_class, "__init__"):
                    # Check if tool accepts permission_manager
                    import inspect

                    sig = inspect.signature(tool_class.__init__)
                    params = list(sig.parameters.keys())

                    if "permission_manager" in params:
                        tool = tool_class(permission_manager=self.permission_manager)
                    else:
                        tool = tool_class()
                else:
                    tool = tool_class()

                # Register with MCP server
                if hasattr(tool, "register"):
                    tool.register(mcp_server)

                self._loaded_tools[tool_name] = tool
                registered.append(tool)
                logger.debug(f"Registered tool: {tool_name}")

            except Exception as e:
                logger.warning(f"Failed to register tool '{tool_name}': {e}")

        return registered

    def load_all(
        self,
        mcp_server: "FastMCP",
        enabled_tools: dict[str, bool] | None = None,
        enabled_packages: dict[str, bool] | None = None,
        **kwargs: Any,
    ) -> dict[str, "BaseTool"]:
        """Load all discovered tools.

        Args:
            mcp_server: The FastMCP server to register tools with
            enabled_tools: Dict of tool_name -> enabled state
            enabled_packages: Dict of package_name -> enabled state
            **kwargs: Additional arguments passed to tool registration

        Returns:
            Dict mapping tool name to BaseTool instance
        """
        if not self._discovered_packages:
            self.discover_packages()

        enabled_tools = enabled_tools or {}
        enabled_packages = enabled_packages or {}

        for package_name in self._discovered_packages:
            # Check if package is enabled
            if not enabled_packages.get(package_name, True):
                logger.debug(f"Skipping disabled package: {package_name}")
                continue

            # Build package-specific enabled_tools
            package_tool_names = PACKAGE_TOOL_PREFIXES.get(package_name, [])
            package_enabled = {name: enabled_tools.get(name, True) for name in package_tool_names}

            self.load_package(
                package_name,
                mcp_server,
                enabled_tools=package_enabled,
                **kwargs,
            )

        return self._loaded_tools

    def get_tool(self, name: str) -> "BaseTool | None":
        """Get a loaded tool by name."""
        return self._loaded_tools.get(name)

    def list_tools(self) -> list[str]:
        """List all loaded tool names."""
        return list(self._loaded_tools.keys())

    def list_packages(self) -> list[str]:
        """List all discovered package names."""
        return list(self._discovered_packages.keys())


def discover_tools() -> dict[str, list[str]]:
    """Discover all available tools from installed packages.

    Returns:
        Dict mapping package name to list of tool names
    """
    loader = EntryPointToolLoader()
    return loader.discover_packages()


def register_tools_from_entrypoints(
    mcp_server: "FastMCP",
    permission_manager: "PermissionManager" | None = None,
    enabled_tools: dict[str, bool] | None = None,
    enabled_packages: dict[str, bool] | None = None,
    **kwargs: Any,
) -> dict[str, "BaseTool"]:
    """Register tools from all discovered hanzo-tools-* packages.

    This is the main entry point for loading tools via entry points.

    Args:
        mcp_server: The FastMCP server to register tools with
        permission_manager: Optional permission manager for file tools
        enabled_tools: Dict of tool_name -> enabled state
        enabled_packages: Dict of package_name -> enabled state
        **kwargs: Additional arguments passed to tool registration

    Returns:
        Dict mapping tool name to BaseTool instance
    """
    loader = EntryPointToolLoader(permission_manager=permission_manager)
    return loader.load_all(
        mcp_server,
        enabled_tools=enabled_tools,
        enabled_packages=enabled_packages,
        **kwargs,
    )
