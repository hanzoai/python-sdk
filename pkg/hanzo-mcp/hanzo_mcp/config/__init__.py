"""Unified configuration for hanzo-mcp.

Delegates to hanzoai.config (ConfigLoader, RuntimeConfig) for file discovery
and merging.  MCP-specific types (BackendConfig, PluginConfig, HanzoMCPSettings)
live here but are populated FROM the canonical RuntimeConfig.

Config file locations (handled by ConfigLoader):
  User:    ~/.hanzo/settings.json
  Project: .hanzo/settings.json
  Local:   .hanzo/settings.local.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Re-export canonical config types from hanzoai ---
from hanzoai.config import (
    ConfigEntry,
    ConfigError,
    ConfigLoader,
    ConfigSource,
    McpClaudeAiProxyConfig,
    McpOAuthConfig,
    McpRemoteConfig,
    McpSdkConfig,
    McpServerConfig,
    McpStdioConfig,
    McpTransport,
    McpWsConfig,
    OAuthConfig,
    RuntimeConfig,
)
from pydantic import BaseModel, Field

# --- Re-export tool config ---
from .tool_config import (
    TOOL_REGISTRY,
    DynamicToolRegistry,
    ToolCategory,
    ToolConfigEntry,
)

__all__ = [
    # hanzoai.config re-exports
    "ConfigEntry",
    "ConfigError",
    "ConfigLoader",
    "ConfigSource",
    "McpClaudeAiProxyConfig",
    "McpOAuthConfig",
    "McpRemoteConfig",
    "McpSdkConfig",
    "McpServerConfig",
    "McpStdioConfig",
    "McpTransport",
    "McpWsConfig",
    "OAuthConfig",
    "RuntimeConfig",
    # Tool config
    "TOOL_REGISTRY",
    "DynamicToolRegistry",
    "ToolCategory",
    "ToolConfigEntry",
    # MCP-specific models
    "BackendConfig",
    "PluginConfig",
    "HanzoMCPSettings",
    # Functions
    "get_global_config_path",
    "get_project_config_path",
    "load_config",
    "load_settings",
    "save_global_config",
    "save_settings",
    "get_default_config",
]


# ---------------------------------------------------------------------------
# MCP-specific Pydantic models
# ---------------------------------------------------------------------------

class BackendConfig(BaseModel):
    """Configuration for a specific MCP backend (e.g. sqlite memory)."""

    enabled: bool = True
    path: Optional[str] = None
    url: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class PluginConfig(BaseModel):
    """Plugin system configuration (backends, user/project IDs)."""

    enabled_backends: List[str] = ["sqlite"]
    backend_configs: Dict[str, BackendConfig] = Field(default_factory=dict)
    default_user_id: str = "default"
    default_project_id: str = "default"

    class Config:
        extra = "allow"


class ServerConfig(BaseModel):
    """Server runtime settings."""

    name: str = "hanzo-mcp"
    host: str = "127.0.0.1"
    port: int = 8888
    transport: str = "stdio"
    log_level: str = "INFO"
    command_timeout: float = 120.0


class AgentConfig(BaseModel):
    """Agent sub-agent settings."""

    enabled: bool = False
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_iterations: int = 10
    max_tool_uses: int = 30


class HanzoMCPSettings(BaseModel):
    """Top-level MCP settings.  Constructed from RuntimeConfig.merged."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    enabled_tools: Dict[str, bool] = Field(default_factory=dict)
    allowed_paths: List[str] = Field(default_factory=list)
    project_paths: List[str] = Field(default_factory=list)
    project_dir: Optional[str] = None

    class Config:
        extra = "allow"

    def is_tool_enabled(self, name: str) -> bool:
        if name in self.enabled_tools:
            return self.enabled_tools[name]
        entry = TOOL_REGISTRY.get(name)
        if entry is not None:
            return entry.enabled
        return True

    def get_enabled_tools(self) -> List[str]:
        DynamicToolRegistry.initialize()
        result = []
        for name in TOOL_REGISTRY.keys():
            if self.is_tool_enabled(name):
                result.append(name)
        return result


# ---------------------------------------------------------------------------
# Path helpers (backwards compat -- these now point to canonical locations)
# ---------------------------------------------------------------------------

def _config_home() -> Path:
    import os
    return Path(os.environ.get("HANZO_CONFIG_HOME", Path.home() / ".hanzo"))


def get_global_config_path() -> Path:
    """Canonical user config: ~/.hanzo/settings.json"""
    p = _config_home()
    p.mkdir(parents=True, exist_ok=True)
    return p / "settings.json"


def get_project_config_path() -> Optional[Path]:
    """Project config: .hanzo/settings.json in cwd."""
    p = Path.cwd() / ".hanzo" / "settings.json"
    if p.exists():
        return p
    return None


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def _runtime_to_plugin_config(rc: RuntimeConfig) -> PluginConfig:
    """Extract PluginConfig from the merged runtime dict."""
    plugins_raw = rc.merged.get("plugins", rc.merged.get("mcp", {}))
    if not isinstance(plugins_raw, dict):
        plugins_raw = {}

    backends_raw = plugins_raw.get("backend_configs", plugins_raw.get("backends", {}))
    backend_configs = {}
    for name, cfg in (backends_raw if isinstance(backends_raw, dict) else {}).items():
        if isinstance(cfg, dict):
            backend_configs[name] = BackendConfig(**cfg)

    return PluginConfig(
        enabled_backends=plugins_raw.get("enabled_backends", ["sqlite"]),
        backend_configs=backend_configs,
        default_user_id=plugins_raw.get("default_user_id", "default"),
        default_project_id=plugins_raw.get("default_project_id", "default"),
    )


def _runtime_to_settings(rc: RuntimeConfig) -> HanzoMCPSettings:
    """Build HanzoMCPSettings from a RuntimeConfig."""
    m = rc.merged

    server_raw = m.get("server", {})
    agent_raw = m.get("agent", {})
    enabled_tools = m.get("enabled_tools", {})

    return HanzoMCPSettings(
        server=ServerConfig(**{k: v for k, v in server_raw.items() if isinstance(server_raw, dict)}),
        agent=AgentConfig(**{k: v for k, v in agent_raw.items() if isinstance(agent_raw, dict)}),
        plugins=_runtime_to_plugin_config(rc),
        enabled_tools=enabled_tools if isinstance(enabled_tools, dict) else {},
        allowed_paths=m.get("allowed_paths", []),
        project_paths=m.get("project_paths", []),
        project_dir=m.get("project_dir"),
    )


def load_config(
    global_config_path: Optional[Path] = None,
    project_config_path: Optional[Path] = None,
) -> PluginConfig:
    """Load PluginConfig using canonical ConfigLoader.

    Accepts legacy path overrides for backwards compatibility but prefers
    the standard discovery (User/Project/Local).
    """
    loader = ConfigLoader.default_for(Path.cwd())
    rc = loader.load()

    # If caller passed explicit paths, layer them on top
    if global_config_path and global_config_path.is_file():
        extra = json.loads(global_config_path.read_text(encoding="utf-8"))
        if isinstance(extra, dict):
            rc.merged.update(extra)
    if project_config_path and project_config_path.is_file():
        extra = json.loads(project_config_path.read_text(encoding="utf-8"))
        if isinstance(extra, dict):
            rc.merged.update(extra)

    return _runtime_to_plugin_config(rc)


def load_settings(
    project_dir: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> HanzoMCPSettings:
    """Load full MCP settings via ConfigLoader, with optional overrides."""
    cwd = Path(project_dir) if project_dir else Path.cwd()
    loader = ConfigLoader.default_for(cwd)
    rc = loader.load()

    if config_overrides:
        from hanzoai.config import _deep_merge
        rc.merged = _deep_merge(rc.merged, config_overrides)

    settings = _runtime_to_settings(rc)
    if project_dir:
        settings.project_dir = project_dir
    return settings


def save_global_config(config: PluginConfig) -> None:
    """Save PluginConfig to ~/.hanzo/settings.json (merges into existing)."""
    path = get_global_config_path()
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    existing["plugins"] = config.model_dump()
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def save_settings(settings: HanzoMCPSettings, global_config: bool = True) -> Path:
    """Save HanzoMCPSettings to the appropriate config file.

    Returns the path written to.
    """
    data = settings.model_dump(exclude_none=True)

    if global_config:
        path = get_global_config_path()
    else:
        path = Path.cwd() / ".hanzo" / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    existing.update(data)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return path


def get_default_config() -> PluginConfig:
    """Default PluginConfig with sqlite backend."""
    return PluginConfig(
        enabled_backends=["sqlite"],
        backend_configs={
            "sqlite": BackendConfig(
                enabled=True,
                path=str(Path.home() / ".hanzo" / "memory.db"),
                settings={},
            )
        },
    )
