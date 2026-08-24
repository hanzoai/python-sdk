"""MCP tool for Hanzo team surfaces — workspaces, membership and invitations.

Auth: Uses HanzoSession from hanzo-tools-auth for Bearer JWT tokens.
Backend: Hanzo IAM, which owns tenancy. Workspaces, memberships, invitations and
the signed-in account all live under /v1/iam/.

Addresses: a collection is a plural noun and one row of it is
{collection}/{owner}/{name} — a workspace is named by its owner and its name,
never by an opaque id. A collection GET answers a wrapper keyed by the plural,
a row GET answers the record itself, and absence is 404.

Two of these answer the {status, msg, data} envelope instead — memberships and
account — so each reader here reads the shape its own route answers.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Annotated, final

import httpx
from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

IAM_BASE_URL = os.getenv("IAM_URL", "https://hanzo.id")

DESCRIPTION = """Hanzo team — workspaces, membership and invitations.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

A workspace is named by owner and name, as `owner/name`.

Actions:
- workspaces: List workspaces (params: owner)
- workspace: Get one workspace (params: id, as owner/name)
- create_workspace: Create a workspace (params: owner, name, display_name)
- delete_workspace: Delete a workspace (params: id, as owner/name)
- members: List an organization's members (params: org)
- invite: Invite someone to an organization (params: org, email)
- account: Get the signed-in account
"""

ACTIONS = (
    "workspaces", "workspace", "create_workspace", "delete_workspace",
    "members", "invite", "account",
)


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _iam_url(path: str) -> str:
    """Build the full IAM URL. IAM serves its CRUD under /v1/iam/."""
    return f"{IAM_BASE_URL}/v1/iam/{path.lstrip('/')}"


def _auth_headers(token: str) -> dict[str, str]:
    """Build auth headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "hanzo-mcp/0.1",
    }


async def _iam(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Call IAM and return the decoded body."""
    session = _get_session()
    token = session.get_iam_token()
    if not token:
        raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method,
            _iam_url(path),
            headers=_auth_headers(token),
            params=params,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()


def _rows(data: Any, key: str) -> list:
    """Read a collection GET: {"workspaces": [...], "total": N} -> the list.

    A missing key is an error, not an empty page: reading it as [] would report
    "none" for a healthy org.
    """
    if not isinstance(data, dict) or key not in data:
        raise RuntimeError(f"IAM answered no {key} list")
    return data[key] or []


def _reason(response: httpx.Response) -> str:
    """The reason IAM gave: the RFC 9457 detail, the envelope's msg, else the body."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("title") or body.get("msg") or body)
    return str(body)


def _carried(data: Any) -> Any:
    """Read the {status, msg, data} envelope memberships and account answer."""
    if not isinstance(data, dict):
        return data
    if data.get("status") == "error":
        raise RuntimeError(data.get("msg") or "IAM refused the request")
    return data.get("data")


@final
class TeamTool(BaseTool):
    """MCP tool for Hanzo team operations."""

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
        id: str | None = None,
        owner: str | None = None,
        name: str | None = None,
        display_name: str | None = None,
        org: str | None = None,
        email: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            if action == "workspaces":
                return await self._workspaces(owner)
            elif action == "workspace":
                return await self._workspace(id)
            elif action == "create_workspace":
                return await self._create_workspace(owner, name, display_name)
            elif action == "delete_workspace":
                return await self._delete_workspace(id)
            elif action == "members":
                return await self._members(org)
            elif action == "invite":
                return await self._invite(org, email)
            elif action == "account":
                return await self._account()
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": list(ACTIONS),
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "error": f"IAM API error {e.response.status_code}",
                "detail": _reason(e.response),
            })
        except Exception as e:
            logger.exception(f"Team tool error: {e}")
            return json.dumps({"error": f"Team error: {e}"})

    # -- Workspace actions ---------------------------------------------------

    async def _workspaces(self, owner: str | None) -> str:
        params = {"owner": owner} if owner else {}
        data = await _iam("GET", "workspaces", params=params)
        result = [
            {
                "owner": w.get("owner"),
                "name": w.get("name"),
                "displayName": w.get("displayName"),
                "organization": w.get("organization"),
                "createdTime": w.get("createdTime"),
            }
            for w in _rows(data, "workspaces")
        ]
        return json.dumps(
            {"count": len(result), "total": data.get("total"), "workspaces": result},
            indent=2,
        )

    async def _workspace(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (workspace, format: owner/name)"})
        return json.dumps(await _iam("GET", f"workspaces/{id}"), indent=2)

    async def _create_workspace(
        self, owner: str | None, name: str | None, display_name: str | None
    ) -> str:
        if not owner or not name:
            return json.dumps({"error": "Required: owner, name. Optional: display_name"})
        data = await _iam("POST", "workspaces", body={
            "owner": owner,
            "name": name,
            "displayName": display_name or name,
            "organization": owner,
        })
        return json.dumps({"action": "created", "result": data}, indent=2)

    async def _delete_workspace(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (workspace, format: owner/name)"})
        data = await _iam("DELETE", f"workspaces/{id}")
        return json.dumps({"action": "deleted", "id": id, "result": data}, indent=2)

    # -- Member actions ------------------------------------------------------

    async def _members(self, org: str | None) -> str:
        if not org:
            return json.dumps({"error": "Required: org"})
        members = _carried(await _iam("GET", "memberships", params={"org": org})) or []
        result = [
            {
                "user": m.get("user"),
                "org": m.get("org"),
                "role": m.get("role"),
                "createdTime": m.get("createdTime"),
            }
            for m in members
        ]
        return json.dumps({"org": org, "count": len(result), "members": result}, indent=2)

    async def _invite(self, org: str | None, email: str | None) -> str:
        if not org or not email:
            return json.dumps({"error": "Required: org, email"})
        data = await _iam("POST", "invitations", body={
            "owner": org,
            "name": email.replace("@", "-at-").replace(".", "-"),
            "displayName": email,
            "email": email,
        })
        return json.dumps(
            {"action": "invited", "org": org, "email": email, "result": data}, indent=2
        )

    # -- Account action ------------------------------------------------------

    async def _account(self) -> str:
        return json.dumps(_carried(await _iam("GET", "account")), indent=2)

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
            id: Annotated[
                str | None,
                Field(description="Workspace, as owner/name (for workspace, delete_workspace)"),
            ] = None,
            owner: Annotated[
                str | None,
                Field(description="Organization owning the workspace (for workspaces, create_workspace)"),
            ] = None,
            name: Annotated[
                str | None,
                Field(description="Workspace name (for create_workspace)"),
            ] = None,
            display_name: Annotated[
                str | None,
                Field(description="Workspace display name (for create_workspace)"),
            ] = None,
            org: Annotated[
                str | None,
                Field(description="Organization (for members, invite)"),
            ] = None,
            email: Annotated[
                str | None,
                Field(description="Email address (for invite)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                id=id,
                owner=owner,
                name=name,
                display_name=display_name,
                org=org,
                email=email,
            )
