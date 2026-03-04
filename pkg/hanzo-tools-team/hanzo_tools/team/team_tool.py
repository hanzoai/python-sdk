"""MCP tool for Hanzo Team — workspace and member management.

Manage workspaces, members, and invitations for collaborative
Hanzo Team accounts.

Auth: Uses HanzoSession from hanzo-tools-auth for Bearer JWT tokens.
Backend: Hanzo Team service.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, final

import httpx
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

TEAM_BASE_URL = os.getenv("HANZO_TEAM_URL", "https://api.hanzo.ai/team")

DESCRIPTION = """Hanzo Team — workspace and member management.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Actions:
- workspaces: List all workspaces
- workspace: Get workspace details (params: workspace_id)
- create_workspace: Create a new workspace (params: name)
- delete_workspace: Delete a workspace (params: workspace_id)
- members: List workspace members (params: workspace_id)
- invite: Invite a member to a workspace (params: workspace_id, email, role)
- account: Get current account info
"""


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _team_url(path: str) -> str:
    """Build full Team API URL."""
    return f"{TEAM_BASE_URL}/{path.lstrip('/')}"


def _auth_headers(token: str) -> dict[str, str]:
    """Build auth headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "hanzo-mcp/0.1",
    }


def _get_token() -> str:
    """Get Bearer token from session or raise."""
    session = _get_session()
    token = session.get_iam_token()
    if not token:
        raise RuntimeError("Not authenticated. Run 'hanzo login' first.")
    return token


async def _team_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET request to Team API."""
    token = _get_token()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _team_url(path),
            headers=_auth_headers(token),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def _team_post(path: str, body: dict[str, Any] | None = None) -> Any:
    """POST request to Team API."""
    token = _get_token()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _team_url(path),
            headers=_auth_headers(token),
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json()


async def _team_delete(path: str) -> Any:
    """DELETE request to Team API."""
    token = _get_token()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            _team_url(path),
            headers=_auth_headers(token),
        )
        resp.raise_for_status()
        if not resp.content or resp.status_code == 204:
            return {}
        return resp.json()


@final
class TeamTool(BaseTool):
    """MCP tool for Hanzo Team operations."""

    @property
    def name(self) -> str:
        return "team"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "account",
        workspace_id: str | None = None,
        name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            if action == "workspaces":
                return await self._workspaces()
            elif action == "workspace":
                return await self._workspace(workspace_id)
            elif action == "create_workspace":
                return await self._create_workspace(name)
            elif action == "delete_workspace":
                return await self._delete_workspace(workspace_id)
            elif action == "members":
                return await self._members(workspace_id)
            elif action == "invite":
                return await self._invite(workspace_id, email, role)
            elif action == "account":
                return await self._account()
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "workspaces", "workspace", "create_workspace",
                        "delete_workspace", "members", "invite", "account",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except httpx.HTTPStatusError as e:
            body = e.response.text
            try:
                body = e.response.json()
            except Exception:
                pass
            return json.dumps({"error": f"Team API error {e.response.status_code}", "detail": body})
        except Exception as e:
            logger.exception(f"Team tool error: {e}")
            return json.dumps({"error": f"Team error: {e}"})

    # -- Workspace actions ---------------------------------------------------

    async def _workspaces(self) -> str:
        data = await _team_get("workspaces")
        workspaces = data if isinstance(data, list) else data.get("workspaces", [])
        result = []
        for w in workspaces:
            result.append({
                "id": w.get("id"),
                "name": w.get("name"),
                "slug": w.get("slug"),
                "createdAt": w.get("createdAt"),
                "memberCount": w.get("memberCount"),
            })
        return json.dumps({"count": len(result), "workspaces": result}, indent=2)

    async def _workspace(self, workspace_id: str | None) -> str:
        if not workspace_id:
            return json.dumps({"error": "Required: workspace_id"})
        data = await _team_get(f"workspaces/{workspace_id}")
        return json.dumps(data, indent=2)

    async def _create_workspace(self, name: str | None) -> str:
        if not name:
            return json.dumps({"error": "Required: name"})
        data = await _team_post("workspaces", body={"name": name})
        return json.dumps({"action": "created", "result": data}, indent=2)

    async def _delete_workspace(self, workspace_id: str | None) -> str:
        if not workspace_id:
            return json.dumps({"error": "Required: workspace_id"})
        data = await _team_delete(f"workspaces/{workspace_id}")
        return json.dumps({"action": "deleted", "workspace_id": workspace_id, "result": data}, indent=2)

    # -- Member actions ------------------------------------------------------

    async def _members(self, workspace_id: str | None) -> str:
        if not workspace_id:
            return json.dumps({"error": "Required: workspace_id"})
        data = await _team_get(f"workspaces/{workspace_id}/members")
        members = data if isinstance(data, list) else data.get("members", [])
        result = []
        for m in members:
            result.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "email": m.get("email"),
                "role": m.get("role"),
                "joinedAt": m.get("joinedAt"),
            })
        return json.dumps({
            "workspace_id": workspace_id,
            "count": len(result),
            "members": result,
        }, indent=2)

    async def _invite(self, workspace_id: str | None, email: str | None, role: str | None) -> str:
        if not workspace_id or not email:
            return json.dumps({"error": "Required: workspace_id, email. Optional: role"})
        body: dict[str, Any] = {"email": email}
        if role:
            body["role"] = role
        data = await _team_post(f"workspaces/{workspace_id}/invitations", body=body)
        return json.dumps({
            "action": "invited",
            "workspace_id": workspace_id,
            "email": email,
            "role": role or "member",
            "result": data,
        }, indent=2)

    # -- Account action ------------------------------------------------------

    async def _account(self) -> str:
        data = await _team_get("account")
        return json.dumps(data, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register Team tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="team",
            description=DESCRIPTION,
        )
        async def team(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Workspaces: workspaces, workspace, create_workspace, delete_workspace. "
                        "Members: members, invite. "
                        "Account: account."
                    ),
                ),
            ] = "account",
            workspace_id: Annotated[
                str | None,
                Field(description="Workspace ID (for workspace, delete_workspace, members, invite)"),
            ] = None,
            name: Annotated[
                str | None,
                Field(description="Workspace name (for create_workspace)"),
            ] = None,
            email: Annotated[
                str | None,
                Field(description="Email address (for invite)"),
            ] = None,
            role: Annotated[
                str | None,
                Field(description="Member role (for invite, e.g. admin, member, viewer)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                workspace_id=workspace_id,
                name=name,
                email=email,
                role=role,
            )
