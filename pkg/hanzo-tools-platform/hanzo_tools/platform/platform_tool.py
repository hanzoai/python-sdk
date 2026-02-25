"""MCP tool for Hanzo platform services — PaaS, IAM, and cloud.

Combines PaaS deployments, IAM user/org management, and cloud services
into a single MCP tool to avoid tool proliferation.

Auth: Uses HanzoSession from hanzo-tools-auth to exchange IAM tokens
for PaaS sessions and access IAM APIs.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, final

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo platform management — PaaS deployments, IAM, and cloud services.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

PaaS actions:
- deployments: List containers/deployments in a project environment
- deploy: Get details of a specific deployment
- logs: View container logs
- redeploy: Trigger a rolling restart of a container
- env: List environments for a project

IAM actions:
- whoami: Current user info
- users: List users in the organization
- orgs: List organizations
- roles: List roles

Cloud actions:
- services: List managed services (cluster info)
- projects: List projects in an organization
"""


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


@final
class PlatformTool(BaseTool):
    """MCP tool for Hanzo platform operations."""

    @property
    def name(self) -> str:
        return "platform"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "whoami",
        org: str | None = None,
        project: str | None = None,
        environment: str | None = None,
        container: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            # IAM actions
            if action == "whoami":
                return await self._whoami()
            elif action == "users":
                return await self._users()
            elif action == "orgs":
                return await self._orgs()
            elif action == "roles":
                return await self._roles()
            # PaaS actions
            elif action == "projects":
                return await self._projects(org)
            elif action == "env":
                return await self._envs(org, project)
            elif action == "deployments":
                return await self._deployments(org, project, environment)
            elif action == "deploy":
                return await self._deploy_detail(org, project, environment, container)
            elif action == "logs":
                return await self._logs(org, project, environment, container)
            elif action == "redeploy":
                return await self._redeploy(org, project, environment, container)
            # Cloud actions
            elif action == "services":
                return await self._services()
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "whoami", "users", "orgs", "roles",
                        "projects", "env", "deployments", "deploy", "logs", "redeploy",
                        "services",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"Platform tool error: {e}")
            return json.dumps({"error": f"Platform error: {e}"})

    # -- IAM actions ---------------------------------------------------------

    async def _whoami(self) -> str:
        session = _get_session()
        if not session.is_authenticated():
            return json.dumps({"error": "Not authenticated. Run 'hanzo login' first."})

        token = session.get_iam_token()
        if token:
            try:
                import jwt

                claims = jwt.decode(token, options={"verify_signature": False})
                return json.dumps({
                    "sub": claims.get("sub"),
                    "name": claims.get("name"),
                    "email": claims.get("email"),
                    "organization": claims.get("owner"),
                    "iss": claims.get("iss"),
                }, indent=2)
            except Exception:
                pass

        info = session.get_token_info()
        return json.dumps(info, indent=2)

    async def _users(self) -> str:
        session = _get_session()
        iam = session.get_iam_client()
        users = iam.get_users()
        result = []
        for u in users:
            result.append({
                "id": getattr(u, "id", None),
                "name": getattr(u, "name", None),
                "email": getattr(u, "email", None),
                "display_name": getattr(u, "display_name", None),
            })
        return json.dumps({"count": len(result), "users": result}, indent=2)

    async def _orgs(self) -> str:
        session = _get_session()
        iam = session.get_iam_client()
        orgs = iam.get_organizations()
        return json.dumps({"count": len(orgs), "organizations": orgs}, indent=2)

    async def _roles(self) -> str:
        session = _get_session()
        iam = session.get_iam_client()
        roles = iam.get_roles()
        return json.dumps({"count": len(roles), "roles": roles}, indent=2)

    # -- PaaS actions --------------------------------------------------------

    async def _projects(self, org: str | None) -> str:
        if not org:
            return json.dumps({"error": "Required: org (organization ID)"})

        session = _get_session()
        paas = session.get_paas_client()
        projects = paas.get(f"/v1/org/{org}/project")
        return json.dumps({"org": org, "count": len(projects), "projects": projects}, indent=2)

    async def _envs(self, org: str | None, project: str | None) -> str:
        if not org or not project:
            return json.dumps({"error": "Required: org and project"})

        session = _get_session()
        paas = session.get_paas_client()
        envs = paas.get(f"/v1/org/{org}/project/{project}/env")
        return json.dumps({"org": org, "project": project, "environments": envs}, indent=2)

    async def _deployments(self, org: str | None, project: str | None, env: str | None) -> str:
        if not org or not project or not env:
            return json.dumps({"error": "Required: org, project, and environment"})

        session = _get_session()
        paas = session.get_paas_client()
        containers = paas.get(f"/v1/org/{org}/project/{project}/env/{env}/container")

        result = []
        for c in containers if isinstance(containers, list) else []:
            result.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "image": c.get("image"),
                "status": c.get("status"),
                "replicas": c.get("replicas"),
            })

        return json.dumps({
            "org": org,
            "project": project,
            "environment": env,
            "count": len(result),
            "containers": result,
        }, indent=2)

    async def _deploy_detail(
        self, org: str | None, project: str | None, env: str | None, container: str | None
    ) -> str:
        if not org or not project or not env or not container:
            return json.dumps({"error": "Required: org, project, environment, and container"})

        session = _get_session()
        paas = session.get_paas_client()
        data = paas.get(f"/v1/org/{org}/project/{project}/env/{env}/container/{container}")
        return json.dumps(data, indent=2)

    async def _logs(
        self, org: str | None, project: str | None, env: str | None, container: str | None
    ) -> str:
        if not org or not project or not env or not container:
            return json.dumps({"error": "Required: org, project, environment, and container"})

        session = _get_session()
        paas = session.get_paas_client()
        logs = paas.get(f"/v1/org/{org}/project/{project}/env/{env}/container/{container}/logs")
        if isinstance(logs, dict):
            return json.dumps(logs, indent=2)
        return str(logs)

    async def _redeploy(
        self, org: str | None, project: str | None, env: str | None, container: str | None
    ) -> str:
        if not org or not project or not env or not container:
            return json.dumps({"error": "Required: org, project, environment, and container"})

        session = _get_session()
        paas = session.get_paas_client()

        # Fetch current config and PUT it back to trigger rolling restart
        current = paas.get(f"/v1/org/{org}/project/{project}/env/{env}/container/{container}")
        result = paas.put(
            f"/v1/org/{org}/project/{project}/env/{env}/container/{container}",
            json=current,
        )
        return json.dumps({"action": "redeployed", "container": container, "result": result}, indent=2)

    # -- Cloud actions -------------------------------------------------------

    async def _services(self) -> str:
        session = _get_session()
        paas = session.get_paas_client()
        info = paas.get("/v1/cluster/info")
        templates = paas.get("/v1/cluster/templates")
        return json.dumps({
            "cluster": info,
            "templates": templates,
        }, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register platform tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="platform",
            description=DESCRIPTION,
        )
        async def platform(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "IAM: whoami, users, orgs, roles. "
                        "PaaS: projects, env, deployments, deploy, logs, redeploy. "
                        "Cloud: services."
                    ),
                ),
            ] = "whoami",
            org: Annotated[
                str | None,
                Field(description="Organization ID (for PaaS actions)"),
            ] = None,
            project: Annotated[
                str | None,
                Field(description="Project ID (for PaaS actions)"),
            ] = None,
            environment: Annotated[
                str | None,
                Field(description="Environment ID (for PaaS actions)"),
            ] = None,
            container: Annotated[
                str | None,
                Field(description="Container/deployment ID (for deploy, logs, redeploy)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                org=org,
                project=project,
                environment=environment,
                container=container,
            )
