"""Hanzo AI - Implementation of Hanzo capabilities using MCP."""

# Polyfill typing.override for Python < 3.12
try:  # pragma: no cover
    from typing import override as _override  # type: ignore
except Exception:  # pragma: no cover
    import typing as _typing

    def override(obj):  # type: ignore
        return obj

    _typing.override = override  # type: ignore[attr-defined]

# Configure FastMCP logging globally for stdio transport
import os
import warnings

# Suppress llm deprecation warnings about event loop
warnings.filterwarnings(
    "ignore", message="There is no current event loop", category=DeprecationWarning
)

if os.environ.get("HANZO_MCP_TRANSPORT") == "stdio":
    try:
        from fastmcp.utilities.logging import configure_logging

        configure_logging(level="ERROR")
    except ImportError:
        pass

# Version from pyproject.toml (single source of truth)
try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("hanzo-mcp")
except Exception:
    __version__ = "0.10.24"  # fallback

# Re-export canonical types from hanzoai core.
# hanzo-mcp works standalone but prefers hanzoai when available.
try:
    from hanzoai.config import ConfigLoader, RuntimeConfig
    from hanzoai.mcp import MCPClient, mcp_tool_name, normalize_mcp_name
    from hanzoai.protocols import PermissionMode, PermissionOutcome, PermissionPolicy
    from hanzoai.session import CompactionConfig, Session, compact_session
except ImportError:
    pass  # hanzoai not installed, MCP server still works standalone
