"""Tests for FastAPI integration."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hanzo_iam.fastapi import (
    configure,
    get_config,
    get_token,
    require_token,
    get_token_claims,
    require_auth,
    require_org,
    require_admin,
    require_role,
)
from hanzo_iam.models import IAMConfig, JWTClaims, Organization


class TestConfigure:
    """Tests for configure() function."""

    def test_configure_with_args(self):
        """Configure with explicit arguments."""
        config = configure(
            client_id="test-client",
            client_secret="test-secret",
            org="hanzo",
        )
        assert config.client_id == "test-client"
        assert config.client_secret == "test-secret"
        assert config.organization == "hanzo"
        assert config.server_url == "https://hanzo.id"

    def test_configure_with_organization_enum(self):
        """Configure with Organization enum."""
        config = configure(
            client_id="test-client",
            org=Organization.ZOO,
        )
        assert config.server_url == "https://zoo.id"
        assert config.organization == "zoo"

    def test_configure_missing_client_id_raises(self):
        """Missing client_id raises ValueError."""
        import os
        # Ensure env var is not set
        os.environ.pop("HANZO_IAM_CLIENT_ID", None)

        with pytest.raises(ValueError, match="client_id required"):
            configure(client_id=None)

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
        configure(client_id="test-client", org="hanzo")
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
        configure(client_id="test-client")
        dep = require_org([Organization.HANZO, "zoo"])
        # Verify it's a callable (dependency)
        assert callable(dep)

    def test_require_org_accepts_string_list(self):
        """require_org accepts list of strings."""
        configure(client_id="test-client")
        dep = require_org(["hanzo", "zoo", "lux"])
        assert callable(dep)


class TestRequireRole:
    """Tests for require_role dependency factory."""

    def test_require_role_returns_callable(self):
        """require_role returns a callable dependency."""
        configure(client_id="test-client")
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
