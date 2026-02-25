"""MCP tool for Hanzo KMS secret management.

Wraps the hanzo-kms client to provide secret CRUD operations
via MCP. Auth uses HANZO_KMS_CLIENT_ID / HANZO_KMS_CLIENT_SECRET
environment variables (same pattern as hanzo-cli).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, final

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Manage secrets via Hanzo KMS.

Requires HANZO_KMS_CLIENT_ID and HANZO_KMS_CLIENT_SECRET environment variables.

Actions:
- list: List all secrets in a project/environment (values masked)
- get: Get a single secret value
- set: Create or update a secret
- delete: Remove a secret
- inject: Output secrets as export/dotenv/json format
"""


def _get_kms_client() -> Any:
    """Build a KMS client from environment."""
    from hanzo_kms import ClientSettings, KMSClient

    kms_url = os.getenv("HANZO_KMS_URL", "https://kms.hanzo.ai")
    client_id = os.getenv("HANZO_KMS_CLIENT_ID", "")
    client_secret = os.getenv("HANZO_KMS_CLIENT_SECRET", "")

    if client_id and client_secret:
        from hanzo_kms import AuthenticationOptions, UniversalAuthMethod

        settings = ClientSettings(
            site_url=kms_url,
            auth=AuthenticationOptions(
                universal_auth=UniversalAuthMethod(
                    client_id=client_id,
                    client_secret=client_secret,
                )
            ),
        )
        return KMSClient(settings=settings)

    # Fall back to default env-based construction
    return KMSClient()


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
        project: str | None = None,
        environment: str | None = None,
        secret_name: str | None = None,
        secret_value: str | None = None,
        path: str = "/",
        format: str = "export",
        reveal: bool = False,
        **kwargs: Any,
    ) -> str:
        if action == "list":
            return await self._list(project, environment, path)
        elif action == "get":
            return await self._get(project, environment, secret_name, path, reveal)
        elif action == "set":
            return await self._set(project, environment, secret_name, secret_value, path)
        elif action == "delete":
            return await self._delete(project, environment, secret_name, path)
        elif action == "inject":
            return await self._inject(project, environment, path, format)
        else:
            return json.dumps({"error": f"Unknown action: {action}. Use: list, get, set, delete, inject"})

    async def _list(self, project: str | None, env: str | None, path: str) -> str:
        if not project or not env:
            return json.dumps({"error": "Required: project and environment"})

        client = _get_kms_client()
        try:
            secrets = client.list_secrets(project_id=project, environment=env, path=path)
        finally:
            client.close()

        if not secrets:
            return json.dumps({"message": f"No secrets found in {project}/{env}", "secrets": []})

        rows = []
        for s in secrets:
            val = s.secret_value
            masked = f"{val[:4]}***" if len(val) > 4 else "***"
            rows.append({
                "key": s.secret_key,
                "value": masked,
                "version": s.version,
                "updated": str(s.updated_at)[:19] if s.updated_at else None,
            })

        return json.dumps({
            "project": project,
            "environment": env,
            "path": path,
            "count": len(rows),
            "secrets": rows,
        }, indent=2)

    async def _get(
        self, project: str | None, env: str | None, name: str | None, path: str, reveal: bool
    ) -> str:
        if not project or not env or not name:
            return json.dumps({"error": "Required: project, environment, and secret_name"})

        client = _get_kms_client()
        try:
            secret = client.get_secret(
                project_id=project, environment=env, secret_name=name, path=path
            )
        finally:
            client.close()

        val = secret.secret_value
        if not reveal:
            val = f"{val[:4]}***" if len(val) > 4 else "***"

        return json.dumps({
            "key": secret.secret_key,
            "value": val,
            "version": secret.version,
            "type": secret.type,
            "environment": secret.environment,
            "comment": secret.secret_comment or None,
            "revealed": reveal,
        }, indent=2)

    async def _set(
        self, project: str | None, env: str | None, name: str | None, value: str | None, path: str
    ) -> str:
        if not project or not env or not name or not value:
            return json.dumps({"error": "Required: project, environment, secret_name, and secret_value"})

        client = _get_kms_client()
        try:
            # Try update first, create if it doesn't exist
            try:
                secret = client.update_secret(
                    project_id=project,
                    environment=env,
                    secret_name=name,
                    secret_value=value,
                )
                return json.dumps({
                    "action": "updated",
                    "key": name,
                    "version": secret.version,
                })
            except Exception:
                secret = client.create_secret(
                    project_id=project,
                    environment=env,
                    secret_name=name,
                    secret_value=value,
                )
                return json.dumps({
                    "action": "created",
                    "key": name,
                })
        finally:
            client.close()

    async def _delete(
        self, project: str | None, env: str | None, name: str | None, path: str
    ) -> str:
        if not project or not env or not name:
            return json.dumps({"error": "Required: project, environment, and secret_name"})

        client = _get_kms_client()
        try:
            client.delete_secret(
                project_id=project,
                environment=env,
                secret_name=name,
                path=path,
            )
        finally:
            client.close()

        return json.dumps({"action": "deleted", "key": name})

    async def _inject(self, project: str | None, env: str | None, path: str, fmt: str) -> str:
        if not project or not env:
            return json.dumps({"error": "Required: project and environment"})

        client = _get_kms_client()
        try:
            secrets = client.list_secrets(project_id=project, environment=env, path=path)
        finally:
            client.close()

        if not secrets:
            return json.dumps({"message": "No secrets found", "output": ""})

        if fmt == "json":
            data = {s.secret_key: s.secret_value for s in secrets}
            return json.dumps(data, indent=2)
        elif fmt == "dotenv":
            lines = []
            for s in secrets:
                val = s.secret_value.replace('"', '\\"')
                lines.append(f'{s.secret_key}="{val}"')
            return "\n".join(lines)
        else:  # export
            lines = []
            for s in secrets:
                val = s.secret_value.replace("'", "'\\''")
                lines.append(f"export {s.secret_key}='{val}'")
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
            project: Annotated[
                str | None,
                Field(description="KMS project ID or slug"),
            ] = None,
            environment: Annotated[
                str | None,
                Field(description="Environment: dev, staging, production"),
            ] = None,
            secret_name: Annotated[
                str | None,
                Field(description="Secret key name (for get/set/delete)"),
            ] = None,
            secret_value: Annotated[
                str | None,
                Field(description="Secret value (for set)"),
            ] = None,
            path: Annotated[
                str,
                Field(description="Secret path prefix (default: /)"),
            ] = "/",
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
                project=project,
                environment=environment,
                secret_name=secret_name,
                secret_value=secret_value,
                path=path,
                format=format,
                reveal=reveal,
            )
