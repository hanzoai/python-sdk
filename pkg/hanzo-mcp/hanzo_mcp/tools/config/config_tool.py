"""Configuration tool for Hanzo AI.

Git-style config tool for managing settings.
"""

from typing import Unpack, Optional, Annotated, TypedDict, final, override
from pathlib import Path

from pydantic import Field
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.config import load_settings, save_settings
from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.config.index_config import IndexScope, IndexConfig

# Parameter types
Action = Annotated[
    str,
    Field(
        description="Action: get (default), set, list, toggle",
        default="get",
    ),
]

Key = Annotated[
    Optional[str],
    Field(
        description="Configuration key (e.g., tools.write.enabled, enabled_tools.write, index.scope)",
        default=None,
    ),
]

Value = Annotated[
    Optional[str],
    Field(
        description="Configuration value",
        default=None,
    ),
]

Scope = Annotated[
    str,
    Field(
        description="Config scope: local (project) or global",
        default="local",
    ),
]

ConfigPath = Annotated[
    Optional[str],
    Field(
        description="Path for project-specific config",
        default=None,
    ),
]


class ConfigParams(TypedDict, total=False):
    """Parameters for config tool."""

    action: str
    key: Optional[str]
    value: Optional[str]
    scope: str
    path: Optional[str]


def _parse_bool(value: str) -> Optional[bool]:
    v = value.strip().lower()
    if v in {"true", "1", "yes", "on"}:
        return True
    if v in {"false", "0", "no", "off"}:
        return False
    return None


@final
class ConfigTool(BaseTool):
    """Git-style configuration management tool."""

    def __init__(self, permission_manager: PermissionManager):
        """Initialize config tool."""
        super().__init__(permission_manager)
        self.index_config = IndexConfig()

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "config"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Git-style configuration. Actions: get (default), set, list, toggle.

Usage:
config index.scope
config --action set index.scope project
config --action set tools.write.enabled false
config --action list
config --action toggle index.scope --path ./project"""

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[ConfigParams],
    ) -> str:
        """Execute config operation."""
        tool_ctx = self.create_tool_context(ctx)

        # Extract parameters
        action = params.get("action", "get")
        key = params.get("key")
        value = params.get("value")
        scope = params.get("scope", "local")
        path = params.get("path")

        # Route to handler
        if action == "get":
            return await self._handle_get(key, scope, path, tool_ctx)
        elif action == "set":
            return await self._handle_set(key, value, scope, path, tool_ctx)
        elif action == "list":
            return await self._handle_list(scope, path, tool_ctx)
        elif action == "toggle":
            return await self._handle_toggle(key, scope, path, tool_ctx)
        else:
            return f"Error: Unknown action '{action}'. Valid actions: get, set, list, toggle"

    async def _handle_get(self, key: Optional[str], scope: str, path: Optional[str], tool_ctx) -> str:
        """Get configuration value."""
        if not key:
            return "Error: key required for get action"

        # Handle index scope
        if key == "index.scope":
            current_scope = self.index_config.get_scope(path)
            return f"index.scope={current_scope.value}"

        # tools.<name>.enabled → enabled_tools lookup
        if key.startswith("tools.") and key.endswith(".enabled"):
            parts = key.split(".")
            if len(parts) == 3:
                tool_name = parts[1]
                settings = load_settings(project_dir=path if scope == "local" else None)
                return f"{key}={settings.is_tool_enabled(tool_name)}"

        # enabled_tools.<name>
        if key.startswith("enabled_tools."):
            tool_name = key.split(".", 1)[1]
            settings = load_settings(project_dir=path if scope == "local" else None)
            val = settings.enabled_tools.get(tool_name)
            return f"{key}={val if val is not None else 'unset'}"

        # Indexing (legacy) per-tool setting: <tool>.enabled
        if "." in key:
            tool, setting = key.split(".", 1)
            if setting == "enabled":
                enabled = self.index_config.is_indexing_enabled(tool)
                return f"{key}={enabled}"

        return f"Unknown key: {key}"

    def _save_project_settings(self, settings, project_dir: Optional[str]) -> Path:
        """Save to project config if path provided; else global."""
        if project_dir:
            project_path = Path(project_dir)
            project_path.mkdir(parents=True, exist_ok=True)
            cfg = project_path / ".hanzo-mcp.json"
            cfg.write_text(
                __import__("json").dumps(settings.__dict__ if hasattr(settings, "__dict__") else {}, indent=2)
            )
            return cfg
        # Fallback to global handler
        return save_settings(settings, global_config=True)

    async def _handle_set(
        self,
        key: Optional[str],
        value: Optional[str],
        scope: str,
        path: Optional[str],
        tool_ctx,
    ) -> str:
        """Set configuration value."""
        if not key:
            return "Error: key required for set action"
        if value is None:
            return "Error: value required for set action"

        # Handle index scope
        if key == "index.scope":
            try:
                new_scope = IndexScope(value)
                self.index_config.set_scope(new_scope, path if scope == "local" else None)
                return f"Set {key}={value} ({'project' if path else 'global'})"
            except ValueError:
                return f"Error: Invalid scope value '{value}'. Valid: project, global, auto"

        # tools.<name>.enabled → enabled_tools mapping
        if key.startswith("tools.") and key.endswith(".enabled"):
            parts = key.split(".")
            if len(parts) == 3:
                tool_name = parts[1]
                parsed = _parse_bool(value)
                if parsed is None:
                    return "Error: value must be boolean (true/false)"
                settings = load_settings(project_dir=path if scope == "local" else None)
                et = dict(settings.enabled_tools)
                et[tool_name] = parsed
                settings.enabled_tools = et
                # Save
                if scope == "local" and path:
                    # Write a project .hanzo-mcp.json adjacent to the path
                    # Note: save_settings(local) saves to CWD; we target specific path here
                    out = self._save_project_settings(settings, path)
                    return f"Set {key}={parsed} (project: {out})"
                else:
                    out = save_settings(settings, global_config=True)
                    return f"Set {key}={parsed} (global: {out})"

        # enabled_tools.<name>
        if key.startswith("enabled_tools."):
            tool_name = key.split(".", 1)[1]
            parsed = _parse_bool(value)
            if parsed is None:
                return "Error: value must be boolean (true/false)"
            settings = load_settings(project_dir=path if scope == "local" else None)
            et = dict(settings.enabled_tools)
            et[tool_name] = parsed
            settings.enabled_tools = et
            if scope == "local" and path:
                out = self._save_project_settings(settings, path)
                return f"Set {key}={parsed} (project: {out})"
            else:
                out = save_settings(settings, global_config=True)
                return f"Set {key}={parsed} (global: {out})"

        # Indexing (legacy) per-tool setting: <tool>.enabled (search indexers)
        if "." in key:
            tool, setting = key.split(".", 1)
            if setting == "enabled":
                parsed = _parse_bool(value)
                if parsed is None:
                    return "Error: value must be boolean (true/false)"
                self.index_config.set_indexing_enabled(tool, parsed)
                return f"Set {key}={parsed}"

        return f"Unknown key: {key}"

    async def _handle_list(self, scope: str, path: Optional[str], tool_ctx) -> str:
        """List all configuration."""
        status = self.index_config.get_status()

        output = ["=== Configuration ==="]
        output.append(f"\nDefault scope: {status['default_scope']}")

        if path:
            current_scope = self.index_config.get_scope(path)
            output.append(f"Current path scope: {current_scope.value}")

        output.append(f"\nProjects with custom config: {status['project_count']}")

        output.append("\nTool settings (indexing):")
        for tool, settings in status["tools"].items():
            output.append(f"  {tool}:")
            output.append(f"    enabled: {settings['enabled']}")
            output.append(f"    per_project: {settings['per_project']}")

        # Also show enabled_tools snapshot
        settings_snapshot = load_settings(project_dir=path if scope == "local" else None)
        output.append("\nEnabled tools (execution):")
        for tool_name, enabled in sorted(settings_snapshot.enabled_tools.items()):
            output.append(f"  {tool_name}: {enabled}")

        return "\n".join(output)

    async def _handle_toggle(self, key: Optional[str], scope: str, path: Optional[str], tool_ctx) -> str:
        """Toggle configuration value."""
        if not key:
            return "Error: key required for toggle action"

        # Handle index scope toggle
        if key == "index.scope":
            new_scope = self.index_config.toggle_scope(path if scope == "local" else None)
            return f"Toggled index.scope to {new_scope.value}"

        # Handle execution tool enable/disable: tools.<name>.enabled or enabled_tools.<name>
        if key.startswith("tools.") and key.endswith(".enabled"):
            parts = key.split(".")
            if len(parts) == 3:
                tool_name = parts[1]
                settings = load_settings(project_dir=path if scope == "local" else None)
                current = bool(settings.enabled_tools.get(tool_name, True))
                settings.enabled_tools[tool_name] = not current
                if scope == "local" and path:
                    out = self._save_project_settings(settings, path)
                    return f"Toggled {key} to {not current} (project: {out})"
                else:
                    out = save_settings(settings, global_config=True)
                    return f"Toggled {key} to {not current} (global: {out})"

        if key.startswith("enabled_tools."):
            tool_name = key.split(".", 1)[1]
            settings = load_settings(project_dir=path if scope == "local" else None)
            current = bool(settings.enabled_tools.get(tool_name, True))
            settings.enabled_tools[tool_name] = not current
            if scope == "local" and path:
                out = self._save_project_settings(settings, path)
                return f"Toggled {key} to {not current} (project: {out})"
            else:
                out = save_settings(settings, global_config=True)
                return f"Toggled {key} to {not current} (global: {out})"

        # Handle indexing toggles (legacy)
        if "." in key:
            tool, setting = key.split(".", 1)
            if setting == "enabled":
                current = self.index_config.is_indexing_enabled(tool)
                self.index_config.set_indexing_enabled(tool, not current)
                return f"Toggled {key} to {not current}"

        return f"Cannot toggle key: {key}"

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        pass
