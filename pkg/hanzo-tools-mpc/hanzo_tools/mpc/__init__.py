"""Hanzo MPC Tools -- threshold signing, vaults, wallets, and policies via MCP."""

from .mpc_tool import MPCTool

TOOLS = [MPCTool]

__all__ = ["MPCTool", "TOOLS"]
