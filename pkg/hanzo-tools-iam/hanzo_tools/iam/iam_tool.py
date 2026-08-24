"""MCP tool for Hanzo IAM — identity and access management.

Users, organizations, roles, permissions, providers, applications, tokens,
sessions, invitations and audit logs.

Auth: Uses HanzoSession from hanzo-tools-auth for Bearer JWT tokens.
Backend: Hanzo IAM (HIP-0026) — the CRUD surface under /v1/iam/.

Addresses: a collection is a plural noun and one row of it is
{collection}/{owner}/{name}. A collection GET answers a wrapper keyed by the
plural — {"users": [...], "total": N} — a row GET answers the record itself,
absence is 404, and a refusal is an RFC 9457 problem document.

Scope: IAM decides which organizations a caller may read. Omitting `owner` asks
for the caller's own scope, which is the right default; naming someone else's org
is refused rather than silently reinterpreted. Applications and sessions are the
two routes that require an owner, so those ask for one.
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

DESCRIPTION = """Hanzo IAM — identity and access management.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

User actions:
- users: List users (params: owner)
- user: Get one user (params: id, as owner/name)
- create_user: Create a user (params: owner, name, email, password, display_name)
- update_user: Update a user (params: id, plus fields to update)
- delete_user: Delete a user (params: id)

Organization actions:
- orgs: List organizations
- org: Get one organization (params: id, as admin/org-name)

Role and permission actions:
- roles: List roles (params: owner)
- role: Get one role (params: id, as owner/role-name)
- permissions: List permissions (params: owner)

Provider and application actions:
- providers: List auth providers (params: owner)
- apps: List applications (params: owner, required)

Token and session actions:
- tokens: List tokens (params: owner)
- sessions: List sessions (params: owner, required)

Invitation actions:
- invitations: List invitations (params: owner)
- invite: Send an invitation (params: email, org)

Audit actions:
- records: List audit logs (params: owner)
"""

ACTIONS = (
    "users", "user", "create_user", "update_user", "delete_user",
    "orgs", "org",
    "roles", "role", "permissions",
    "providers", "apps",
    "tokens", "sessions",
    "invitations", "invite",
    "records",
)


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _iam_url(path: str) -> str:
    """Build full IAM API URL.

    The Hanzo IAM server (HIP-0026) registers its CRUD surface under /v1/iam/.
    """
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
    """Read a collection GET: {"users": [...], "total": N} -> the list.

    A missing key is an error, not an empty page: reading it as [] would report
    "none" for a healthy org.
    """
    if not isinstance(data, dict) or key not in data:
        raise RuntimeError(f"IAM answered no {key} list")
    return data[key] or []


def _scope(owner: str | None) -> dict[str, str]:
    """Query scope. Omitted means the caller's own, which the server decides."""
    return {"owner": owner} if owner else {}


@final
class IAMTool(BaseTool):
    """MCP tool for Hanzo IAM operations."""

    @property
    def name(self) -> str:
        return "iam"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str,
        id: str | None = None,
        owner: str | None = None,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        display_name: str | None = None,
        org: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            # User actions
            if action == "users":
                return await self._users(owner)
            elif action == "user":
                return await self._user(id)
            elif action == "create_user":
                return await self._create_user(owner, name, email, password, display_name)
            elif action == "update_user":
                return await self._update_user(id, name, email, display_name, **kwargs)
            elif action == "delete_user":
                return await self._delete_user(id)

            # Organization actions
            elif action == "orgs":
                return await self._orgs()
            elif action == "org":
                return await self._org(id)

            # Role and permission actions
            elif action == "roles":
                return await self._roles(owner)
            elif action == "role":
                return await self._role(id)
            elif action == "permissions":
                return await self._permissions(owner)

            # Provider and application actions
            elif action == "providers":
                return await self._providers(owner)
            elif action == "apps":
                return await self._apps(owner)

            # Token and session actions
            elif action == "tokens":
                return await self._tokens(owner)
            elif action == "sessions":
                return await self._sessions(owner)

            # Invitation actions
            elif action == "invitations":
                return await self._invitations(owner)
            elif action == "invite":
                return await self._invite(email, org)

            # Audit actions
            elif action == "records":
                return await self._records(owner)

            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": list(ACTIONS),
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except httpx.HTTPStatusError as e:
            body = e.response.text
            try:
                body = e.response.json()
            except Exception:
                pass
            return json.dumps({"error": f"IAM API error {e.response.status_code}", "detail": body})
        except Exception as e:
            logger.exception(f"IAM tool error: {e}")
            return json.dumps({"error": f"IAM error: {e}"})

    # -- User actions --------------------------------------------------------

    async def _users(self, owner: str | None) -> str:
        data = await _iam("GET", "users", params=_scope(owner))
        result = [
            {
                "id": u.get("id"),
                "name": u.get("name"),
                "email": u.get("email"),
                "displayName": u.get("displayName"),
                "createdTime": u.get("createdTime"),
            }
            for u in _rows(data, "users")
        ]
        return json.dumps(
            {"owner": owner, "count": len(result), "total": data.get("total"), "users": result},
            indent=2,
        )

    async def _user(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: owner/name)"})
        return json.dumps(await _iam("GET", f"users/{id}"), indent=2)

    async def _create_user(
        self,
        owner: str | None,
        name: str | None,
        email: str | None,
        password: str | None,
        display_name: str | None,
    ) -> str:
        if not owner or not name or not email:
            return json.dumps({"error": "Required: owner, name, email. Optional: password, display_name"})

        body: dict[str, Any] = {
            "user": {
                "owner": owner,
                "name": name,
                "email": email,
                "displayName": display_name or name,
            },
        }
        # The password rides the create call and the server hashes it. It is
        # never a field on the user row.
        if password:
            body["password"] = password

        data = await _iam("POST", "users", body=body)
        return json.dumps({"action": "created", "result": data}, indent=2)

    async def _update_user(
        self,
        id: str | None,
        name: str | None,
        email: str | None,
        display_name: str | None,
        **kwargs: Any,
    ) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: owner/name)"})

        # A PUT replaces the row, so start from the stored one.
        current = await _iam("GET", f"users/{id}")

        if name is not None:
            current["name"] = name
        if email is not None:
            current["email"] = email
        if display_name is not None:
            current["displayName"] = display_name
        for k, v in kwargs.items():
            if v is not None:
                current[k] = v

        data = await _iam("PUT", f"users/{id}", body={"user": current})
        return json.dumps({"action": "updated", "id": id, "result": data}, indent=2)

    async def _delete_user(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: owner/name)"})
        data = await _iam("DELETE", f"users/{id}")
        return json.dumps({"action": "deleted", "id": id, "result": data}, indent=2)

    # -- Organization actions ------------------------------------------------

    async def _orgs(self) -> str:
        data = await _iam("GET", "organizations")
        result = [
            {
                "name": o.get("name"),
                "displayName": o.get("displayName"),
                "websiteUrl": o.get("websiteUrl"),
                "createdTime": o.get("createdTime"),
            }
            for o in _rows(data, "organizations")
        ]
        return json.dumps({"count": len(result), "organizations": result}, indent=2)

    async def _org(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (organization ID, format: admin/org-name)"})
        return json.dumps(await _iam("GET", f"organizations/{id}"), indent=2)

    # -- Role and permission actions -----------------------------------------

    async def _roles(self, owner: str | None) -> str:
        data = await _iam("GET", "roles", params=_scope(owner))
        result = [
            {
                "name": r.get("name"),
                "displayName": r.get("displayName"),
                "users": len(r.get("users") or []),
                "roles": len(r.get("roles") or []),
            }
            for r in _rows(data, "roles")
        ]
        return json.dumps({"count": len(result), "roles": result}, indent=2)

    async def _role(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (role ID, format: owner/role-name)"})
        return json.dumps(await _iam("GET", f"roles/{id}"), indent=2)

    async def _permissions(self, owner: str | None) -> str:
        data = await _iam("GET", "permissions", params=_scope(owner))
        result = [
            {
                "name": p.get("name"),
                "displayName": p.get("displayName"),
                "resources": p.get("resources") or [],
                "actions": p.get("actions") or [],
                "effect": p.get("effect"),
            }
            for p in _rows(data, "permissions")
        ]
        return json.dumps({"count": len(result), "permissions": result}, indent=2)

    # -- Provider and application actions ------------------------------------

    async def _providers(self, owner: str | None) -> str:
        data = await _iam("GET", "providers", params=_scope(owner))
        result = [
            {
                "name": p.get("name"),
                "displayName": p.get("displayName"),
                "type": p.get("type"),
                "category": p.get("category"),
            }
            for p in _rows(data, "providers")
        ]
        return json.dumps({"count": len(result), "providers": result}, indent=2)

    async def _apps(self, owner: str | None) -> str:
        if not owner:
            return json.dumps({"error": "Required: owner (IAM scopes applications by owner)"})
        data = await _iam("GET", "applications", params={"owner": owner})
        result = [
            {
                "name": a.get("name"),
                "displayName": a.get("displayName"),
                "organization": a.get("organization"),
                "clientId": a.get("clientId"),
            }
            for a in _rows(data, "applications")
        ]
        return json.dumps({"count": len(result), "applications": result}, indent=2)

    # -- Token and session actions -------------------------------------------

    async def _tokens(self, owner: str | None) -> str:
        data = await _iam("GET", "tokens", params=_scope(owner))
        result = [
            {
                "name": t.get("name"),
                "user": t.get("user"),
                "application": t.get("application"),
                "createdTime": t.get("createdTime"),
                "expiresIn": t.get("expiresIn"),
            }
            for t in _rows(data, "tokens")
        ]
        return json.dumps({"count": len(result), "tokens": result}, indent=2)

    async def _sessions(self, owner: str | None) -> str:
        if not owner:
            return json.dumps({"error": "Required: owner (IAM scopes sessions by owner)"})
        data = await _iam("GET", "sessions", params={"owner": owner})
        result = [
            {
                "name": s.get("name"),
                "application": s.get("application"),
                "createdTime": s.get("createdTime"),
                "sessionId": s.get("sessionId") or [],
            }
            for s in _rows(data, "sessions")
        ]
        return json.dumps({"count": len(result), "sessions": result}, indent=2)

    # -- Invitation actions --------------------------------------------------

    async def _invitations(self, owner: str | None) -> str:
        data = await _iam("GET", "invitations", params=_scope(owner))
        result = [
            {
                "name": i.get("name"),
                "email": i.get("email"),
                "state": i.get("state"),
                "createdTime": i.get("createdTime"),
            }
            for i in _rows(data, "invitations")
        ]
        return json.dumps({"count": len(result), "invitations": result}, indent=2)

    async def _invite(self, email: str | None, org: str | None) -> str:
        if not email or not org:
            return json.dumps({"error": "Required: email, org"})

        data = await _iam("POST", "invitations", body={
            "owner": org,
            "name": email.replace("@", "-at-").replace(".", "-"),
            "displayName": email,
            "email": email,
        })
        return json.dumps({"action": "invited", "email": email, "result": data}, indent=2)

    # -- Audit actions -------------------------------------------------------

    async def _records(self, owner: str | None) -> str:
        data = await _iam("GET", "audit-logs", params=_scope(owner))
        result = [
            {
                "name": r.get("name"),
                "method": r.get("method"),
                "requestUri": r.get("requestUri"),
                "action": r.get("action"),
                "createdTime": r.get("createdTime"),
                "user": r.get("user"),
                "ip": r.get("ip"),
            }
            for r in _rows(data, "auditLogs")[:50]
        ]
        return json.dumps({"count": len(result), "records": result}, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register IAM tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="iam",
            description=DESCRIPTION,
        )
        async def iam(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Users: users, user, create_user, update_user, delete_user. "
                        "Orgs: orgs, org. "
                        "Roles: roles, role, permissions. "
                        "Auth: providers, apps, tokens, sessions. "
                        "Invitations: invitations, invite. "
                        "Audit: records."
                    ),
                ),
            ],
            id: Annotated[
                str | None,
                Field(description="Row identity, as owner/name (users, roles, orgs)"),
            ] = None,
            owner: Annotated[
                str | None,
                Field(
                    description=(
                        "Organization to read. Omit for your own scope; apps and"
                        " sessions require one."
                    )
                ),
            ] = None,
            name: Annotated[
                str | None,
                Field(description="Name for create/update operations"),
            ] = None,
            email: Annotated[
                str | None,
                Field(description="Email for user creation or invitations"),
            ] = None,
            password: Annotated[
                str | None,
                Field(description="Password for user creation; the server hashes it"),
            ] = None,
            display_name: Annotated[
                str | None,
                Field(description="Display name for create/update operations"),
            ] = None,
            org: Annotated[
                str | None,
                Field(description="Organization name for invitations"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                id=id,
                owner=owner,
                name=name,
                email=email,
                password=password,
                display_name=display_name,
                org=org,
            )
