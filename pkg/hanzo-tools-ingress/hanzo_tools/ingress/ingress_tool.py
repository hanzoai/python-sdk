"""MCP tool for Traefik ingress inspection and PaaS domain management.

Traefik actions query the Traefik API for routers, services, middlewares,
entrypoints, and dashboard overview.  Domain actions use the PaaS API to
manage custom domains, verify DNS, and check TLS certificate status.

Auth: Uses HanzoSession from hanzo-tools-auth for authenticated API calls.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Annotated, final

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Traefik ingress inspection and PaaS domain management.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Traefik actions:
- routers: List HTTP routers
- services: List HTTP services
- middlewares: List middlewares
- entrypoints: List entrypoints
- overview: Dashboard overview stats
- tcp_routers: List TCP routers

Domain actions (PaaS):
- domains: List custom domains for a project
- add_domain: Add a custom domain (params: project_id, domain)
- remove_domain: Remove a custom domain (params: project_id, domain)
- verify_domain: Verify domain DNS (params: project_id, domain)
- tls_status: Get TLS certificate status (params: domain)
"""


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


@final
class IngressTool(BaseTool):
    """MCP tool for Traefik ingress and domain operations."""

    @property
    def name(self) -> str:
        return "ingress"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "overview",
        project_id: str | None = None,
        domain: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            # Traefik actions
            if action == "routers":
                return await self._routers()
            elif action == "services":
                return await self._services()
            elif action == "middlewares":
                return await self._middlewares()
            elif action == "entrypoints":
                return await self._entrypoints()
            elif action == "overview":
                return await self._overview()
            elif action == "tcp_routers":
                return await self._tcp_routers()
            # Domain actions
            elif action == "domains":
                return await self._domains(project_id)
            elif action == "add_domain":
                return await self._add_domain(project_id, domain)
            elif action == "remove_domain":
                return await self._remove_domain(project_id, domain)
            elif action == "verify_domain":
                return await self._verify_domain(project_id, domain)
            elif action == "tls_status":
                return await self._tls_status(domain)
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "routers", "services", "middlewares", "entrypoints",
                        "overview", "tcp_routers",
                        "domains", "add_domain", "remove_domain",
                        "verify_domain", "tls_status",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"Ingress tool error: {e}")
            return json.dumps({"error": f"Ingress error: {e}"})

    # -- Traefik actions -----------------------------------------------------

    async def _traefik_get(self, path: str) -> Any:
        """GET from the Traefik API via the PaaS gateway."""
        session = _get_session()
        paas = session.get_paas_client()
        return paas.get(f"/v1/ingress{path}")

    async def _routers(self) -> str:
        data = await self._traefik_get("/http/routers")
        routers = data if isinstance(data, list) else []
        result = []
        for r in routers:
            result.append({
                "name": r.get("name"),
                "rule": r.get("rule"),
                "service": r.get("service"),
                "entryPoints": r.get("entryPoints"),
                "status": r.get("status"),
                "tls": bool(r.get("tls")),
                "provider": r.get("provider"),
            })
        return json.dumps({"count": len(result), "routers": result}, indent=2)

    async def _services(self) -> str:
        data = await self._traefik_get("/http/services")
        services = data if isinstance(data, list) else []
        result = []
        for s in services:
            result.append({
                "name": s.get("name"),
                "type": s.get("type"),
                "status": s.get("status"),
                "provider": s.get("provider"),
                "servers": s.get("loadBalancer", {}).get("servers") if isinstance(s.get("loadBalancer"), dict) else None,
            })
        return json.dumps({"count": len(result), "services": result}, indent=2)

    async def _middlewares(self) -> str:
        data = await self._traefik_get("/http/middlewares")
        middlewares = data if isinstance(data, list) else []
        result = []
        for m in middlewares:
            result.append({
                "name": m.get("name"),
                "type": m.get("type"),
                "status": m.get("status"),
                "provider": m.get("provider"),
            })
        return json.dumps({"count": len(result), "middlewares": result}, indent=2)

    async def _entrypoints(self) -> str:
        data = await self._traefik_get("/entrypoints")
        entrypoints = data if isinstance(data, list) else []
        result = []
        for ep in entrypoints:
            result.append({
                "name": ep.get("name"),
                "address": ep.get("address"),
                "protocol": ep.get("protocol"),
            })
        return json.dumps({"count": len(result), "entrypoints": result}, indent=2)

    async def _overview(self) -> str:
        data = await self._traefik_get("/overview")
        return json.dumps(data, indent=2)

    async def _tcp_routers(self) -> str:
        data = await self._traefik_get("/tcp/routers")
        routers = data if isinstance(data, list) else []
        result = []
        for r in routers:
            result.append({
                "name": r.get("name"),
                "rule": r.get("rule"),
                "service": r.get("service"),
                "entryPoints": r.get("entryPoints"),
                "status": r.get("status"),
                "tls": bool(r.get("tls")),
            })
        return json.dumps({"count": len(result), "tcp_routers": result}, indent=2)

    # -- Domain actions (PaaS) -----------------------------------------------

    async def _domains(self, project_id: str | None) -> str:
        if not project_id:
            return json.dumps({"error": "Required: project_id"})

        session = _get_session()
        paas = session.get_paas_client()
        data = paas.get(f"/v1/project/{project_id}/domain")
        domains = data if isinstance(data, list) else []
        result = []
        for d in domains:
            result.append({
                "id": d.get("id"),
                "domain": d.get("domain"),
                "verified": d.get("verified"),
                "tls": d.get("tls"),
                "created_at": d.get("createdAt"),
            })
        return json.dumps({
            "project_id": project_id,
            "count": len(result),
            "domains": result,
        }, indent=2)

    async def _add_domain(self, project_id: str | None, domain: str | None) -> str:
        if not project_id or not domain:
            return json.dumps({"error": "Required: project_id and domain"})

        session = _get_session()
        paas = session.get_paas_client()
        result = paas.post(f"/v1/project/{project_id}/domain", json={"domain": domain})
        return json.dumps({
            "action": "add_domain",
            "project_id": project_id,
            "domain": domain,
            "result": result,
        }, indent=2)

    async def _remove_domain(self, project_id: str | None, domain: str | None) -> str:
        if not project_id or not domain:
            return json.dumps({"error": "Required: project_id and domain"})

        session = _get_session()
        paas = session.get_paas_client()
        result = paas.delete(f"/v1/project/{project_id}/domain/{domain}")
        return json.dumps({
            "action": "remove_domain",
            "project_id": project_id,
            "domain": domain,
            "result": result,
        }, indent=2)

    async def _verify_domain(self, project_id: str | None, domain: str | None) -> str:
        if not project_id or not domain:
            return json.dumps({"error": "Required: project_id and domain"})

        session = _get_session()
        paas = session.get_paas_client()
        result = paas.post(f"/v1/project/{project_id}/domain/{domain}/verify")
        return json.dumps({
            "action": "verify_domain",
            "project_id": project_id,
            "domain": domain,
            "result": result,
        }, indent=2)

    async def _tls_status(self, domain: str | None) -> str:
        if not domain:
            return json.dumps({"error": "Required: domain"})

        session = _get_session()
        paas = session.get_paas_client()
        result = paas.get(f"/v1/domain/{domain}/tls")
        return json.dumps({
            "domain": domain,
            "tls": result,
        }, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register ingress tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="ingress",
            description=DESCRIPTION,
        )
        async def ingress(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Traefik: routers, services, middlewares, entrypoints, overview, tcp_routers. "
                        "Domains: domains, add_domain, remove_domain, verify_domain, tls_status."
                    ),
                ),
            ] = "overview",
            project_id: Annotated[
                str | None,
                Field(description="Project ID (for domain actions)"),
            ] = None,
            domain: Annotated[
                str | None,
                Field(description="Domain name (for add_domain, remove_domain, verify_domain, tls_status)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                project_id=project_id,
                domain=domain,
            )
