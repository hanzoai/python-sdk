"""Hanzo Auth Tools — authentication bridge for MCP platform tools.

Provides the HanzoSession singleton for shared auth state, and
the LoginTool MCP tool for auth management.
"""

from .session import HanzoSession
from .login_tool import LoginTool

# Tools list for entry point discovery
TOOLS = [LoginTool]

__all__ = [
    "LoginTool",
    "HanzoSession",
    "TOOLS",
]
