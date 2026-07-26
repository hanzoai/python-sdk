"""MCP tool for Hanzo KMS secret management.

Wraps the hanzo-kms client to provide secret CRUD operations via MCP. A
secret is (org, path, name, env): the org comes from HANZO_KMS_ORG, and auth
from HANZO_KMS_CLIENT_ID / HANZO_KMS_CLIENT_SECRET (or HANZO_KMS_TOKEN) —
the same pattern as hanzo-cli.
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

DEFAULT_ENV = "default"

DESCRIPTION = """Manage secrets via Hanzo KMS.

Requires HANZO_KMS_CLIENT_ID and HANZO_KMS_CLIENT_SECRET (or HANZO_KMS_TOKEN)
environment variables. HANZO_KMS_ORG selects the organization (default: hanzo).

A secret is identified by path + name + env, e.g. path="providers/lux",
name="deploy-mnemonic", env="prod".

Actions:
- list: List the secret names at a path
- get: Get a single secret value (masked unless reveal=true)
- set: Create or replace a secret
- delete: Remove a secret
- inject: Output every secret at a path as export/dotenv/json
"""


def _get_kms_client() -> Any:
    """Build a KMS client from the environment.

    KMSClient() reads HANZO_KMS_URL / _ORG / _CLIENT_ID / _CLIENT_SECRET /
    _TOKEN itself — see hanzo_kms.settings_from_env.
    """
    from hanzo_kms import KMSClient

    return KMSClient()


def _masked(value: str) -> str:
    return f"{value[:4]}***" if len(value) > 4 else "***"


@final
class KMSTool(BaseTool):
    """MCP tool for KMS secret management."""

    @property
    def name(self) -> str:
        return "kms"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "list",
        path: str = "",
        name: str | None = None,
        value: str | None = None,
        env: str = DEFAULT_ENV,
        format: str = "export",
        reveal: bool = False,
        **kwargs: Any,
    ) -> str:
        if action == "list":
            return await self._list(path, env)
        elif action == "get":
            return await self._get(path, name, env, reveal)
        elif action == "set":
            return await self._set(path, name, value, env)
        elif action == "delete":
            return await self._delete(path, name, env)
        elif action == "inject":
            return await self._inject(path, env, format)
        return json.dumps(
            {"error": f"Unknown action: {action}. Use: list, get, set, delete, inject"}
        )

    async def _list(self, path: str, env: str) -> str:
        client = _get_kms_client()
        try:
            names = client.list_secrets(path, env)
        finally:
            client.close()

        return json.dumps(
            {"path": path, "env": env, "count": len(names), "names": names}, indent=2
        )

    async def _get(self, path: str, name: str | None, env: str, reveal: bool) -> str:
        if not name:
            return json.dumps({"error": "Required: name"})

        client = _get_kms_client()
        try:
            value = client.get_secret(path, name, env)
        finally:
            client.close()

        return json.dumps(
            {
                "path": path,
                "name": name,
                "env": env,
                "value": value if reveal else _masked(value),
                "revealed": reveal,
            },
            indent=2,
        )

    async def _set(self, path: str, name: str | None, value: str | None, env: str) -> str:
        if not name or value is None:
            return json.dumps({"error": "Required: name and value"})

        client = _get_kms_client()
        try:
            # One upsert — KMS holds exactly one value per (path, name, env).
            client.put_secret(path, name, value, env)
        finally:
            client.close()

        return json.dumps({"action": "set", "path": path, "name": name, "env": env})

    async def _delete(self, path: str, name: str | None, env: str) -> str:
        if not name:
            return json.dumps({"error": "Required: name"})

        client = _get_kms_client()
        try:
            client.delete_secret(path, name, env)
        finally:
            client.close()

        return json.dumps({"action": "deleted", "path": path, "name": name, "env": env})

    async def _inject(self, path: str, env: str, fmt: str) -> str:
        client = _get_kms_client()
        try:
            # One list plus one read per name — the list route returns names.
            values = {
                name: client.get_secret(path, name, env)
                for name in client.list_secrets(path, env)
            }
        finally:
            client.close()

        if not values:
            return json.dumps({"message": "No secrets found", "output": ""})

        if fmt == "json":
            return json.dumps(values, indent=2)

        lines = []
        for name, value in values.items():
            if fmt == "dotenv":
                dotenv_safe = value.replace('"', '\\"')
                lines.append(f'{name}="{dotenv_safe}"')
            else:  # export
                shell_safe = value.replace("'", "'\\''")
                lines.append(f"export {name}='{shell_safe}'")
        return "\n".join(lines)

    def register(self, mcp_server: FastMCP) -> None:
        """Register KMS tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="kms",
            description=DESCRIPTION,
        )
        async def kms(
            action: Annotated[
                str,
                Field(description="Action: list, get, set, delete, inject"),
            ] = "list",
            path: Annotated[
                str,
                Field(description="Secret path, e.g. providers/lux"),
            ] = "",
            name: Annotated[
                str | None,
                Field(description="Secret name (for get/set/delete). No slashes."),
            ] = None,
            value: Annotated[
                str | None,
                Field(description="Secret value (for set)"),
            ] = None,
            env: Annotated[
                str,
                Field(description="Environment bucket, e.g. dev, prod"),
            ] = DEFAULT_ENV,
            format: Annotated[
                str,
                Field(description="Output format for inject: export, dotenv, json"),
            ] = "export",
            reveal: Annotated[
                bool,
                Field(description="Show full secret value (default: masked)"),
            ] = False,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                path=path,
                name=name,
                value=value,
                env=env,
                format=format,
                reveal=reveal,
            )
