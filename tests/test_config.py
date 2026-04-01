"""Tests for hanzoai.config — hierarchical config discovery and merging."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hanzoai.config import (
    ConfigEntry,
    ConfigError,
    ConfigLoader,
    ConfigSource,
    McpClaudeAiProxyConfig,
    McpOAuthConfig,
    McpRemoteConfig,
    McpSdkConfig,
    McpStdioConfig,
    McpTransport,
    McpWsConfig,
    OAuthConfig,
    RuntimeConfig,
    _deep_merge,
)


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------


class TestDeepMerge:
    def test_flat_override(self):
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_flat_union(self):
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_nested_merge(self):
        base = {"a": {"x": 1, "y": 2}}
        over = {"a": {"y": 3, "z": 4}}
        assert _deep_merge(base, over) == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_nested_replace_non_dict(self):
        assert _deep_merge({"a": {"x": 1}}, {"a": 42}) == {"a": 42}

    def test_empty(self):
        assert _deep_merge({}, {"a": 1}) == {"a": 1}
        assert _deep_merge({"a": 1}, {}) == {"a": 1}


# ---------------------------------------------------------------------------
# ConfigLoader.discover
# ---------------------------------------------------------------------------


class TestDiscover:
    def test_returns_three_entries(self, tmp_path: Path):
        loader = ConfigLoader(cwd=tmp_path, config_home=tmp_path / ".hanzo")
        entries = loader.discover()
        assert len(entries) == 3
        assert entries[0].source == ConfigSource.User
        assert entries[1].source == ConfigSource.Project
        assert entries[2].source == ConfigSource.Local

    def test_paths(self, tmp_path: Path):
        home = tmp_path / "home" / ".hanzo"
        cwd = tmp_path / "project"
        loader = ConfigLoader(cwd=cwd, config_home=home)
        entries = loader.discover()
        assert entries[0].path == home / "settings.json"
        assert entries[1].path == cwd / ".hanzo" / "settings.json"
        assert entries[2].path == cwd / ".hanzo" / "settings.local.json"


# ---------------------------------------------------------------------------
# ConfigLoader.default_for
# ---------------------------------------------------------------------------


class TestDefaultFor:
    def test_uses_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        custom = tmp_path / "custom"
        monkeypatch.setenv("HANZO_CONFIG_HOME", str(custom))
        loader = ConfigLoader.default_for(tmp_path)
        assert loader.config_home == custom

    def test_falls_back_to_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("HANZO_CONFIG_HOME", raising=False)
        loader = ConfigLoader.default_for(tmp_path)
        assert loader.config_home == Path.home() / ".hanzo"


# ---------------------------------------------------------------------------
# ConfigLoader.load — file handling
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


class TestLoad:
    def test_empty_when_no_files(self, tmp_path: Path):
        loader = ConfigLoader(cwd=tmp_path, config_home=tmp_path / "h")
        cfg = loader.load()
        assert cfg.merged == {}
        assert cfg.loaded_entries == []

    def test_single_user_file(self, tmp_path: Path):
        home = tmp_path / "h"
        _write_json(home / "settings.json", {"theme": "dark"})
        cfg = ConfigLoader(cwd=tmp_path, config_home=home).load()
        assert cfg.merged == {"theme": "dark"}
        assert len(cfg.loaded_entries) == 1
        assert cfg.loaded_entries[0].source == ConfigSource.User

    def test_project_overrides_user(self, tmp_path: Path):
        home = tmp_path / "h"
        _write_json(home / "settings.json", {"a": 1, "b": 2})
        _write_json(tmp_path / ".hanzo" / "settings.json", {"b": 99})
        cfg = ConfigLoader(cwd=tmp_path, config_home=home).load()
        assert cfg.merged == {"a": 1, "b": 99}
        assert len(cfg.loaded_entries) == 2

    def test_local_overrides_project(self, tmp_path: Path):
        home = tmp_path / "h"
        _write_json(home / "settings.json", {"a": 1})
        _write_json(tmp_path / ".hanzo" / "settings.json", {"b": 2})
        _write_json(tmp_path / ".hanzo" / "settings.local.json", {"b": 3, "c": 4})
        cfg = ConfigLoader(cwd=tmp_path, config_home=home).load()
        assert cfg.merged == {"a": 1, "b": 3, "c": 4}
        assert len(cfg.loaded_entries) == 3

    def test_invalid_json_raises(self, tmp_path: Path):
        home = tmp_path / "h"
        p = home / "settings.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{bad json", encoding="utf-8")
        with pytest.raises(ConfigError, match="invalid JSON"):
            ConfigLoader(cwd=tmp_path, config_home=home).load()

    def test_non_object_top_level_raises(self, tmp_path: Path):
        home = tmp_path / "h"
        _write_json(home / "settings.json", [1, 2, 3])
        with pytest.raises(ConfigError, match="top-level value must be a JSON object"):
            ConfigLoader(cwd=tmp_path, config_home=home).load()

    def test_mcp_servers_replaced_not_merged(self, tmp_path: Path):
        home = tmp_path / "h"
        _write_json(home / "settings.json", {
            "mcpServers": {
                "alpha": {"command": "a", "transport": "stdio"},
                "beta": {"command": "b", "transport": "stdio"},
            }
        })
        _write_json(tmp_path / ".hanzo" / "settings.json", {
            "mcpServers": {
                "gamma": {"command": "g", "transport": "stdio"},
            }
        })
        cfg = ConfigLoader(cwd=tmp_path, config_home=home).load(trust_project_mcp=True)
        servers = cfg.mcp_servers()
        assert set(servers.keys()) == {"gamma"}


# ---------------------------------------------------------------------------
# RuntimeConfig accessors
# ---------------------------------------------------------------------------


class TestRuntimeConfig:
    def test_empty(self):
        cfg = RuntimeConfig.empty()
        assert cfg.merged == {}
        assert cfg.get("anything") is None

    def test_get(self):
        cfg = RuntimeConfig(merged={"foo": "bar"})
        assert cfg.get("foo") == "bar"
        assert cfg.get("nope") is None


# ---------------------------------------------------------------------------
# MCP server parsing
# ---------------------------------------------------------------------------


class TestMcpServers:
    def test_stdio(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "myserver": {
                    "transport": "stdio",
                    "command": "node",
                    "args": ["server.js"],
                    "env": {"PORT": "8080"},
                }
            }
        })
        servers = cfg.mcp_servers()
        s = servers["myserver"]
        assert isinstance(s, McpStdioConfig)
        assert s.command == "node"
        assert s.args == ["server.js"]
        assert s.env == {"PORT": "8080"}
        assert s.transport == McpTransport.Stdio

    def test_stdio_default_transport(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "s": {"command": "echo"}
            }
        })
        s = cfg.mcp_servers()["s"]
        assert isinstance(s, McpStdioConfig)

    def test_http_remote(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "remote": {
                    "transport": "http",
                    "url": "https://example.com/mcp",
                    "headers": {"Authorization": "Bearer tok"},
                }
            }
        })
        s = cfg.mcp_servers()["remote"]
        assert isinstance(s, McpRemoteConfig)
        assert s.url == "https://example.com/mcp"
        assert s.transport == McpTransport.Http

    def test_sse_remote(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "sse": {"transport": "sse", "url": "https://x.com/events"}
            }
        })
        s = cfg.mcp_servers()["sse"]
        assert isinstance(s, McpRemoteConfig)
        assert s.transport == McpTransport.Sse

    def test_ws(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "ws": {"transport": "ws", "url": "wss://x.com/ws"}
            }
        })
        s = cfg.mcp_servers()["ws"]
        assert isinstance(s, McpWsConfig)
        assert s.transport == McpTransport.Ws
        assert s.url == "wss://x.com/ws"

    def test_sdk(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "my-sdk": {"transport": "sdk", "name": "my-sdk-server"}
            }
        })
        s = cfg.mcp_servers()["my-sdk"]
        assert isinstance(s, McpSdkConfig)
        assert s.transport == McpTransport.Sdk
        assert s.name == "my-sdk-server"

    def test_claudeai_proxy(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "proxy": {
                    "transport": "claudeai-proxy",
                    "url": "https://claude.ai/proxy",
                    "id": "server-123",
                }
            }
        })
        s = cfg.mcp_servers()["proxy"]
        assert isinstance(s, McpClaudeAiProxyConfig)
        assert s.transport == McpTransport.ClaudeAiProxy
        assert s.url == "https://claude.ai/proxy"
        assert s.id == "server-123"

    def test_remote_with_oauth(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {
                "authed": {
                    "transport": "http",
                    "url": "https://example.com/mcp",
                    "oauth": {
                        "clientId": "cid",
                        "callbackPort": 9999,
                        "authServerMetadataUrl": "https://auth.example.com/.well-known",
                        "xaa": True,
                    },
                }
            }
        })
        s = cfg.mcp_servers()["authed"]
        assert isinstance(s, McpRemoteConfig)
        assert s.oauth is not None
        assert s.oauth.client_id == "cid"
        assert s.oauth.callback_port == 9999
        assert s.oauth.xaa is True

    def test_sdk_missing_name_raises(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {"bad": {"transport": "sdk"}}
        })
        with pytest.raises(ConfigError, match="requires 'name'"):
            cfg.mcp_servers()

    def test_claudeai_proxy_missing_id_raises(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {"bad": {"transport": "claudeai-proxy", "url": "https://x.com"}}
        })
        with pytest.raises(ConfigError, match="requires 'id'"):
            cfg.mcp_servers()

    def test_unknown_transport_raises(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {"bad": {"transport": "grpc"}}
        })
        with pytest.raises(ConfigError, match="unknown transport"):
            cfg.mcp_servers()

    def test_stdio_missing_command_raises(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {"bad": {"transport": "stdio"}}
        })
        with pytest.raises(ConfigError, match="requires 'command'"):
            cfg.mcp_servers()

    def test_http_missing_url_raises(self):
        cfg = RuntimeConfig(merged={
            "mcpServers": {"bad": {"transport": "http"}}
        })
        with pytest.raises(ConfigError, match="requires 'url'"):
            cfg.mcp_servers()

    def test_no_mcp_servers_returns_empty(self):
        assert RuntimeConfig.empty().mcp_servers() == {}


# ---------------------------------------------------------------------------
# OAuth parsing
# ---------------------------------------------------------------------------


class TestOAuth:
    def test_parses_camel_case(self):
        cfg = RuntimeConfig(merged={
            "oauth": {
                "clientId": "my-id",
                "authorizeUrl": "https://hanzo.id/authorize",
                "tokenUrl": "https://hanzo.id/token",
                "scopes": ["read", "write"],
                "callbackPort": 8080,
            }
        })
        oauth = cfg.oauth()
        assert isinstance(oauth, OAuthConfig)
        assert oauth.client_id == "my-id"
        assert oauth.authorize_url == "https://hanzo.id/authorize"
        assert oauth.token_url == "https://hanzo.id/token"
        assert oauth.scopes == ["read", "write"]
        assert oauth.callback_port == 8080

    def test_parses_snake_case(self):
        cfg = RuntimeConfig(merged={
            "oauth": {
                "client_id": "cid",
                "authorize_url": "https://hanzo.id/authorize",
                "token_url": "https://hanzo.id/token",
            }
        })
        oauth = cfg.oauth()
        assert oauth is not None
        assert oauth.client_id == "cid"
        assert oauth.authorize_url == "https://hanzo.id/authorize"

    def test_returns_none_when_missing(self):
        assert RuntimeConfig.empty().oauth() is None

    def test_returns_none_when_no_client_id(self):
        cfg = RuntimeConfig(merged={
            "oauth": {
                "authorizeUrl": "https://x.com/auth",
                "tokenUrl": "https://x.com/token",
            }
        })
        assert cfg.oauth() is None

    def test_returns_none_when_no_authorize_url(self):
        cfg = RuntimeConfig(merged={
            "oauth": {
                "clientId": "cid",
                "tokenUrl": "https://x.com/token",
            }
        })
        assert cfg.oauth() is None

    def test_returns_none_when_no_token_url(self):
        cfg = RuntimeConfig(merged={
            "oauth": {
                "clientId": "cid",
                "authorizeUrl": "https://x.com/auth",
            }
        })
        assert cfg.oauth() is None
