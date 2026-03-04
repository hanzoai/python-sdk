"""MCP tool for Hanzo IAM — identity and access management.

Full control over users, organizations, roles, permissions, providers,
applications, tokens, sessions, invitations, and audit records.

Auth: Uses HanzoSession from hanzo-tools-auth for Bearer JWT tokens.
Backend: Casdoor IAM at hanzo.id/api/
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

IAM_BASE_URL = os.getenv("HANZO_IAM_URL", "https://hanzo.id")

DESCRIPTION = """Hanzo IAM — identity and access management.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

User actions:
- users: List users (params: owner)
- user: Get user by ID (params: id)
- create_user: Create a user (params: owner, name, email, password, display_name)
- update_user: Update a user (params: id, plus fields to update)
- delete_user: Delete a user (params: id)

Organization actions:
- orgs: List organizations
- org: Get organization details (params: id)

Role and permission actions:
- roles: List roles
- role: Get role details (params: id)
- permissions: List permissions
- enforce: Check permission (params: owner, model, resource, action)

Provider and application actions:
- providers: List auth providers
- apps: List applications

Token and session actions:
- tokens: List tokens
- sessions: List sessions

Invitation actions:
- invitations: List invitations
- invite: Send invitation (params: email, org)

Audit and system actions:
- records: List audit records
- system_info: Get IAM system info
- health: Health check
"""


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _iam_url(path: str) -> str:
    """Build full IAM API URL."""
    return f"{IAM_BASE_URL}/api/{path.lstrip('/')}"


def _auth_headers(token: str) -> dict[str, str]:
    """Build auth headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "hanzo-mcp/0.1",
    }


async def _iam_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET request to IAM API."""
    session = _get_session()
    token = session.get_iam_token()
    if not token:
        raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _iam_url(path),
            headers=_auth_headers(token),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def _iam_post(path: str, body: dict[str, Any] | None = None) -> Any:
    """POST request to IAM API."""
    session = _get_session()
    token = session.get_iam_token()
    if not token:
        raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _iam_url(path),
            headers=_auth_headers(token),
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json()


async def _iam_delete(path: str, body: dict[str, Any] | None = None) -> Any:
    """DELETE request to IAM API."""
    session = _get_session()
    token = session.get_iam_token()
    if not token:
        raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _iam_url(path),
            headers=_auth_headers(token),
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json()


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
        action: str = "health",
        id: str | None = None,
        owner: str | None = None,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        display_name: str | None = None,
        org: str | None = None,
        model: str | None = None,
        resource: str | None = None,
        permission_action: str | None = None,
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
                return await self._roles()
            elif action == "role":
                return await self._role(id)
            elif action == "permissions":
                return await self._permissions()
            elif action == "enforce":
                return await self._enforce(owner, model, resource, permission_action)

            # Provider and application actions
            elif action == "providers":
                return await self._providers()
            elif action == "apps":
                return await self._apps()

            # Token and session actions
            elif action == "tokens":
                return await self._tokens()
            elif action == "sessions":
                return await self._sessions()

            # Invitation actions
            elif action == "invitations":
                return await self._invitations()
            elif action == "invite":
                return await self._invite(email, org)

            # Audit and system actions
            elif action == "records":
                return await self._records()
            elif action == "system_info":
                return await self._system_info()
            elif action == "health":
                return await self._health()

            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "users", "user", "create_user", "update_user", "delete_user",
                        "orgs", "org",
                        "roles", "role", "permissions", "enforce",
                        "providers", "apps",
                        "tokens", "sessions",
                        "invitations", "invite",
                        "records", "system_info", "health",
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
            return json.dumps({"error": f"IAM API error {e.response.status_code}", "detail": body})
        except Exception as e:
            logger.exception(f"IAM tool error: {e}")
            return json.dumps({"error": f"IAM error: {e}"})

    # -- User actions --------------------------------------------------------

    async def _users(self, owner: str | None) -> str:
        owner = owner or "hanzo"
        data = await _iam_get("get-users", params={"owner": owner})
        users = data if isinstance(data, list) else []
        result = []
        for u in users:
            result.append({
                "id": u.get("id"),
                "name": u.get("name"),
                "email": u.get("email"),
                "displayName": u.get("displayName"),
                "createdTime": u.get("createdTime"),
            })
        return json.dumps({"owner": owner, "count": len(result), "users": result}, indent=2)

    async def _user(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: org/username)"})
        data = await _iam_get("get-user", params={"id": id})
        return json.dumps(data, indent=2)

    async def _create_user(
        self,
        owner: str | None,
        name: str | None,
        email: str | None,
        password: str | None,
        display_name: str | None,
    ) -> str:
        if not name or not email:
            return json.dumps({"error": "Required: name, email. Optional: owner, password, display_name"})

        user_data = {
            "owner": owner or "hanzo",
            "name": name,
            "email": email,
            "displayName": display_name or name,
        }
        if password:
            user_data["password"] = password

        data = await _iam_post("add-user", body={"user": user_data})
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
            return json.dumps({"error": "Required: id (user ID, format: org/username)"})

        # Fetch current user first
        current = await _iam_get("get-user", params={"id": id})
        if not isinstance(current, dict):
            return json.dumps({"error": f"User not found: {id}"})

        # Apply updates
        if name is not None:
            current["name"] = name
        if email is not None:
            current["email"] = email
        if display_name is not None:
            current["displayName"] = display_name
        for k, v in kwargs.items():
            if v is not None:
                current[k] = v

        data = await _iam_post("update-user", body={"user": current})
        return json.dumps({"action": "updated", "id": id, "result": data}, indent=2)

    async def _delete_user(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: org/username)"})

        # Fetch user to get full object for deletion
        current = await _iam_get("get-user", params={"id": id})
        if not isinstance(current, dict):
            return json.dumps({"error": f"User not found: {id}"})

        data = await _iam_delete("delete-user", body={"user": current})
        return json.dumps({"action": "deleted", "id": id, "result": data}, indent=2)

    # -- Organization actions ------------------------------------------------

    async def _orgs(self) -> str:
        data = await _iam_get("get-organizations", params={"owner": "admin"})
        orgs = data if isinstance(data, list) else []
        result = []
        for o in orgs:
            result.append({
                "name": o.get("name"),
                "displayName": o.get("displayName"),
                "websiteUrl": o.get("websiteUrl"),
                "createdTime": o.get("createdTime"),
            })
        return json.dumps({"count": len(result), "organizations": result}, indent=2)

    async def _org(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (organization ID, format: admin/org-name)"})
        data = await _iam_get("get-organization", params={"id": id})
        return json.dumps(data, indent=2)

    # -- Role and permission actions -----------------------------------------

    async def _roles(self) -> str:
        data = await _iam_get("get-roles", params={"owner": "hanzo"})
        roles = data if isinstance(data, list) else []
        result = []
        for r in roles:
            result.append({
                "name": r.get("name"),
                "displayName": r.get("displayName"),
                "users": len(r.get("users", [])),
                "roles": len(r.get("roles", [])),
            })
        return json.dumps({"count": len(result), "roles": result}, indent=2)

    async def _role(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (role ID, format: org/role-name)"})
        data = await _iam_get("get-role", params={"id": id})
        return json.dumps(data, indent=2)

    async def _permissions(self) -> str:
        data = await _iam_get("get-permissions", params={"owner": "hanzo"})
        perms = data if isinstance(data, list) else []
        result = []
        for p in perms:
            result.append({
                "name": p.get("name"),
                "displayName": p.get("displayName"),
                "resources": p.get("resources", []),
                "actions": p.get("actions", []),
                "effect": p.get("effect"),
            })
        return json.dumps({"count": len(result), "permissions": result}, indent=2)

    async def _enforce(
        self,
        owner: str | None,
        model: str | None,
        resource: str | None,
        action: str | None,
    ) -> str:
        if not model or not resource or not action:
            return json.dumps({"error": "Required: model, resource, permission_action. Optional: owner"})

        data = await _iam_get("enforce", params={
            "owner": owner or "hanzo",
            "model": model,
            "resource": resource,
            "action": action,
        })
        return json.dumps({
            "allowed": data,
            "model": model,
            "resource": resource,
            "action": action,
        }, indent=2)

    # -- Provider and application actions ------------------------------------

    async def _providers(self) -> str:
        data = await _iam_get("get-providers", params={"owner": "admin"})
        providers = data if isinstance(data, list) else []
        result = []
        for p in providers:
            result.append({
                "name": p.get("name"),
                "displayName": p.get("displayName"),
                "type": p.get("type"),
                "category": p.get("category"),
            })
        return json.dumps({"count": len(result), "providers": result}, indent=2)

    async def _apps(self) -> str:
        data = await _iam_get("get-applications", params={"owner": "admin"})
        apps = data if isinstance(data, list) else []
        result = []
        for a in apps:
            result.append({
                "name": a.get("name"),
                "displayName": a.get("displayName"),
                "organization": a.get("organization"),
                "clientId": a.get("clientId"),
            })
        return json.dumps({"count": len(result), "applications": result}, indent=2)

    # -- Token and session actions -------------------------------------------

    async def _tokens(self) -> str:
        data = await _iam_get("get-tokens", params={"owner": "admin"})
        tokens = data if isinstance(data, list) else []
        result = []
        for t in tokens:
            result.append({
                "name": t.get("name"),
                "user": t.get("user"),
                "application": t.get("application"),
                "createdTime": t.get("createdTime"),
                "expiresIn": t.get("expiresIn"),
            })
        return json.dumps({"count": len(result), "tokens": result}, indent=2)

    async def _sessions(self) -> str:
        data = await _iam_get("get-sessions", params={"owner": "admin"})
        sessions = data if isinstance(data, list) else []
        result = []
        for s in sessions:
            result.append({
                "name": s.get("name"),
                "application": s.get("application"),
                "createdTime": s.get("createdTime"),
                "sessionId": s.get("sessionId", []),
            })
        return json.dumps({"count": len(result), "sessions": result}, indent=2)

    # -- Invitation actions --------------------------------------------------

    async def _invitations(self) -> str:
        data = await _iam_get("get-invitations", params={"owner": "admin"})
        invitations = data if isinstance(data, list) else []
        result = []
        for i in invitations:
            result.append({
                "name": i.get("name"),
                "email": i.get("email"),
                "state": i.get("state"),
                "createdTime": i.get("createdTime"),
            })
        return json.dumps({"count": len(result), "invitations": result}, indent=2)

    async def _invite(self, email: str | None, org: str | None) -> str:
        if not email:
            return json.dumps({"error": "Required: email. Optional: org"})

        invitation = {
            "owner": "admin",
            "name": email.replace("@", "-at-").replace(".", "-"),
            "email": email,
            "organization": org or "hanzo",
        }
        data = await _iam_post("add-invitation", body={"invitation": invitation})
        return json.dumps({"action": "invited", "email": email, "result": data}, indent=2)

    # -- Audit and system actions --------------------------------------------

    async def _records(self) -> str:
        data = await _iam_get("get-records", params={"owner": "admin"})
        records = data if isinstance(data, list) else []
        result = []
        for r in records[:50]:  # Limit to 50 most recent
            result.append({
                "name": r.get("name"),
                "method": r.get("method"),
                "requestUri": r.get("requestUri"),
                "action": r.get("action"),
                "createdTime": r.get("createdTime"),
                "user": r.get("user"),
                "ip": r.get("ip"),
            })
        return json.dumps({"count": len(result), "records": result}, indent=2)

    async def _system_info(self) -> str:
        data = await _iam_get("get-system-info")
        return json.dumps(data, indent=2)

    async def _health(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{IAM_BASE_URL}/api/health")
                return json.dumps({
                    "status": "ok" if resp.status_code == 200 else "error",
                    "code": resp.status_code,
                    "url": IAM_BASE_URL,
                }, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e), "url": IAM_BASE_URL})

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
                        "Roles: roles, role, permissions, enforce. "
                        "Auth: providers, apps, tokens, sessions. "
                        "Invitations: invitations, invite. "
                        "System: records, system_info, health."
                    ),
                ),
            ] = "health",
            id: Annotated[
                str | None,
                Field(description="Entity ID (format: org/name for users, roles, etc.)"),
            ] = None,
            owner: Annotated[
                str | None,
                Field(description="Organization owner (default: hanzo)"),
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
                Field(description="Password for user creation"),
            ] = None,
            display_name: Annotated[
                str | None,
                Field(description="Display name for create/update operations"),
            ] = None,
            org: Annotated[
                str | None,
                Field(description="Organization name for invitations"),
            ] = None,
            model: Annotated[
                str | None,
                Field(description="Permission model name (for enforce action)"),
            ] = None,
            resource: Annotated[
                str | None,
                Field(description="Resource path (for enforce action)"),
            ] = None,
            permission_action: Annotated[
                str | None,
                Field(description="Permission action to check (for enforce action)"),
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
                model=model,
                resource=resource,
                permission_action=permission_action,
            )
