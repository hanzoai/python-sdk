"""Unified tool management command.

Combines install, uninstall, upgrade, enable, disable, and list into a single tool.
"""

from typing import Any, Unpack, Literal, Optional, Annotated, TypedDict, final, override
from pathlib import Path

from pydantic import Field

# Import async I/O utilities
from hanzo_async import mkdir, read_json, write_json, path_exists
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.common.auto_timeout import auto_timeout

Action = Annotated[
    Literal[
        "install",  # Install a tool package
        "uninstall",  # Remove a tool package
        "upgrade",  # Upgrade package(s)
        "reload",  # Hot-reload a package
        "enable",  # Enable a tool
        "disable",  # Disable a tool
        "list",  # List installed tools
        "status",  # Show tool status
        "self_update",  # Update hanzo-mcp itself
    ],
    Field(description="Action to perform"),
]


class ToolParams(TypedDict, total=False):
    """Parameters for unified tool command."""

    action: str
    name: Optional[str]  # Tool or package name
    source: str  # For install: pypi, git, local
    version: Optional[str]  # Version constraint
    persist: bool  # Persist enable/disable changes
    category: Optional[str]  # Filter list by category
    disabled: bool  # Show only disabled tools
    enabled: bool  # Show only enabled tools


@final
class UnifiedToolTool(BaseTool):
    """Unified tool management.

    Combines package installation, tool enable/disable, and listing
    into a single coherent command.
    """

    # Tool states stored here
    _tool_states: dict = {}
    _config_file = Path.home() / ".hanzo" / "mcp" / "tool_states.json"
    _initialized = False

    def __init__(self):
        """Initialize the tool."""
        # Note: Async initialization happens on first use via _ensure_initialized
        pass

    @classmethod
    async def _ensure_initialized(cls):
        """Ensure states are loaded (async)."""
        if not cls._initialized:
            await cls._load_states_async()
            cls._initialized = True

    @classmethod
    async def _load_states_async(cls):
        """Load tool states from config file (async)."""
        if await path_exists(cls._config_file):
            try:
                cls._tool_states = await read_json(cls._config_file)
            except Exception:
                cls._tool_states = {}
        else:
            cls._tool_states = {}

    @classmethod
    async def _save_states_async(cls):
        """Save tool states to config file (async)."""
        await mkdir(cls._config_file.parent, parents=True, exist_ok=True)
        await write_json(cls._config_file, cls._tool_states)

    @classmethod
    def is_tool_enabled(cls, tool_name: str) -> bool:
        """Check if a tool is enabled (sync, uses cached state)."""
        # Uses cached state - call _ensure_initialized first in async contexts
        return cls._tool_states.get(tool_name, True)

    @property
    @override
    def name(self) -> str:
        return "tool"

    @property
    @override
    def description(self) -> str:
        return """Unified tool management command.

Actions:
- list: List all tools and their status
- enable: Enable a disabled tool
- disable: Disable a tool
- status: Check status of a specific tool
- install: Install a tool package from PyPI/git
- uninstall: Remove a tool package
- upgrade: Upgrade package(s) to latest
- reload: Hot-reload a package without restart
- self_update: Update hanzo-mcp itself

Examples:
  tool list                              # List all tools
  tool list --category=shell             # List shell tools
  tool list --disabled                   # List disabled tools
  tool enable --name=browser             # Enable browser tool
  tool disable --name=grep               # Disable grep
  tool status --name=llm                 # Check llm status
  tool install --name=hanzo-tools-data   # Install package
  tool upgrade                           # Upgrade all
  tool self_update                       # Update hanzo-mcp
"""

    @override
    @auto_timeout("tool")
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[ToolParams],
    ) -> str:
        """Execute tool management action."""
        # Ensure async initialization
        await self._ensure_initialized()

        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        action = params.get("action", "list")
        name = params.get("name")
        source = params.get("source", "pypi")
        version = params.get("version")
        persist = params.get("persist", True)
        category = params.get("category")
        show_disabled = params.get("disabled", False)
        show_enabled = params.get("enabled", False)

        # Route to appropriate handler
        if action == "list":
            return await self._handle_list(category, show_disabled, show_enabled)
        elif action == "status":
            return await self._handle_status(name)
        elif action == "enable":
            return await self._handle_enable(name, persist)
        elif action == "disable":
            return await self._handle_disable(name, persist)
        elif action == "install":
            return await self._handle_install(name, source, version, tool_ctx)
        elif action == "uninstall":
            return await self._handle_uninstall(name, tool_ctx)
        elif action == "upgrade":
            return await self._handle_upgrade(name, tool_ctx)
        elif action == "reload":
            return await self._handle_reload(name, tool_ctx)
        elif action == "self_update":
            return await self._handle_self_update(tool_ctx)
        else:
            return f"Unknown action: {action}. Use: list, enable, disable, status, install, uninstall, upgrade, reload, self_update"

    async def _handle_list(
        self,
        category: Optional[str],
        show_disabled: bool,
        show_enabled: bool,
    ) -> str:
        """List all tools."""
        from hanzo_mcp.config.tool_config import DynamicToolRegistry

        DynamicToolRegistry.initialize()
        all_tools = DynamicToolRegistry.list_all()

        lines = []
        if show_disabled:
            lines.append("=== Disabled Tools ===\n")
        elif show_enabled:
            lines.append("=== Enabled Tools ===\n")
        else:
            lines.append("=== All Tools ===\n")

        # Group by category
        by_category: dict = {}
        for tool_name, config in all_tools.items():
            cat = config.category.value if config.category else "other"
            if category and cat != category:
                continue
            if cat not in by_category:
                by_category[cat] = []

            is_enabled = self.is_tool_enabled(tool_name)
            if show_disabled and is_enabled:
                continue
            if show_enabled and not is_enabled:
                continue

            by_category[cat].append((tool_name, config, is_enabled))

        # Output by category
        for cat, tools in sorted(by_category.items()):
            if not tools:
                continue
            lines.append(f"[{cat}]")
            for tool_name, config, is_enabled in sorted(tools, key=lambda x: x[0]):
                status = "✓" if is_enabled else "○"
                desc = config.description[:50] + "..." if len(config.description) > 50 else config.description
                lines.append(f"  {status} {tool_name}: {desc}")
            lines.append("")

        # Summary
        total = sum(len(t) for t in by_category.values())
        enabled = sum(1 for tools in by_category.values() for _, _, e in tools if e)
        lines.append(f"Total: {total} | Enabled: {enabled} | Disabled: {total - enabled}")

        return "\n".join(lines)

    async def _handle_status(self, name: Optional[str]) -> str:
        """Check status of a specific tool."""
        if not name:
            return "Error: name required for status action"

        from hanzo_mcp.config.tool_config import DynamicToolRegistry

        DynamicToolRegistry.initialize()
        config = DynamicToolRegistry.get(name)

        if not config:
            return f"Tool '{name}' not found"

        is_enabled = self.is_tool_enabled(name)
        status = "enabled" if is_enabled else "disabled"

        return f"""Tool: {name}
Status: {status}
Category: {config.category.value if config.category else "unknown"}
Package: {config.package or "built-in"}
Description: {config.description}"""

    async def _handle_enable(self, name: Optional[str], persist: bool) -> str:
        """Enable a tool."""
        if not name:
            return "Error: name required for enable action"

        if self.is_tool_enabled(name):
            return f"Tool '{name}' is already enabled"

        self._tool_states[name] = True
        if persist:
            await self._save_states_async()

        return f"✓ Enabled tool '{name}'" + ("" if persist else " (temporary)")

    async def _handle_disable(self, name: Optional[str], persist: bool) -> str:
        """Disable a tool."""
        if not name:
            return "Error: name required for disable action"

        # Prevent disabling critical tools
        critical = {"tool", "version", "stats", "config", "mode", "llm", "consensus"}
        if name in critical:
            return f"Error: Cannot disable critical tool '{name}'"

        if not self.is_tool_enabled(name):
            return f"Tool '{name}' is already disabled"

        self._tool_states[name] = False
        if persist:
            await self._save_states_async()

        return f"○ Disabled tool '{name}'" + ("" if persist else " (temporary)")

    async def _handle_install(
        self,
        name: Optional[str],
        source: str,
        version: Optional[str],
        tool_ctx: Any,
    ) -> str:
        """Install a tool package."""
        if not name:
            return "Error: package name required for install"

        from hanzo_mcp.tools.common.tool_registry import get_registry

        await tool_ctx.info(f"Installing {name} from {source}...")
        registry = await get_registry()
        result = await registry.install(package=name, source=source, version=version)

        if result["success"]:
            tools = result.get("tools", [])
            return (
                f"✓ Installed {name} v{result.get('version', 'latest')}\n"
                f"Tools: {', '.join(tools) if tools else 'none detected'}"
            )
        return f"✗ Failed: {result.get('error', 'unknown error')}"

    async def _handle_uninstall(self, name: Optional[str], tool_ctx: Any) -> str:
        """Uninstall a tool package."""
        if not name:
            return "Error: package name required for uninstall"

        from hanzo_mcp.tools.common.tool_registry import get_registry

        await tool_ctx.info(f"Uninstalling {name}...")
        registry = await get_registry()
        result = await registry.uninstall(name)

        if result["success"]:
            return f"✓ Uninstalled {name}"
        return f"✗ Failed: {result.get('error', 'unknown error')}"

    async def _handle_upgrade(self, name: Optional[str], tool_ctx: Any) -> str:
        """Upgrade tool package(s)."""
        from hanzo_mcp.tools.common.tool_registry import get_registry

        await tool_ctx.info(f"Upgrading {name or 'all packages'}...")
        registry = await get_registry()
        result = await registry.upgrade(name)

        if result["success"]:
            upgraded = [r["package"] for r in result.get("results", []) if r.get("success")]
            return f"✓ Upgraded: {', '.join(upgraded) if upgraded else 'none'}"
        return f"✗ Upgrade failed"

    async def _handle_reload(self, name: Optional[str], tool_ctx: Any) -> str:
        """Hot-reload a tool package."""
        if not name:
            return "Error: package name required for reload"

        from hanzo_mcp.tools.common.tool_registry import get_registry

        await tool_ctx.info(f"Reloading {name}...")
        registry = await get_registry()
        result = await registry.reload_package(name)

        if result["success"]:
            tools = result.get("tools", [])
            return f"✓ Reloaded {name}\nTools: {', '.join(tools) if tools else 'none'}"
        return f"✗ Failed: {result.get('error', 'unknown error')}"

    async def _handle_self_update(self, tool_ctx: Any) -> str:
        """Update hanzo-mcp itself."""
        from hanzo_mcp.tools.common.tool_registry import get_registry

        await tool_ctx.info("Checking for hanzo-mcp updates...")
        registry = await get_registry()
        result = await registry.self_update()

        if result["success"]:
            return f"✓ Updated hanzo-mcp from v{result.get('current_version')}\n{result.get('message', '')}"
        return f"✗ Update failed: {result.get('error', 'unknown error')}"

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def tool(
            action: Action = "list",
            name: Annotated[Optional[str], Field(description="Tool or package name")] = None,
            source: Annotated[str, Field(description="Source: pypi, git, local")] = "pypi",
            version: Annotated[Optional[str], Field(description="Version constraint")] = None,
            persist: Annotated[bool, Field(description="Persist changes")] = True,
            category: Annotated[Optional[str], Field(description="Filter by category")] = None,
            disabled: Annotated[bool, Field(description="Show only disabled")] = False,
            enabled: Annotated[bool, Field(description="Show only enabled")] = False,
            ctx: MCPContext = None,
        ) -> str:
            """Unified tool management: install, enable, disable, list, upgrade."""
            return await tool_instance.call(
                ctx,
                action=action,
                name=name,
                source=source,
                version=version,
                persist=persist,
                category=category,
                disabled=disabled,
                enabled=enabled,
            )


def register_unified_tool(mcp_server) -> list:
    """Register the unified tool command."""
    tool = UnifiedToolTool()
    tool.register(mcp_server)
    return [tool]
