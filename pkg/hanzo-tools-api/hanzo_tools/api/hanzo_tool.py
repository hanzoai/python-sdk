"""Unified Hanzo platform tool, projected from cloud's OpenAPI registry.

One MCP tool reaches every service cloud serves. The service/action surface is
derived from ``/v1/openapi.json`` at runtime rather than hand-listed here, so a
newly mounted app is callable the moment cloud serves it — no Python release,
and no list that silently drifts behind the platform.

One tool, not one per service: agents degrade badly with hundreds of tools, and
the spec already carries the routing information a dispatcher needs.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core import BaseTool, HanzoCloud, auto_timeout, create_tool_context

from . import spec as openapi

# Names that address the catalog itself rather than a cloud service.
CATALOG_SERVICES = frozenset({"services", "list"})
REFRESH_SERVICES = frozenset({"refresh", "reload"})

# Convenience synonyms for services whose product tag is not the obvious word.
SERVICE_ALIASES: dict[str, str] = {
    "identity": "iam",
    "payments": "billing",
    "knowledge": "kb",
    "platform": "paas",
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
            self._cloud = HanzoCloud()
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
        **kwargs: Any,
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        key = self._normalize(service)
        try:
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
            data = await self._get_cloud().call(route.method, route.path, query, body)
            return self._dump(
                {"service": key, "request": f"{route.method} {route.path}", "data": data}
            )
        except Exception as exc:
            return self._dump(self._error(key, exc))

    def _error(self, service: str, exc: Exception) -> dict[str, Any]:
        out: dict[str, Any] = {"error": str(exc), "service": service}
        if self._catalog is not None and service not in self._catalog.services:
            out["hint"] = 'call hanzo(service="services") to list services'
        return out

    @staticmethod
    def _dump(payload: dict[str, Any]) -> str:
        return json.dumps(payload, indent=2, default=str)

    def register(self, mcp_server: FastMCP) -> None:
        """Register the single unified hanzo tool."""
        tool_instance = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def hanzo(
            service: Annotated[
                str,
                Field(
                    description=(
                        "Product tag, e.g. billing, iam, kb, paas, git. "
                        'Use "services" to list them, "refresh" to refetch the spec.'
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
                str | None,
                Field(
                    description=(
                        "JSON object string. Body for POST/PUT/PATCH, else query "
                        'string. Example: "{\\"query\\":\\"oauth jwt\\"}"'
                    )
                ),
            ] = None,
            method: Annotated[
                str | None,
                Field(description="Override HTTP method (GET/POST/PUT/PATCH/DELETE)."),
            ] = None,
            ctx: MCPContext = None,  # type: ignore[assignment]
        ) -> str:
            return await tool_instance.call(
                ctx, service=service, action=action, params=params, method=method
            )
