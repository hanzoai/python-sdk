"""Hanzo Node - Cross-platform installer for the Hanzo AI node."""

__version__ = "0.1.0"

from .installer import install, uninstall, is_installed, get_binary_path

__all__ = ["install", "uninstall", "get_binary_path", "is_installed", "__version__"]
