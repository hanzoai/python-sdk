"""Unified Hanzo platform tool, projected from cloud's OpenAPI registry.

One MCP tool reaches every service cloud serves. The service/action surface is
derived from ``/v1/openapi.json`` at runtime rather than hand-listed here, so a
newly mounted app is callable the moment cloud serves it — no Python release,
and no list that silently drifts behind the platform.

One tool, not one per service: agents degrade badly with hundreds of tools, and
the spec already carries the routing information a dispatcher needs.

Who it acts as is ``hanzo_login``'s answer, shared with every Hanzo tool on the machine:
``HANZO_API_KEY``, then the ``hanzo`` CLI's login, then the legacy stored key. A call can
name another account (``as``) or org (``org``), and ``service="auth"`` is answered locally.
"""

from __future__ import annotations

import functools
import json
from importlib import metadata
from typing import Annotated, Any, final, override

import hanzo_login as login
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core import BaseTool, HanzoCloud, auto_timeout, create_tool_context

from . import spec as openapi

try:
    AGENT = f"hanzo-tools-api/{metadata.version('hanzo-tools-api')}"
except metadata.PackageNotFoundError:
    AGENT = "hanzo-tools-api/source"

# Names that address the catalog itself rather than a cloud service.
CATALOG_SERVICES = frozenset({"services", "list"})
REFRESH_SERVICES = frozenset({"refresh", "reload"})
# Answered here, through the login, never sent to the cloud.
AUTH_SERVICES = frozenset({"auth"})

# Synonyms for a product tag that is not the obvious word. They may only point AT
# a name the fleet serves — `platform -> paas` and `identity -> iam` pointed at
# names it had left behind, so they mapped a caller off the live surface. One
# thing, one name; a synonym that renames is a second name.
SERVICE_ALIASES: dict[str, str] = {
    "knowledge": "kb",
    "rag": "kb",
}


@final
class HanzoTool(BaseTool):
    """Unified tool for every Hanzo cloud service."""

    name = "hanzo"

    def __init__(self) -> None:
        self._catalog: openapi.Catalog | None = None
        self._source: str = ""
        self._cloud: HanzoCloud | None = None

    @property
    @override
    def description(self) -> str:
        return """Unified Hanzo platform tool — every service cloud serves.

The service/action surface is generated from cloud's live OpenAPI registry, so
it always matches what the platform actually serves.

Parameters:
- service: Product tag (the first path segment after /v1/). "services" lists them.
- action: Path within the service ("plans" -> /v1/billing/plans). Omit to list
  a service's actions.
- params: JSON object string; sent as the body for POST/PUT/PATCH, else as the
  query string. Values also fill {templated} path segments.
- method: Override the HTTP method when an action serves several.
- as: Act as this identity (owner or owner/name) for this call, whatever key is set.
- org: Act in this org (sent as X-Org-Id); an operation's own `org` goes inside params.

Who you are (answered locally): service="auth", action whoami | list | use | switch.
  hanzo(service="auth", action="whoami")
  hanzo(service="auth", action="use", params='{"identity":"lux/ops"}')     this process only
  hanzo(service="auth", action="switch", params='{"identity":"lux/ops"}')  the whole machine

Examples:
  hanzo(service="services")
  hanzo(service="billing")
  hanzo(service="billing", action="plans")
  hanzo(service="kb", action="search", params='{"query":"authentication oauth jwt"}')
  hanzo(service="refresh")
"""

    def _get_catalog(self, refresh: bool = False) -> openapi.Catalog:
        if self._catalog is None or refresh:
            document, source = openapi.load(refresh=refresh)
            self._catalog = openapi.Catalog(document)
            self._source = source
        return self._catalog

    def _get_cloud(self) -> HanzoCloud:
        if self._cloud is None:
            self._cloud = HanzoCloud(agent=AGENT)
        return self._cloud

    @staticmethod
    def _normalize(service: str) -> str:
        key = (service or "").strip().lower()
        return SERVICE_ALIASES.get(key, key)

    @staticmethod
    def _parse_params(params: str | None) -> dict[str, Any]:
        if not params:
            return {}
        try:
            parsed = json.loads(params)
        except json.JSONDecodeError as exc:
            raise ValueError(f"params must be a JSON object string: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("params must decode to a JSON object")
        return parsed

    @override
    @auto_timeout("hanzo")
    async def call(
        self,
        ctx: MCPContext,
        service: str = "services",
        action: str = "",
        params: str | dict[str, Any] | None = None,
        method: str | None = None,
        org: str | None = None,
        **kwargs: Any,
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        identity = kwargs.pop("as", None)
        key = self._normalize(service)
        try:
            if key in AUTH_SERVICES:
                supplied = params if isinstance(params, dict) else self._parse_params(params)
                return self._dump(self._auth(action, supplied, identity))

            if key in REFRESH_SERVICES:
                catalog = self._get_catalog(refresh=True)
                return self._dump(
                    {
                        "refreshed": True,
                        "source": self._source,
                        "services": len(catalog.services),
                    }
                )

            catalog = self._get_catalog()

            if key in CATALOG_SERVICES:
                summary = catalog.summary()
                return self._dump(
                    {
                        "source": self._source,
                        "count": len(summary),
                        "services": summary,
                        "usage": 'hanzo(service="billing", action="plans")',
                    }
                )

            supplied = params if isinstance(params, dict) else self._parse_params(params)
            supplied = {**supplied, **{k: v for k, v in kwargs.items() if v is not None}}

            if not action:
                return self._dump(catalog.describe(key))

            route = catalog.resolve(key, action, method, has_params=bool(supplied))
            query, body = openapi.split_params(route, supplied)
            data = await self._get_cloud().call(
                route.method, route.path, query, body, identity=identity, org=org
            )
            return self._dump(
                {"service": key, "request": f"{route.method} {route.path}", "data": data}
            )
        except Exception as exc:
            return self._dump(self._error(key, exc))

    @staticmethod
    def _auth(action: str, params: dict[str, Any], identity: str | None) -> dict[str, Any]:
        """Who this process acts as. The CLI answers; no token or key is ever returned."""
        what = (action or "whoami").strip().lower()
        if what == "whoami":
            return login.describe(identity)
        if what == "list":
            rows = login.identities()
            active = next((r["key"] for r in rows if r.get("active")), None)
            return {"identities": rows, "active": active, "using": login.using()}
        if what == "use":
            target = params.get("identity") or None
            login.use(target)
            if target is None:
                return {"using": None, "message": "Cleared: this process acts as the CLI's active identity again."}
            return {
                "using": target,
                "scope": "process",
                "message": f"This process only: it now acts as {target}. Other Hanzo tools and sessions "
                "on this machine are unchanged; `switch` changes the whole machine.",
            }
        if what == "switch":
            target = params.get("identity")
            if not target:
                raise ValueError('switch needs params {"identity": "owner/name"}')
            login.switch(target)
            return {
                "active": target,
                "scope": "machine",
                "message": f"GLOBAL: every Hanzo tool and session on this machine now acts as {target}, "
                "the CLI's active identity (a running tool follows within 5 minutes).",
            }
        raise ValueError(f"unknown auth action {action!r}; use whoami, list, use or switch")

    def _error(self, service: str, exc: Exception) -> dict[str, Any]:
        out: dict[str, Any] = {"error": str(exc), "service": service}
        if service not in AUTH_SERVICES and self._catalog is not None and service not in self._catalog.services:
            out["hint"] = 'call hanzo(service="services") to list services'
        return out

    @staticmethod
    def _dump(payload: dict[str, Any]) -> str:
        return json.dumps(payload, indent=2, default=str)

    def register(self, mcp_server: FastMCP) -> None:
        """Register the single unified hanzo tool."""
        tool_instance = self

        async def hanzo(
            service: Annotated[
                str,
                Field(
                    description=(
                        "Product tag, e.g. billing, iam, kb, paas, git. "
                        'Use "services" to list them, "refresh" to refetch the spec, '
                        '"auth" for who you are (whoami, list, use, switch).'
                    )
                ),
            ] = "services",
            action: Annotated[
                str,
                Field(
                    description=(
                        "Path within the service, e.g. 'plans' for "
                        "/v1/billing/plans. Omit to list the service's actions."
                    )
                ),
            ] = "",
            params: Annotated[
                str | dict[str, Any] | None,
                Field(
                    description=(
                        "JSON object (or its string). Body for POST/PUT/PATCH, else "
                        'query string. Example: {"query": "oauth jwt"}'
                    )
                ),
            ] = None,
            method: Annotated[
                str | None,
                Field(description="Override HTTP method (GET/POST/PUT/PATCH/DELETE)."),
            ] = None,
            as_: Annotated[
                str | None,
                Field(
                    alias="as",
                    description="Act as this identity (owner or owner/name) for this call.",
                ),
            ] = None,
            org: Annotated[
                str | None,
                Field(
                    description=(
                        "Act in this org (X-Org-Id). An operation's own `org` "
                        "parameter goes inside params."
                    )
                ),
            ] = None,
            ctx: MCPContext = None,  # type: ignore[assignment]
        ) -> str: ...

        # `as` is a keyword, so `hanzo` declares the schema with `as_` aliased to "as"; the
        # call arrives keyed "as" and is taken whole.
        @functools.wraps(hanzo)
        async def serve(**arguments: Any) -> str:
            return await tool_instance.call(arguments.pop("ctx", None), **arguments)

        mcp_server.tool(name=self.name, description=self.description)(serve)
