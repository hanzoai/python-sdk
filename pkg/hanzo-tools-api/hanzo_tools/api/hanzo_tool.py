"""Unified Hanzo platform tool.

Provides a compact `hanzo` surface that routes to Hanzo service tools
(`auth`, `billing`, `commerce`, `iam`, `ingress`, `kms`, `mpc`, `paas`,
`team`, and generic `api`).
"""

from __future__ import annotations

import importlib
import inspect
import json
from typing import Annotated, Any, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

SERVICE_TOOL_PATHS: dict[str, str] = {
    "api": "hanzo_tools.api.api_tool:APITool",
    "auth": "hanzo_tools.auth.login_tool:LoginTool",
    "billing": "hanzo_tools.billing.billing_tool:BillingTool",
    "commerce": "hanzo_tools.commerce.commerce_tool:CommerceTool",
    "iam": "hanzo_tools.iam.iam_tool:IAMTool",
    "ingress": "hanzo_tools.ingress.ingress_tool:IngressTool",
    "kms": "hanzo_tools.kms.kms_tool:KMSTool",
    "mpc": "hanzo_tools.mpc.mpc_tool:MPCTool",
    "paas": "hanzo_tools.paas.paas_tool:PaaSTool",
    "team": "hanzo_tools.team.team_tool:TeamTool",
}

SERVICE_ALIASES: dict[str, str] = {
    "platform": "paas",
    "identity": "iam",
    "payments": "billing",
    "store": "commerce",
}


@final
class HanzoTool(BaseTool):
    """Unified tool for Hanzo platform services."""

    name = "hanzo"

    def __init__(self) -> None:
        self._delegates: dict[str, BaseTool] = {}

    @property
    @override
    def description(self) -> str:
        return """Unified Hanzo platform tool.

Use one `hanzo` tool surface for service operations across:
- auth
- billing
- commerce
- iam
- ingress
- kms
- mpc
- paas
- team
- api (generic OpenAPI bridge)

Parameters:
- service: Target Hanzo service
- action: Service-specific action
- args: JSON object string for service-specific parameters

Examples:
  hanzo(service="auth", action="status")
  hanzo(service="commerce", action="orders")
  hanzo(service="iam", action="users", args='{"owner":"hanzo"}')
  hanzo(service="api", action="list")
"""

    def _normalize_service(self, service: str) -> str:
        key = (service or "").strip().lower().replace("-", "_")
        key = SERVICE_ALIASES.get(key, key)
        return key

    def _load_delegate(self, service: str) -> BaseTool:
        if service in self._delegates:
            return self._delegates[service]

        path = SERVICE_TOOL_PATHS.get(service)
        if not path:
            available = ", ".join(sorted(SERVICE_TOOL_PATHS.keys()))
            raise ValueError(
                f"Unknown service '{service}'. Available services: {available}"
            )

        module_name, class_name = path.split(":")
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        tool = cls()
        self._delegates[service] = tool
        return tool

    def _parse_args(self, args: str | None) -> dict[str, Any]:
        if not args:
            return {}
        try:
            parsed = json.loads(args)
        except json.JSONDecodeError as exc:
            raise ValueError(f"args must be valid JSON object string: {exc}") from exc

        if not isinstance(parsed, dict):
            raise ValueError("args must decode to a JSON object")
        return parsed

    async def _delegate_call(
        self,
        tool: BaseTool,
        ctx: MCPContext,
        payload: dict[str, Any],
    ) -> str:
        sig = inspect.signature(tool.call)
        params = sig.parameters
        accepts_kwargs = any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
        )

        if accepts_kwargs:
            return await tool.call(ctx, **payload)

        allowed = {
            name
            for name, param in params.items()
            if name not in {"self", "ctx"}
            and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }
        filtered = {k: v for k, v in payload.items() if k in allowed}
        return await tool.call(ctx, **filtered)

    @override
    @auto_timeout("hanzo")
    async def call(
        self,
        ctx: MCPContext,
        service: str = "api",
        action: str = "list",
        args: str | None = None,
        **kwargs: Any,
    ) -> str:
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        service_key = self._normalize_service(service)
        if service_key in {"services", "list"}:
            return json.dumps(
                {
                    "services": sorted(SERVICE_TOOL_PATHS.keys()),
                    "aliases": SERVICE_ALIASES,
                    "usage": 'hanzo(service="commerce", action="orders", args="{\\"query\\":\\"...\\\"}")',
                },
                indent=2,
            )

        try:
            delegate = self._load_delegate(service_key)
            payload = {"action": action}
            payload.update(self._parse_args(args))
            payload.update({k: v for k, v in kwargs.items() if v is not None})
            return await self._delegate_call(delegate, ctx, payload)
        except Exception as exc:
            return json.dumps(
                {
                    "error": str(exc),
                    "service": service_key,
                    "available_services": sorted(SERVICE_TOOL_PATHS.keys()),
                },
                indent=2,
            )

    def register(self, mcp_server: FastMCP) -> None:
        """Register unified hanzo tool with explicit compact params."""
        tool_instance = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def hanzo(
            service: Annotated[
                str,
                Field(
                    description=(
                        "Target service: api, auth, billing, commerce, iam, ingress, "
                        "kms, mpc, paas, team. Use 'services' to list."
                    )
                ),
            ] = "api",
            action: Annotated[
                str,
                Field(description="Service action to execute (service-specific)."),
            ] = "list",
            args: Annotated[
                str | None,
                Field(
                    description=(
                        "JSON object string with service-specific parameters. "
                        'Example: "{\\"query\\":\\"foo\\",\\"owner\\":\\"hanzo\\"}"'
                    )
                ),
            ] = None,
            ctx: MCPContext = None,  # type: ignore[assignment]
        ) -> str:
            return await tool_instance.call(ctx, service=service, action=action, args=args)
