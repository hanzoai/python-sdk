"""MCP tool for Hanzo authentication management.

Provides status, login (browser flow), logout, and whoami actions
accessible via Claude Code or any MCP client.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, final

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core.base import BaseTool

from .session import HanzoSession

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo authentication management.

Manage your Hanzo platform authentication. Check auth status, view current user
info, or logout.

Actions:
- status: Show current authentication state and accessible services
- whoami: Show current user info from IAM token
- logout: Clear stored credentials
- refresh: Refresh an expired token
"""


@final
class LoginTool(BaseTool):
    """MCP tool for authentication operations."""

    @property
    def name(self) -> str:
        return "auth"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "status",
        **kwargs: Any,
    ) -> str:
        session = HanzoSession.get()

        if action == "status":
            return await self._status(session)
        elif action == "whoami":
            return await self._whoami(session)
        elif action == "logout":
            return await self._logout(session)
        elif action == "refresh":
            return await self._refresh(session)
        else:
            return json.dumps({"error": f"Unknown action: {action}. Use: status, whoami, logout, refresh"})

    async def _status(self, session: HanzoSession) -> str:
        info = session.get_token_info()

        if not info.get("authenticated"):
            return json.dumps({
                "authenticated": False,
                "message": "Not authenticated. Run 'hanzo login' in your terminal to authenticate.",
                "services": {
                    "iam": False,
                    "kms": _check_kms_env(),
                    "paas": False,
                },
            }, indent=2)

        services = {
            "iam": True,
            "kms": _check_kms_env(),
            "paas": info.get("authenticated", False),
        }

        return json.dumps({
            "authenticated": True,
            "source": info.get("source", "unknown"),
            "organization": info.get("organization"),
            "server_url": info.get("server_url"),
            "expired": info.get("expired", False),
            "services": services,
        }, indent=2)

    async def _whoami(self, session: HanzoSession) -> str:
        if not session.is_authenticated():
            return json.dumps({"error": "Not authenticated. Run 'hanzo login' first."})

        try:
            iam_client = session.get_iam_client()
            token = session.get_iam_token()
            if token:
                # Try to decode JWT claims (without verification for display)
                try:
                    import jwt

                    claims = jwt.decode(token, options={"verify_signature": False})
                    return json.dumps({
                        "sub": claims.get("sub"),
                        "name": claims.get("name"),
                        "email": claims.get("email"),
                        "organization": claims.get("owner"),
                        "iss": claims.get("iss"),
                    }, indent=2)
                except Exception:
                    pass

            # Fallback to stored token info
            info = session.get_token_info()
            return json.dumps({
                "organization": info.get("organization"),
                "server_url": info.get("server_url"),
                "source": info.get("source"),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to get user info: {e}"})

    async def _logout(self, session: HanzoSession) -> str:
        session.logout()
        session.close()
        HanzoSession.reset()
        return json.dumps({"message": "Logged out. Cleared stored credentials."})

    async def _refresh(self, session: HanzoSession) -> str:
        if not session.is_authenticated():
            return json.dumps({"error": "Not authenticated. Run 'hanzo login' first."})

        if session.refresh_token():
            return json.dumps({"message": "Token refreshed successfully."})
        else:
            return json.dumps({"error": "Token refresh failed. Run 'hanzo login' again."})

    def register(self, mcp_server: FastMCP) -> None:
        """Register auth tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="auth",
            description=DESCRIPTION,
        )
        async def auth(
            action: Annotated[
                str,
                Field(
                    description="Action: status (check auth state), whoami (current user), logout, refresh",
                    default="status",
                ),
            ] = "status",
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(ctx, action=action)


def _check_kms_env() -> bool:
    """Check if KMS credentials are available."""
    import os

    return bool(os.getenv("HANZO_KMS_CLIENT_ID") and os.getenv("HANZO_KMS_CLIENT_SECRET"))
