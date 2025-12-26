"""Tools package for Hanzo AI.

This package provides dynamic tool loading from hanzo-tools-* packages via entry points.
Tools are discovered and loaded at runtime, enabling:
- Install/uninstall tool packages independently
- Enable/disable individual tools
- Hot-reload without server restart

IMPORTANT: All tool implementations live in hanzo-tools-* packages.
This module only handles discovery and registration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server import FastMCP
    from hanzo_tools.core import BaseTool, PermissionManager

logger = logging.getLogger(__name__)


def register_all_tools(
    mcp_server: "FastMCP",
    permission_manager: "PermissionManager",
    agent_model: str | None = None,
    agent_max_tokens: int | None = None,
    agent_api_key: str | None = None,
    agent_base_url: str | None = None,
    agent_max_iterations: int = 10,
    agent_max_tool_uses: int = 30,
    enable_agent_tool: bool = False,
    disable_write_tools: bool = False,
    disable_search_tools: bool = False,
    enabled_tools: dict[str, bool] | None = None,
    vector_config: dict | None = None,
    use_mode: bool = True,
    force_mode: str | None = None,
) -> list["BaseTool"]:
    """Register all Hanzo tools with the MCP server.

    Tools are discovered from installed hanzo-tools-* packages via entry points.

    Args:
        mcp_server: The FastMCP server instance
        permission_manager: Permission manager for access control
        agent_model: Optional model name for agent tool in LiteLLM format
        agent_max_tokens: Optional maximum tokens for agent responses
        agent_api_key: Optional API key for the LLM provider
        agent_base_url: Optional base URL for the LLM provider API endpoint
        agent_max_iterations: Maximum number of iterations for agent (default: 10)
        agent_max_tool_uses: Maximum number of total tool uses for agent (default: 30)
        enable_agent_tool: Whether to enable the agent tool (default: False)
        disable_write_tools: Whether to disable write tools (default: False)
        disable_search_tools: Whether to disable search tools (default: False)
        enabled_tools: Dictionary of individual tool enable/disable states (default: None)
        vector_config: Vector store configuration (default: None)
        use_mode: Whether to use mode system for tool configuration (default: True)
        force_mode: Force a specific mode to be active (default: None)

    Returns:
        List of registered BaseTool instances
    """
    from hanzo_mcp.tools.common.entrypoint_loader import (
        PACKAGE_TOOL_PREFIXES,
        EntryPointToolLoader,
    )

    all_tools: dict[str, "BaseTool"] = {}
    tool_config = enabled_tools or {}

    def is_tool_enabled(tool_name: str, category_enabled: bool = True) -> bool:
        """Check if a specific tool should be enabled."""
        if tool_name in tool_config:
            return tool_config[tool_name]
        return category_enabled

    # Apply mode configuration if enabled
    if use_mode:
        try:
            from hanzo_mcp.tools.common.mode import activate_mode_from_env
            from hanzo_mcp.tools.common.mode_loader import ModeLoader

            activate_mode_from_env()
            tool_config = ModeLoader.get_enabled_tools_from_mode(
                base_enabled_tools=enabled_tools, force_mode=force_mode
            )
            ModeLoader.apply_environment_from_mode()
        except ImportError:
            logger.debug("Mode system not available")

    # Build enabled state for each tool based on configuration
    resolved_enabled_tools: dict[str, bool] = {}

    # Filesystem tools
    for tool in PACKAGE_TOOL_PREFIXES.get("filesystem", []):
        if tool in ["write", "edit", "multi_edit"]:
            resolved_enabled_tools[tool] = is_tool_enabled(tool, not disable_write_tools)
        elif tool in ["ast", "search"]:
            resolved_enabled_tools[tool] = is_tool_enabled(tool, not disable_search_tools)
        else:
            resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # Shell tools - always enabled by default
    for tool in PACKAGE_TOOL_PREFIXES.get("shell", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # Browser tool
    resolved_enabled_tools["browser"] = is_tool_enabled("browser", True)

    # Memory tools
    for tool in PACKAGE_TOOL_PREFIXES.get("memory", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # Todo tools
    resolved_enabled_tools["todo"] = is_tool_enabled("todo", True)

    # Reasoning tools
    resolved_enabled_tools["think"] = is_tool_enabled("think", True)
    resolved_enabled_tools["critic"] = is_tool_enabled("critic", True)

    # LSP tool
    resolved_enabled_tools["lsp"] = is_tool_enabled("lsp", True)

    # Refactor tool
    resolved_enabled_tools["refactor"] = is_tool_enabled("refactor", True)

    # Database tools
    for tool in PACKAGE_TOOL_PREFIXES.get("database", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # Agent tools
    resolved_enabled_tools["agent"] = enable_agent_tool or is_tool_enabled("agent", False)
    resolved_enabled_tools["swarm"] = is_tool_enabled("swarm", False)
    for tool in ["claude", "codex", "gemini", "grok", "code_auth"]:
        resolved_enabled_tools[tool] = is_tool_enabled(tool, enable_agent_tool)

    # Editor tools
    for tool in PACKAGE_TOOL_PREFIXES.get("editor", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # LLM tools
    resolved_enabled_tools["llm"] = is_tool_enabled("llm", True)
    resolved_enabled_tools["consensus"] = is_tool_enabled("consensus", True)

    # Vector tools (usually disabled by default unless config provided)
    vector_enabled = vector_config is not None
    for tool in PACKAGE_TOOL_PREFIXES.get("vector", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, vector_enabled)

    # Config tools
    resolved_enabled_tools["config"] = is_tool_enabled("config", True)
    resolved_enabled_tools["mode"] = is_tool_enabled("mode", True)

    # MCP tools
    resolved_enabled_tools["mcp"] = is_tool_enabled("mcp", True)

    # Jupyter tools
    for tool in PACKAGE_TOOL_PREFIXES.get("jupyter", []):
        resolved_enabled_tools[tool] = is_tool_enabled(tool, True)

    # Create loader and discover packages
    loader = EntryPointToolLoader(permission_manager=permission_manager)
    discovered = loader.discover_packages()

    if discovered:
        logger.info(f"Discovered {len(discovered)} tool packages: {', '.join(discovered.keys())}")

        # Load all discovered tools
        loaded = loader.load_all(
            mcp_server,
            enabled_tools=resolved_enabled_tools,
        )
        all_tools.update(loaded)
        logger.info(f"Loaded {len(loaded)} tools from entry points")
    else:
        logger.warning("No tool packages discovered via entry points")

    # Register system tools that are always available
    _register_system_tools(mcp_server, all_tools)

    return list(all_tools.values())


def _register_system_tools(
    mcp_server: "FastMCP",
    all_tools: dict[str, "BaseTool"],
) -> None:
    """Register built-in system tools that are always available.

    These are core tools that don't come from hanzo-tools-* packages.
    """
    # Version tool
    try:
        from hanzo_mcp.tools.common.version_tool import register_version_tool

        register_version_tool(mcp_server)
    except ImportError:
        logger.debug("Version tool not available")

    # Unified tool command (replaces tool_install, tool_enable, tool_disable, tool_list)
    try:
        from hanzo_mcp.tools.common.tool import register_unified_tool

        unified_tools = register_unified_tool(mcp_server)
        for tool in unified_tools:
            all_tools[tool.name] = tool
        logger.info("Registered unified 'tool' command")
    except ImportError as e:
        logger.debug(f"Unified tool not available: {e}")
        # Fallback to legacy tools if unified tool fails
        try:
            from hanzo_mcp.tools.common.tool_install import register_tool_install

            install_tools = register_tool_install(mcp_server)
            for tool in install_tools:
                all_tools[tool.name] = tool
        except ImportError:
            pass

    # Stats tool
    try:
        from hanzo_mcp.tools.common.stats import StatsTool

        stats_tool = StatsTool()
        stats_tool.register(mcp_server)
        all_tools[stats_tool.name] = stats_tool
    except ImportError:
        logger.debug("Stats tool not available")


# Re-export for backward compatibility
__all__ = ["register_all_tools"]
