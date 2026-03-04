"""PaaSTool test suite — action routing, validation, auth, error handling."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from hanzo_tools.paas.paas_tool import PaaSTool


@pytest.fixture
def tool():
    return PaaSTool()


@pytest.fixture
def ctx():
    return MagicMock()


def _mock_session(**overrides):
    session = MagicMock()
    session.is_authenticated.return_value = overrides.get("authenticated", True)
    session.get_iam_token.return_value = overrides.get("token", None)
    session.get_token_info.return_value = overrides.get("token_info", {})
    if "paas_get" in overrides:
        session.get_paas_client.return_value.get.return_value = overrides["paas_get"]
    return session


def _fake_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}."


class TestProperties:
    def test_name(self, tool):
        assert tool.name == "paas"

    def test_description_sections(self, tool):
        for section in ("PaaS actions", "IAM actions", "Cloud actions"):
            assert section in tool.description


class TestActionRouting:
    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="bogus"))
        assert "Unknown action" in result["error"]

    @pytest.mark.asyncio
    async def test_unknown_action_lists_available(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="bogus"))
        expected = {"whoami", "users", "orgs", "roles", "projects", "env",
                    "deployments", "deploy", "logs", "redeploy", "services"}
        assert set(result["available"]) == expected

    @pytest.mark.asyncio
    async def test_default_action_is_whoami(self, tool, ctx):
        session = _mock_session(authenticated=False)
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx))
        assert "Not authenticated" in result["error"]


class TestWhoami:
    @pytest.mark.asyncio
    async def test_unauthenticated(self, tool, ctx):
        session = _mock_session(authenticated=False)
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="whoami"))
        assert "Not authenticated" in result["error"]

    @pytest.mark.asyncio
    async def test_jwt_decode(self, tool, ctx):
        token = _fake_jwt({"sub": "u1", "name": "Z", "email": "z@hanzo.ai", "owner": "hanzo"})
        session = _mock_session(token=token)
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="whoami"))
        assert result["sub"] == "u1"
        assert result["email"] == "z@hanzo.ai"
        assert result["organization"] == "hanzo"

    @pytest.mark.asyncio
    async def test_fallback_to_token_info(self, tool, ctx):
        session = _mock_session(token=None, token_info={"sub": "fallback"})
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="whoami"))
        assert result["sub"] == "fallback"


class TestValidation:
    """Required-parameter checks for PaaS actions."""

    @pytest.mark.asyncio
    async def test_projects_needs_org(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            result = json.loads(await tool.call(ctx, action="projects"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_env_needs_org_and_project(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            for kwargs in [
                {"org": "o"},
                {"project": "p"},
                {},
            ]:
                result = json.loads(await tool.call(ctx, action="env", **kwargs))
                assert "error" in result

    @pytest.mark.asyncio
    async def test_deployments_needs_three(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            result = json.loads(await tool.call(ctx, action="deployments", org="o", project="p"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_deploy_needs_container(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            result = json.loads(await tool.call(ctx, action="deploy", org="o", project="p", environment="e"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_logs_needs_container(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            result = json.loads(await tool.call(ctx, action="logs", org="o", project="p", environment="e"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_redeploy_needs_container(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session"):
            result = json.loads(await tool.call(ctx, action="redeploy", org="o", project="p", environment="e"))
        assert "error" in result


class TestProjects:
    @pytest.mark.asyncio
    async def test_returns_projects(self, tool, ctx):
        projects = [{"id": "p1", "name": "web"}, {"id": "p2", "name": "api"}]
        session = _mock_session(paas_get=projects)
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="projects", org="hanzo"))
        assert result["org"] == "hanzo"
        assert result["count"] == 2
        session.get_paas_client.return_value.get.assert_called_once_with("/v1/org/hanzo/project")

    @pytest.mark.asyncio
    async def test_empty_projects(self, tool, ctx):
        session = _mock_session(paas_get=[])
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="projects", org="hanzo"))
        assert result["count"] == 0


class TestDeployments:
    @pytest.mark.asyncio
    async def test_returns_containers(self, tool, ctx):
        containers = [
            {"id": "c1", "name": "web", "image": "nginx:latest", "status": "running", "replicas": 2},
        ]
        session = _mock_session(paas_get=containers)
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(
                ctx, action="deployments", org="o", project="p", environment="prod",
            ))
        assert result["count"] == 1
        assert result["containers"][0]["name"] == "web"
        assert result["containers"][0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_non_list_containers(self, tool, ctx):
        session = _mock_session(paas_get={"error": "not found"})
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(
                ctx, action="deployments", org="o", project="p", environment="prod",
            ))
        assert result["count"] == 0


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_runtime_error(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session", side_effect=RuntimeError("auth failed")):
            result = json.loads(await tool.call(ctx, action="whoami"))
        assert "auth failed" in result["error"]

    @pytest.mark.asyncio
    async def test_generic_exception(self, tool, ctx):
        with patch("hanzo_tools.paas.paas_tool._get_session", side_effect=TypeError("bad")):
            result = json.loads(await tool.call(ctx, action="whoami"))
        assert "bad" in result["error"]

    @pytest.mark.asyncio
    async def test_api_error_in_projects(self, tool, ctx):
        session = MagicMock()
        session.get_paas_client.return_value.get.side_effect = ConnectionError("timeout")
        with patch("hanzo_tools.paas.paas_tool._get_session", return_value=session):
            result = json.loads(await tool.call(ctx, action="projects", org="hanzo"))
        assert "timeout" in result["error"]
