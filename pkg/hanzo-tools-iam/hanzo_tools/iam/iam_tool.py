"""MCP tool for Hanzo IAM — identity and access management.

The caller of this tool is a language model, so the organization it acts in is
not a deployment constant: it is whatever identity the running agent holds.
There is therefore exactly ONE source for "which tenant am I" — IAM's own
`/v1/iam/whoami`, which resolves the token subject to the live user row and
returns the same `owner` IAM's authorization layer pins every request to
(internal/authz/authz.go `principal()`: `Org: u.Owner`).

Nothing else may name a tenant:

  - Not a literal. `owner or "hanzo"` is how an agent operating for one customer
    read another customer's users and reported them as its own.
  - Not configuration. Config names the tenant a PROCESS SERVES; the question
    here is which tenant the CALLER BELONGS TO. Different question.
  - Not the `owner` token claim (nor OIDC userinfo's `owner`, which echoes it).
    That claim names the APPLICATION's organization. IAM refuses to derive
    authority from it by name, because a tenant user signing in through a shared
    admin-org app would otherwise read as SuperAdmin.

A missing tenant is a REFUSAL, never a fallback.

Auth: the bearer stored by `hanzo login` (hanzo-tools-auth).
Backend: Hanzo IAM (HIP-0026) at IAM_URL, canonical surface under /v1/iam/.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Annotated, final

import httpx
from pydantic import Field
from mcp.server import FastMCP
from hanzo_iam.models import IAM_WHOAMI_PATH, IAM_ROUTE_PREFIX, OIDC_DISCOVERY_PATH
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

IAM_BASE_URL = os.getenv("IAM_URL", "https://hanzo.id")

DESCRIPTION = """Hanzo IAM — identity and access management.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Every listing is scoped to YOUR organization, resolved from your credential.
Pass `owner` only to name a DIFFERENT organization; IAM grants that only to a
superadmin and refuses it otherwise.

Identity:
- whoami: The organization and user this credential acts as

Users:
- users: List users (params: owner)
- user: Get a user (params: id, as org/username)
- create_user: Create a user (params: name, email, password, display_name, owner)
- update_user: Update a user (params: id, plus fields to update)
- delete_user: Delete a user (params: id)

Organizations:
- orgs: List organizations (params: owner)
- org: Get an organization (params: id)

Roles and permissions:
- roles: List roles (params: owner)
- role: Get a role (params: id)
- permissions: List permissions (params: owner)

Providers and applications:
- providers: List auth providers (params: owner)
- apps: List applications (params: owner)

Tokens and sessions:
- tokens: List tokens (params: owner)
- sessions: List sessions (params: owner)

Invitations:
- invitations: List invitations (params: owner)
- invite: Send an invitation (params: email, owner)

Audit and system:
- records: List audit records (params: owner)
- health: Is IAM reachable
"""


class IAMError(RuntimeError):
    """IAM answered, and the answer was a refusal or a failure."""


# --------------------------------------------------------------------------
# The one door to IAM.
# --------------------------------------------------------------------------


def _token() -> str | None:
    """The bearer this process holds, or None."""
    from hanzo_tools.auth.session import HanzoSession

    return HanzoSession.get().get_iam_token()


def _url(path: str) -> str:
    """Absolute URL for an IAM path.

    Paths are composed from hanzo_iam's IAM_ROUTE_PREFIX, never spelled here:
    hanzo.id answers 200 text/html on every unmatched path, so a wrong prefix
    fails inside .json() instead of failing like a wrong path.
    """
    return f"{IAM_BASE_URL}{path}"


async def _iam(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    auth: bool = True,
) -> Any:
    """Call IAM once and return its payload.

    The single request helper. It replaced three (`_iam_get`, `_iam_post` and
    an `_iam_delete` that issued a POST), and it unwraps both answer shapes IAM
    serves: the legacy `{status,msg,data}` envelope from the verb aliases, and
    the bare typed object from the REST surface. An envelope whose status is not
    "ok" is an error even though it arrives on HTTP 200 — that is IAM's contract
    (internal/httpx: "branch on status, not HTTP code"), and treating it as data
    is how a refusal gets reported as a result.
    """
    headers = {"Content-Type": "application/json", "User-Agent": "hanzo-mcp/0.1"}
    if auth:
        token = _token()
        if not token:
            raise IAMError("Not authenticated. Run 'hanzo login' first.")
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if body is None:
            resp = await client.get(_url(path), headers=headers, params=params)
        else:
            resp = await client.post(_url(path), headers=headers, json=body)
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            raise IAMError(
                f"{path} answered {resp.headers.get('content-type')} instead of JSON"
                " — the request reached a web page, not the API."
            )
        payload = resp.json()

    if isinstance(payload, dict) and "status" in payload:
        if payload.get("status") != "ok":
            raise IAMError(payload.get("msg") or "IAM refused the request")
        return payload.get("data")
    return payload


async def _principal() -> dict[str, Any]:
    """Ask IAM which organization this credential acts in.

    The ONE tenant resolution. `_iam` raises on the anonymous answer
    ({"status":"error","msg":"please sign in first"}), which is exactly the
    behaviour required: no principal is a refusal, not a default.
    """
    data = await _iam(IAM_WHOAMI_PATH)
    owner = (data or {}).get("owner")
    if not owner:
        raise IAMError(
            "IAM did not report an organization for this credential."
            " Run 'hanzo login' — there is no default tenant."
        )
    return data


async def _owner(requested: str | None) -> str:
    """The organization to scope a read to.

    An explicitly named organization is sent as given: IAM honours it for a
    superadmin and refuses it for everyone else (authz.Scope, honour-or-refuse).
    Dropping it client-side would turn a deliberate cross-tenant read into a
    silently reinterpreted one. Otherwise the caller's own organization — and
    sending it is not optional even though an omitted owner would also scope a
    non-super correctly, because for a SUPERADMIN an omitted owner means EVERY
    tenant, returned as though it were the caller's own.
    """
    return requested or (await _principal())["owner"]


# --------------------------------------------------------------------------
# The action table. Every listing is (path, payload key, projected fields).
# --------------------------------------------------------------------------

P = IAM_ROUTE_PREFIX

# Verb-alias listings: owner in the query, rows in the envelope's `data`.
_LISTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "users": (f"{P}/get-users", ("id", "name", "email", "displayName", "createdTime")),
    "orgs": (f"{P}/get-organizations", ("name", "displayName", "websiteUrl", "createdTime")),
    "roles": (f"{P}/get-roles", ("name", "displayName", "users", "roles")),
    "permissions": (f"{P}/get-permissions", ("name", "displayName", "resources", "actions", "effect")),
    "providers": (f"{P}/get-providers", ("name", "displayName", "type", "category")),
    "apps": (f"{P}/get-applications", ("name", "displayName", "organization", "clientId")),
    "invitations": (f"{P}/get-invitations", ("name", "email", "state", "createdTime")),
    "records": (f"{P}/get-records", ("name", "method", "requestUri", "action", "createdTime", "user", "ip")),
}

# Typed listings: the verb-alias layer does not cover these two, so they use the
# REST surface, which answers with a named collection instead of an envelope.
_TYPED_LISTS: dict[str, tuple[str, str, str, tuple[str, ...]]] = {
    "tokens": ("GET", f"{P}/tokens", "tokens", ("name", "owner", "user", "application", "createdTime", "expiresIn")),
    "sessions": ("POST", f"{P}/sessions/list", "sessions", ("name", "owner", "application", "createdTime", "sessionId")),
}

# Single reads: `?id=<owner>/<name>`. IAM re-scopes the id it is given, so a
# foreign org in `id` is refused rather than answered.
_GETS: dict[str, tuple[str, str]] = {
    "user": (f"{P}/get-user", "user ID (org/username)"),
    "org": (f"{P}/get-organization", "organization ID (org-owner/org-name)"),
    "role": (f"{P}/get-role", "role ID (org/role-name)"),
}


def _project(row: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {f: row.get(f) for f in fields} if isinstance(row, dict) else {"value": row}


def _one_tenant(rows: list[Any], org: str) -> None:
    """Refuse an answer that is not the tenant that was asked for.

    The typed REST listers cannot be scoped by a query parameter: a zip typed
    GET binds NOTHING from the request (a body is read only for non-GET), so
    /v1/iam/tokens?owner=X reaches its handler with an EMPTY owner and falls
    through to authz.Scope(ctx, "") — which pins a normal user to its own org
    but hands a SUPERADMIN every tenant's rows. `?owner=` is still sent, and
    still load-bearing: the Guard pre-authorizes the read from the query string
    (authz.ReadTarget), so it is what refuses a foreign org. It just does not
    FILTER.

    So the request is authorized but the answer may be wider than it, and
    labelling that wider answer with one org name is the whole bug this tool
    exists to not have. A row from somewhere else is a refusal, never a row.
    """
    strays = sorted({
        r["owner"] for r in rows
        if isinstance(r, dict) and r.get("owner") and r["owner"] != org
    })
    if strays:
        raise IAMError(
            f"IAM answered with rows from {', '.join(strays)} for a read scoped to"
            f" {org}; refusing rather than reporting another tenant's rows as {org}'s."
        )


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
        **kwargs: Any,
    ) -> str:
        try:
            if action == "health":
                return await self._health()
            if action == "whoami":
                return json.dumps(await _principal(), indent=2)
            if action in _LISTS:
                return await self._list(action, owner)
            if action in _TYPED_LISTS:
                return await self._typed_list(action, owner)
            if action in _GETS:
                return await self._get(action, id)
            if action == "create_user":
                return await self._create_user(owner, name, email, password, display_name)
            if action == "update_user":
                return await self._update_user(id, name, email, display_name, **kwargs)
            if action == "delete_user":
                return await self._delete_user(id)
            if action == "invite":
                return await self._invite(email, owner)

            return json.dumps({
                "error": f"Unknown action: {action}",
                "available": sorted(
                    ["health", "whoami", "create_user", "update_user", "delete_user", "invite"]
                    + list(_LISTS) + list(_TYPED_LISTS) + list(_GETS)
                ),
            })
        except IAMError as e:
            return json.dumps({"error": str(e)})
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            try:
                detail = e.response.json()
            except ValueError:
                pass
            return json.dumps({"error": f"IAM API error {e.response.status_code}", "detail": detail})
        except Exception as e:
            logger.exception("IAM tool error: %s", e)
            return json.dumps({"error": f"IAM error: {e}"})

    # -- Listings ------------------------------------------------------------

    async def _list(self, action: str, owner: str | None) -> str:
        path, fields = _LISTS[action]
        org = await _owner(owner)
        rows = await _iam(path, params={"owner": org}) or []
        return json.dumps({
            "owner": org,
            "count": len(rows),
            action: [_project(r, fields) for r in rows],
        }, indent=2)

    async def _typed_list(self, action: str, owner: str | None) -> str:
        method, path, key, fields = _TYPED_LISTS[action]
        org = await _owner(owner)
        if method == "GET":
            payload = await _iam(path, params={"owner": org})
        else:
            payload = await _iam(path, body={"owner": org})
        rows = (payload or {}).get(key) or []
        _one_tenant(rows, org)
        return json.dumps({
            "owner": org,
            "count": len(rows),
            action: [_project(r, fields) for r in rows],
        }, indent=2)

    async def _get(self, action: str, id: str | None) -> str:
        path, described = _GETS[action]
        if not id:
            return json.dumps({"error": f"Required: id ({described})"})
        return json.dumps(await _iam(path, params={"id": id}), indent=2)

    # -- Users ---------------------------------------------------------------
    #
    # The write verbs take the user's fields at TOP LEVEL (iam's `userBody`
    # embeds schema.User), NOT the REST twin's {user, password} envelope. Go
    # decodes an object with no matching keys into a ZERO struct, so the wrapped
    # form arrives addressing owner "" / name "" — and authorization runs on the
    # DECODED input, which means the request IAM judges is not the one the agent
    # wrote. Delete reads its key (in.Owner, in.Name) off the same bare body.

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

        body: dict[str, Any] = {
            "owner": await _owner(owner),
            "name": name,
            "email": email,
            "displayName": display_name or name,
        }
        if password:
            # A sibling of the user's fields, never a column on the user: IAM
            # hands it to the ONE users.Create path, which hashes it and stores
            # no plaintext (internal/compat writes.go `userBody`).
            body["password"] = password
        return json.dumps({"action": "created", "result": await _iam(f"{P}/add-user", body=body)}, indent=2)

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

        current = await _iam(f"{P}/get-user", params={"id": id})
        if not isinstance(current, dict):
            return json.dumps({"error": f"User not found: {id}"})

        for key, value in (("name", name), ("email", email), ("displayName", display_name)):
            if value is not None:
                current[key] = value
        for key, value in kwargs.items():
            if value is not None:
                current[key] = value

        result = await _iam(f"{P}/update-user", body=current)
        return json.dumps({"action": "updated", "id": id, "result": result}, indent=2)

    async def _delete_user(self, id: str | None) -> str:
        if not id:
            return json.dumps({"error": "Required: id (user ID, format: org/username)"})

        current = await _iam(f"{P}/get-user", params={"id": id})
        if not isinstance(current, dict):
            return json.dumps({"error": f"User not found: {id}"})

        result = await _iam(f"{P}/delete-user", body=current)
        return json.dumps({"action": "deleted", "id": id, "result": result}, indent=2)

    # -- Invitations ---------------------------------------------------------

    async def _invite(self, email: str | None, owner: str | None) -> str:
        if not email:
            return json.dumps({"error": "Required: email. Optional: owner"})

        # An invitation's owner IS the organization joined; there is no separate
        # organization field on the entity.
        invitation = {
            "owner": await _owner(owner),
            "name": email.replace("@", "-at-").replace(".", "-"),
            "email": email,
        }
        result = await _iam(f"{P}/invitations", body=invitation)
        return json.dumps({"action": "invited", "email": email, "result": result}, indent=2)

    # -- Health --------------------------------------------------------------

    async def _health(self) -> str:
        """Probe IAM's public OIDC discovery document.

        The probe this replaced sent no credential to /v1/iam/healthz, which is
        behind IAM's Guard and answers 401 — so `iam health` reported "error"
        against a perfectly healthy IAM. `/healthz` is registered at the ROOT,
        where hanzo.id's sign-in SPA answers 200 text/html first. Discovery is
        the public, JSON, standards-defined liveness surface of an identity
        provider, and requiring `issuer` proves an IAM answered rather than a
        web page with an agreeable status code.
        """
        try:
            doc = await _iam(OIDC_DISCOVERY_PATH, auth=False)
        except (IAMError, httpx.HTTPError, ValueError) as e:
            return json.dumps({"status": "error", "error": str(e), "url": IAM_BASE_URL})
        healthy = isinstance(doc, dict) and bool(doc.get("issuer"))
        return json.dumps({
            "status": "ok" if healthy else "error",
            "url": IAM_BASE_URL,
            "issuer": doc.get("issuer") if isinstance(doc, dict) else None,
        }, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register the IAM tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(name="iam", description=DESCRIPTION)
        async def iam(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Identity: whoami. "
                        "Users: users, user, create_user, update_user, delete_user. "
                        "Orgs: orgs, org. "
                        "Roles: roles, role, permissions. "
                        "Auth: providers, apps, tokens, sessions. "
                        "Invitations: invitations, invite. "
                        "System: records, health."
                    ),
                ),
            ] = "health",
            id: Annotated[
                str | None,
                Field(description="Entity ID (format: org/name for users, roles, etc.)"),
            ] = None,
            owner: Annotated[
                str | None,
                Field(
                    description=(
                        "Organization to act in. Defaults to YOUR organization,"
                        " resolved from your credential. Naming a different one"
                        " is granted only to a superadmin."
                    ),
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
                Field(description="Password for user creation"),
            ] = None,
            display_name: Annotated[
                str | None,
                Field(description="Display name for create/update operations"),
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
            )
