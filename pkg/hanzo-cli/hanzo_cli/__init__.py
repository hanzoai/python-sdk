"""Hanzo CLI — unified command-line interface for the Hanzo platform."""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    # Single-sourced from the installed distribution. This said "0.1.0" while
    # pyproject said 0.2.2, and click's version_option read THIS — which is why
    # `hanzo --version` reported a release that never existed.
    __version__ = _version("hanzo-cli")
except PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+dev"
