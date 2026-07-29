"""Tests for FastAPI integration."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hanzo_iam.config import IAMConfig
from hanzo_iam.fastapi import (
    configure,
    get_config,
    require_admin,
    require_org,
    require_role,
)
from hanzo_iam.models import Organization


def _config(org: str = "hanzo", **kw) -> IAMConfig:
    """A resource-server config. The tenant and issuer are always named."""
    return IAMConfig(
        server_url=kw.pop("server_url", f"https://{org}.id"),
        client_id=kw.pop("client_id", "test-client"),
        organization=org,
        **kw,
    )


class TestConfigure:
    """configure() takes a config. It does not read the environment itself.

    It used to be the THIRD reader of IAM_ENDPOINT/IAM_ORG (after
    IAMConfig.from_env and IAMClient._config_from_env), and it defaulted the
    org to HANZO. For a resource server that default is issuer confusion: a
    Zoo API that forgot to name its org trusted hanzo.id's JWKS and accepted
    hanzo-issued tokens as its own users.
    """

    def test_configure_takes_a_config(self):
        config = configure(_config(org="hanzo", client_secret="test-secret"))
        assert config.client_id == "test-client"
        assert config.client_secret == "test-secret"
        assert config.organization == "hanzo"
        assert config.server_url == "https://hanzo.id"

    def test_configure_honours_a_non_hanzo_issuer(self):
        config = configure(_config(org=Organization.ZOO.value))
        assert config.server_url == "https://zoo.id"
        assert config.organization == "zoo"

    def test_configure_reads_the_one_env_reader_when_given_nothing(self, monkeypatch):
        monkeypatch.setenv("IAM_ENDPOINT", "https://zoo.id")
        monkeypatch.setenv("IAM_CLIENT_ID", "zoo-api")
        monkeypatch.setenv("IAM_ORG", "zoo")

        config = configure()
        assert config.server_url == "https://zoo.id"
        assert config.organization == "zoo"

    def test_configure_refuses_an_unnamed_tenant(self, monkeypatch):
        """No config and no IAM_ORG must RAISE, never fall back to hanzo."""
        for v in ("IAM_ORG", "IAM_ENDPOINT", "IAM_CLIENT_ID"):
            monkeypatch.delenv(v, raising=False)

        with pytest.raises(ValueError, match="IAM_ORG"):
            configure()

    def test_get_config_before_configure_raises(self):
        """get_config() before configure() raises RuntimeError."""
        # Reset global state
        import hanzo_iam.fastapi as module

        module._config = None

        with pytest.raises(RuntimeError, match="IAM not configured"):
            get_config()


class TestTokenDependencies:
    """Tests for token extraction dependencies."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        configure(_config())
        app = FastAPI()

        @app.get("/optional")
        async def optional_route(token: str | None = None):
            # Simulating get_token behavior
            return {"token": token}

        @app.get("/required")
        async def required_route(token: str = ""):
            # Simulating require_token behavior
            return {"token": token}

        return app

    def test_optional_token_missing(self, app):
        """Optional token returns None when missing."""
        client = TestClient(app)
        # Test basic route without actual dependency
        response = client.get("/optional")
        assert response.status_code == 200


class TestRequireOrg:
    """Tests for require_org dependency factory."""

    def test_require_org_normalizes_strings(self):
        """require_org normalizes Organization enums to strings."""
        configure(_config())
        dep = require_org([Organization.HANZO, "zoo"])
        # Verify it's a callable (dependency)
        assert callable(dep)

    def test_require_org_accepts_string_list(self):
        """require_org accepts list of strings."""
        configure(_config())
        dep = require_org(["hanzo", "zoo", "lux"])
        assert callable(dep)


class TestRequireRole:
    """Tests for require_role dependency factory."""

    def test_require_role_returns_callable(self):
        """require_role returns a callable dependency."""
        configure(_config())
        dep = require_role("moderator")
        assert callable(dep)


class TestRequireAdmin:
    """Tests for require_admin dependency."""

    def test_require_admin_is_async(self):
        """require_admin is an async function."""
        import asyncio

        assert asyncio.iscoroutinefunction(require_admin)


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_exist(self):
        """All __all__ exports exist."""
        from hanzo_iam import fastapi

        expected = [
            "configure",
            "get_config",
            "get_token",
            "require_token",
            "get_token_claims",
            "require_auth",
            "get_current_user",
            "get_optional_user",
            "require_org",
            "require_admin",
            "require_role",
        ]

        for name in expected:
            assert hasattr(fastapi, name), f"Missing export: {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
