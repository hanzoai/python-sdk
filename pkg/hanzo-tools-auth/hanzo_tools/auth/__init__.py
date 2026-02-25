"""Hanzo Auth Tools — authentication bridge for MCP platform tools.

Provides the HanzoSession singleton for shared auth state, and
the LoginTool MCP tool for auth management.
"""

from .login_tool import LoginTool
from .session import HanzoSession

# Tools list for entry point discovery
TOOLS = [LoginTool]

__all__ = [
    "LoginTool",
    "HanzoSession",
    "TOOLS",
]
