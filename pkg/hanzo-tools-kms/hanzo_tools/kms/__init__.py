"""Hanzo KMS Tools — secret management via MCP."""

from .kms_tool import KMSTool

TOOLS = [KMSTool]

__all__ = ["KMSTool", "TOOLS"]
