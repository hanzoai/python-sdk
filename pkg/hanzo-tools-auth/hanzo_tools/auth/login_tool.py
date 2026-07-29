"""MCP tool for Hanzo authentication management.

Actions are exactly what this tool can do — `login` runs the real
loopback+PKCE flow (hanzo_iam.oauth), and `status`/`whoami` report VERIFIED
state, not the mere presence of a string.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Annotated, final

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

from .session import HanzoSession

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo authentication management.

Sign in to the Hanzo platform, inspect the current session, or sign out.
Tokens are verified against the IdP's published signing keys — a token that
does not verify is reported as NOT authenticated.

Actions:
- login: Sign in via the browser (OAuth2 authorization code + PKCE). Opens a
  page at the IdP and waits for the redirect on a local loopback port.
- status: Show verified authentication state and accessible services
- whoami: Show the current user's verified token claims
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

        if action == "login":
            return await self._login(session, **kwargs)
        elif action == "status":
            return await self._status(session)
        elif action == "whoami":
            return await self._whoami(session)
        elif action == "logout":
            return await self._logout(session)
        elif action == "refresh":
            return await self._refresh(session)
        else:
            return json.dumps(
                {"error": f"Unknown action: {action}. Use: login, status, whoami, logout, refresh"}
            )

    async def _login(self, session: HanzoSession, **kwargs: Any) -> str:
        """Run the browser login. Blocks until the callback lands or it times out.

        Runs in a worker thread: the flow binds a socket and waits, and doing
        that on the event loop would wedge the whole MCP server.
        """
        import asyncio
        from functools import partial

        from hanzo_iam import IAMError

        allowed = {"server_url", "client_id", "organization", "scope", "timeout", "open_browser"}
        opts = {k: v for k, v in kwargs.items() if k in allowed and v is not None}

        urls: list[str] = []
        try:
            result = await asyncio.to_thread(
                partial(session.login, on_url=urls.append, **opts)
            )
        except IAMError as e:
            return json.dumps(
                {"authenticated": False, "error": str(e), "authorize_url": urls[0] if urls else None},
                indent=2,
            )
        except Exception as e:
            return json.dumps({"authenticated": False, "error": f"{type(e).__name__}: {e}"}, indent=2)

        claims = result["claims"]
        return json.dumps({
            "authenticated": True,
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "name": claims.get("name"),
            "organization": claims.get("owner") or claims.get("organization"),
            "expires_at": claims.get("exp"),
            "stored_in": result["store"],
        }, indent=2)

    async def _status(self, session: HanzoSession) -> str:
        info = session.get_token_info()

        if not info.get("authenticated"):
            return json.dumps({
                "authenticated": False,
                "reason": info.get("reason"),
                "detail": info.get("detail"),
                "message": "Not authenticated. Run the `login` action to sign in.",
                "services": {"iam": False, "kms": _check_kms_env(), "paas": False},
            }, indent=2)

        return json.dumps({
            "authenticated": True,
            "source": info.get("source", "unknown"),
            "store": info.get("store"),
            "organization": info.get("organization"),
            "server_url": info.get("server_url"),
            "expires_at": info.get("expires_at"),
            "expired": info.get("expired", False),
            # IAM is reachable and the token verified; the others are reported
            # from what we can actually check, never assumed from the IAM token.
            "services": {"iam": True, "kms": _check_kms_env(), "paas": False},
        }, indent=2)

    async def _whoami(self, session: HanzoSession) -> str:
        """Report the identity the ISSUER vouches for.

        Claims come from `verify()`, so they are only ever shown once the
        signature checked out. The previous version decoded the token with
        verify_signature=False and printed whatever it said — an attacker-
        chosen identity, rendered as fact.
        """
        result = session.verify()
        if not result.valid:
            return json.dumps(
                {"error": "Not authenticated.", "reason": result.reason, "detail": result.detail},
                indent=2,
            )
        claims = result.claims
        return json.dumps({
            "sub": claims.get("sub"),
            "name": claims.get("name"),
            "email": claims.get("email"),
            "organization": claims.get("owner") or claims.get("organization"),
            "iss": claims.get("iss"),
            "aud": claims.get("aud"),
            "exp": claims.get("exp"),
        }, indent=2)

    async def _logout(self, session: HanzoSession) -> str:
        session.logout()
        session.close()
        HanzoSession.reset()
        return json.dumps({"message": "Logged out. Cleared stored credentials."})

    async def _refresh(self, session: HanzoSession) -> str:
        # Refresh is exactly what an EXPIRED token needs, so this gates on
        # holding a credential, not on that credential still being valid.
        if not session.has_credential():
            return json.dumps({"error": "No stored credential. Run the `login` action first."})

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
                    description=(
                        "Action: login (browser sign-in), status (verified auth state),"
                        " whoami (current user), logout, refresh"
                    ),
                    default="status",
                ),
            ] = "status",
            timeout: Annotated[
                float,
                Field(description="login only: seconds to wait for the browser callback", default=300.0),
            ] = 300.0,
            open_browser: Annotated[
                bool,
                Field(description="login only: open the URL automatically", default=True),
            ] = True,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx, action=action, timeout=timeout, open_browser=open_browser
            )


def _check_kms_env() -> bool:
    """Check if KMS credentials are available."""
    import os

    return bool(os.getenv("HANZO_KMS_CLIENT_ID") and os.getenv("HANZO_KMS_CLIENT_SECRET"))
