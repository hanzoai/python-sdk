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

# Suppress litellm deprecation warnings about event loop
warnings.filterwarnings("ignore", message="There is no current event loop", category=DeprecationWarning)

if os.environ.get("HANZO_MCP_TRANSPORT") == "stdio":
    try:
        from fastmcp.utilities.logging import configure_logging

        configure_logging(level="ERROR")
    except ImportError:
        pass

__version__ = "0.8.4"
