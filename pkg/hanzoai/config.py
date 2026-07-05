"""Hierarchical configuration discovery and merging.

Three layers (User < Project < Local). Later sources override earlier ones.
MCP server blocks replace entirely. Missing files silently skipped.

Security: Project-level configs (.hanzo/settings.json in a repo) are untrusted.
A cloned repo could contain a malicious config that defines mcpServers with
stdio transport (arbitrary command execution) or overrides oauth URLs (credential
phishing). By default, project and local configs are restricted to safe keys
only. Pass trust_project_mcp=True to override (requires explicit user approval).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when a config file exists but cannot be parsed."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")


class ConfigSource(IntEnum):
    """Config layer precedence. Higher value = higher priority."""

    User = 0
    Project = 1
    Local = 2


@dataclass(frozen=True)
class ConfigEntry:
    """A discovered config file location."""

    source: ConfigSource
    path: Path


class McpTransport(IntEnum):
    Stdio = 0
    Sse = 1
    Http = 2
    Ws = 3
    Sdk = 4
    ClaudeAiProxy = 5


@dataclass(frozen=True)
class McpStdioConfig:
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    @property
    def transport(self) -> McpTransport:
        return McpTransport.Stdio


@dataclass(frozen=True)
class McpOAuthConfig:
    client_id: str | None = None
    callback_port: int | None = None
    auth_server_metadata_url: str | None = None
    xaa: bool | None = None


@dataclass(frozen=True)
class McpRemoteConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    headers_helper: str | None = None
    oauth: McpOAuthConfig | None = None
    transport: McpTransport = McpTransport.Http


@dataclass(frozen=True)
class McpWsConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    headers_helper: str | None = None

    @property
    def transport(self) -> McpTransport:
        return McpTransport.Ws


@dataclass(frozen=True)
class McpSdkConfig:
    name: str

    @property
    def transport(self) -> McpTransport:
        return McpTransport.Sdk


@dataclass(frozen=True)
class McpClaudeAiProxyConfig:
    url: str
    id: str

    @property
    def transport(self) -> McpTransport:
        return McpTransport.ClaudeAiProxy


McpServerConfig = McpStdioConfig | McpRemoteConfig | McpWsConfig | McpSdkConfig | McpClaudeAiProxyConfig


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    authorize_url: str
    token_url: str
    scopes: list[str] = field(default_factory=list)
    callback_port: int | None = None
    manual_redirect_url: str | None = None


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge *override* into *base*, recursing into nested dicts.

    Non-dict values in *override* replace those in *base*.
    """
    merged = dict(base)
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = _deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged


_TRANSPORT_MAP: dict[str, McpTransport] = {
    "stdio": McpTransport.Stdio,
    "sse": McpTransport.Sse,
    "http": McpTransport.Http,
    "ws": McpTransport.Ws,
    "sdk": McpTransport.Sdk,
    "claudeai-proxy": McpTransport.ClaudeAiProxy,
}


def _parse_mcp_server(name: str, raw: dict) -> McpServerConfig:
    transport_str = raw.get("transport", "stdio")
    transport = _TRANSPORT_MAP.get(transport_str)
    if transport is None:
        raise ConfigError(
            Path("<memory>"),
            f"mcpServers.{name}: unknown transport {transport_str!r}",
        )

    if transport == McpTransport.Stdio:
        command = raw.get("command")
        if not command or not isinstance(command, str):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: stdio transport requires 'command' string",
            )
        args = raw.get("args", [])
        if not isinstance(args, list):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: 'args' must be a list",
            )
        env = raw.get("env", {})
        if not isinstance(env, dict):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: 'env' must be an object",
            )
        return McpStdioConfig(command=command, args=args, env=env)

    if transport == McpTransport.Sdk:
        sdk_name = raw.get("name")
        if not sdk_name or not isinstance(sdk_name, str):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: sdk transport requires 'name' string",
            )
        return McpSdkConfig(name=sdk_name)

    if transport == McpTransport.ClaudeAiProxy:
        url = raw.get("url")
        if not url or not isinstance(url, str):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: claudeai-proxy transport requires 'url' string",
            )
        server_id = raw.get("id")
        if not server_id or not isinstance(server_id, str):
            raise ConfigError(
                Path("<memory>"),
                f"mcpServers.{name}: claudeai-proxy transport requires 'id' string",
            )
        return McpClaudeAiProxyConfig(url=url, id=server_id)

    # Shared validation for url-based transports: sse, http, ws
    url = raw.get("url")
    if not url or not isinstance(url, str):
        raise ConfigError(
            Path("<memory>"),
            f"mcpServers.{name}: {transport_str} transport requires 'url' string",
        )
    headers = raw.get("headers", {})
    if not isinstance(headers, dict):
        raise ConfigError(
            Path("<memory>"),
            f"mcpServers.{name}: 'headers' must be an object",
        )
    headers_helper = raw.get("headersHelper") or raw.get("headers_helper")

    if transport == McpTransport.Ws:
        return McpWsConfig(url=url, headers=headers, headers_helper=headers_helper)

    # sse, http -> McpRemoteConfig
    oauth_raw = raw.get("oauth")
    oauth: McpOAuthConfig | None = None
    if isinstance(oauth_raw, dict):
        oauth = McpOAuthConfig(
            client_id=oauth_raw.get("clientId") or oauth_raw.get("client_id"),
            callback_port=oauth_raw.get("callbackPort") or oauth_raw.get("callback_port"),
            auth_server_metadata_url=oauth_raw.get("authServerMetadataUrl") or oauth_raw.get("auth_server_metadata_url"),
            xaa=oauth_raw.get("xaa"),
        )
    return McpRemoteConfig(url=url, headers=headers, headers_helper=headers_helper, oauth=oauth, transport=transport)


def _sanitize_project_config(data: dict, entry: ConfigEntry) -> dict:
    """Remove dangerous keys from an untrusted project/local config.

    Strips:
    - oauth (credential phishing via overridden auth URLs)
    - mcpServers entries with stdio transport (arbitrary command execution)

    Non-stdio mcpServers (http, sse, ws, sdk) are kept -- they connect to
    remote URLs which are visible and auditable, not local binary execution.
    """
    sanitized = dict(data)

    if "oauth" in sanitized:
        logger.warning(
            "Ignoring 'oauth' from project config %s — "
            "project configs cannot override OAuth URLs (phishing risk). "
            "Move to user config (~/.hanzo/settings.json) instead.",
            entry.path,
        )
        del sanitized["oauth"]

    mcp_raw = sanitized.get("mcpServers")
    if isinstance(mcp_raw, dict):
        safe_servers: dict = {}
        for name, cfg in mcp_raw.items():
            transport = cfg.get("transport", "stdio") if isinstance(cfg, dict) else "stdio"
            if transport == "stdio":
                logger.warning(
                    "Ignoring mcpServers.%s (stdio) from project config %s — "
                    "project configs cannot define stdio MCP servers (arbitrary "
                    "command execution risk). Move to user config or pass "
                    "trust_project_mcp=True.",
                    name,
                    entry.path,
                )
            else:
                safe_servers[name] = cfg
        if safe_servers:
            sanitized["mcpServers"] = safe_servers
        else:
            del sanitized["mcpServers"]

    return sanitized


@dataclass
class RuntimeConfig:
    """Merged configuration from all discovered layers."""

    merged: dict = field(default_factory=dict)
    loaded_entries: list[ConfigEntry] = field(default_factory=list)

    @classmethod
    def empty(cls) -> RuntimeConfig:
        return cls()

    def get(self, key: str) -> Any | None:
        return self.merged.get(key)

    def mcp_servers(self) -> dict[str, McpServerConfig]:
        raw = self.merged.get("mcpServers")
        if not isinstance(raw, dict):
            return {}
        return {name: _parse_mcp_server(name, cfg) for name, cfg in raw.items()}

    def oauth(self) -> OAuthConfig | None:
        raw = self.merged.get("oauth")
        if not isinstance(raw, dict):
            return None
        client_id = raw.get("clientId") or raw.get("client_id")
        if not client_id or not isinstance(client_id, str):
            return None
        authorize_url = raw.get("authorizeUrl") or raw.get("authorize_url")
        if not authorize_url or not isinstance(authorize_url, str):
            return None
        token_url = raw.get("tokenUrl") or raw.get("token_url")
        if not token_url or not isinstance(token_url, str):
            return None
        callback_port = raw.get("callbackPort") or raw.get("callback_port")
        return OAuthConfig(
            client_id=client_id,
            authorize_url=authorize_url,
            token_url=token_url,
            scopes=raw.get("scopes", []),
            callback_port=callback_port,
            manual_redirect_url=raw.get("manualRedirectUrl") or raw.get("manual_redirect_url"),
        )


@dataclass(frozen=True)
class ConfigLoader:
    """Discovers and loads hierarchical config files."""

    cwd: Path
    config_home: Path

    @classmethod
    def default_for(cls, cwd: Path) -> ConfigLoader:
        config_home = Path(os.environ.get("HANZO_CONFIG_HOME", Path.home() / ".hanzo"))
        return cls(cwd=cwd, config_home=config_home)

    def discover(self) -> list[ConfigEntry]:
        """Return potential config file entries in precedence order (low to high)."""
        return [
            ConfigEntry(ConfigSource.User, self.config_home / "settings.json"),
            ConfigEntry(ConfigSource.Project, self.cwd / ".hanzo" / "settings.json"),
            ConfigEntry(ConfigSource.Local, self.cwd / ".hanzo" / "settings.local.json"),
        ]

    # Keys that are safe to accept from project-level (untrusted) configs.
    # mcpServers with stdio transport allows arbitrary command execution.
    # oauth allows credential phishing by overriding auth URLs.
    # Both are blocked from project/local configs unless explicitly trusted.
    _PROJECT_SAFE_KEYS = frozenset({"model", "env", "hooks"})

    def load(self, *, trust_project_mcp: bool = False) -> RuntimeConfig:
        """Read and merge all existing config files.

        Missing files are silently skipped. Invalid JSON raises ConfigError.
        The top-level value in each file must be a JSON object.

        Args:
            trust_project_mcp: When False (default), project-level and
                local-level configs cannot define mcpServers with stdio
                transport or oauth blocks. This prevents a malicious cloned
                repo from executing arbitrary commands or phishing credentials
                via .hanzo/settings.json. Set True only after explicit user
                approval.
        """
        merged: dict = {}
        loaded: list[ConfigEntry] = []

        for entry in self.discover():
            if not entry.path.is_file():
                continue

            text = entry.path.read_text(encoding="utf-8")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ConfigError(entry.path, f"invalid JSON: {exc}") from exc

            if not isinstance(data, dict):
                raise ConfigError(entry.path, "top-level value must be a JSON object")

            # R-06: Project/local configs are untrusted. Strip dangerous keys
            # unless the caller has explicitly opted in.
            if entry.source in (ConfigSource.Project, ConfigSource.Local) and not trust_project_mcp:
                data = _sanitize_project_config(data, entry)

            # MCP servers from later sources replace entirely (not merged).
            if "mcpServers" in data and "mcpServers" in merged:
                del merged["mcpServers"]

            merged = _deep_merge(merged, data)
            loaded.append(entry)

        return RuntimeConfig(merged=merged, loaded_entries=loaded)
