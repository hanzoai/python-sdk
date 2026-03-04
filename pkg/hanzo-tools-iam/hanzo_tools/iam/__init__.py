"""Hanzo IAM Tools — identity and access management via MCP."""

from .iam_tool import IAMTool

TOOLS = [IAMTool]

__all__ = ["IAMTool", "TOOLS"]
