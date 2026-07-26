"""Hanzo - Complete AI Infrastructure Platform with CLI, Router, MCP, and Agent Runtime."""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    # The installed distribution is the single source of the version. Hardcoding
    # it here meant three declarations (pyproject 0.4.4, this file 0.3.47,
    # cli.py 0.3.48) that drifted apart, so `hanzo --version` reported a release
    # that did not exist and no one could tell what they were actually running.
    __version__ = _version("hanzo")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0.0.0+dev"

__all__ = ["main", "cli", "__version__"]

from .cli import cli, main
