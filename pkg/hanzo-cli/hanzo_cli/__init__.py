"""Hanzo CLI — unified command-line interface for the Hanzo platform."""

import importlib.metadata as _md

try:
    __version__ = _md.version("hanzo-cli")
except _md.PackageNotFoundError:  # running from a source tree
    __version__ = "0.2.3"
