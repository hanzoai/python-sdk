"""Tests for hanzo-tools-api v0.2.0."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from hanzo_tools.api import (
    APIClient,
    APITool,
    Credential,
    CredentialManager,
    OpenAPIClient,
    SpecCache,
    get_credential_manager,
    reset_credential_manager,
    PROVIDER_CONFIGS,
    ENV_VAR_MAPPINGS,
)
from hanzo_tools.api.models import AuthType
from hanzo_tools.api.storage import (
    MemoryCredentialStorage,
    ChainedCredentialStorage,
)


class TestCredentialManager:
    """Tests for CredentialManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cred_manager(self, temp_config_dir):
        """Create a CredentialManager with temp directory."""
        return CredentialManager(config_dir=temp_config_dir)

    @pytest.mark.asyncio
    async def test_set_and_get_credential(self, cred_manager):
        """Test storing and retrieving credentials."""
        await cred_manager.set_credential(
            provider="test-provider",
            api_key="test-key",
            api_secret="test-secret",
            account_id="test-account",
        )

        cred = await cred_manager.get_credential("test-provider")
        assert cred.provider == "test-provider"
        assert cred.api_key == "test-key"
        assert cred.api_secret == "test-secret"
        assert cred.account_id == "test-account"
        assert cred.has_credentials

    @pytest.mark.asyncio
    async def test_credentials_persist(self, temp_config_dir):
        """Test that credentials persist across instances."""
        # Set credential
        cm1 = CredentialManager(config_dir=temp_config_dir)
        await cm1.set_credential("test", api_key="my-key")

        # Read with new instance
        cm2 = CredentialManager(config_dir=temp_config_dir)
        cred = await cm2.get_credential("test")
        assert cred.api_key == "my-key"

    @pytest.mark.asyncio
    async def test_delete_credential(self, cred_manager):
        """Test deleting credentials."""
        await cred_manager.set_credential("test", api_key="key")
        assert await cred_manager.delete_credential("test")
        assert not await cred_manager.delete_credential("test")  # Already deleted

        cred = await cred_manager.get_credential("test")
        assert not cred.has_credentials

    @pytest.mark.asyncio
    async def test_env_var_fallback(self, temp_config_dir):
        """Test environment variable fallback."""
        # Use a unique provider with custom env var mapping
        with patch.dict(os.environ, {"TESTPROV_API_KEY": "env-token"}, clear=False):
            # Create custom storage chain with our test env var
            from hanzo_tools.api.storage import EnvironmentCredentialStorage

            env_mappings = {"testprov": ["TESTPROV_API_KEY"]}
            storage = ChainedCredentialStorage([
                MemoryCredentialStorage(),
                EnvironmentCredentialStorage(env_mappings),
            ])

            cred_manager = CredentialManager(
                config_dir=temp_config_dir,
                storage=storage,
            )
            cred = await cred_manager.get_credential("testprov")
            assert cred.api_key == "env-token"

    @pytest.mark.asyncio
    async def test_list_providers(self, cred_manager):
        """Test listing providers."""
        await cred_manager.set_credential("custom", api_key="key")

        providers = await cred_manager.list_providers()
        provider_names = [p.name for p in providers]

        # Should include configured providers
        assert "cloudflare" in provider_names
        assert "github" in provider_names
        assert "custom" in provider_names

        # Custom should be configured
        custom = next(p for p in providers if p.name == "custom")
        assert custom.configured

    def test_get_provider_config(self, cred_manager):
        """Test getting provider configuration."""
        config = cred_manager.get_provider_config("cloudflare")
        assert config is not None
        assert config.name == "cloudflare"
        assert config.base_url == "https://api.cloudflare.com/client/v4"
        assert config.auth_type == AuthType.BEARER


class TestProviderConfigs:
    """Tests for built-in provider configurations."""

    def test_all_providers_have_required_fields(self):
        """Test that all providers have required fields."""
        for name, config in PROVIDER_CONFIGS.items():
            assert config.name == name
            assert config.display_name
            assert config.base_url
            assert config.auth_type in AuthType

    def test_env_var_mappings_exist(self):
        """Test that env var mappings cover common providers."""
        expected_providers = ["cloudflare", "github", "openai", "anthropic", "stripe"]
        for provider in expected_providers:
            assert provider in ENV_VAR_MAPPINGS
            assert len(ENV_VAR_MAPPINGS[provider]) > 0


class TestCredential:
    """Tests for Credential model."""

    def test_has_credentials(self):
        """Test has_credentials property."""
        cred = Credential(provider="test")
        assert not cred.has_credentials

        cred = Credential(provider="test", api_key="key")
        assert cred.has_credentials


class TestOpenAPIClient:
    """Tests for OpenAPIClient."""

    @pytest.fixture
    def sample_spec(self):
        """Sample OpenAPI spec for testing."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0"},
            "servers": [{"url": "https://api.test.com/v1"}],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "List all users",
                        "tags": ["users"],
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create a user",
                        "tags": ["users"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                    }
                                }
                            },
                        },
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/users/{id}": {
                    "get": {
                        "operationId": "getUser",
                        "summary": "Get a user",
                        "tags": ["users"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def client(self, sample_spec, temp_config_dir):
        """Create an OpenAPIClient with sample spec."""
        # Create credential manager
        cred_manager = CredentialManager(config_dir=temp_config_dir)
        await cred_manager.set_credential("test", api_key="test-key")

        # Create spec cache and seed it with sample spec
        spec_cache = SpecCache(temp_config_dir / "specs")
        await spec_cache.set("test", sample_spec)

        # Create client
        client = OpenAPIClient(
            "test",
            credential_manager=cred_manager,
            spec_cache=spec_cache,
        )

        # Load the spec
        await client.load_spec()

        return client

    @pytest.mark.asyncio
    async def test_base_url_from_spec(self, client):
        """Test base URL extraction from spec."""
        assert client.base_url == "https://api.test.com/v1"

    @pytest.mark.asyncio
    async def test_list_operations(self, client):
        """Test listing operations."""
        result = client.list_operations()
        assert result.total_count == 3
        op_ids = [op.operation_id for op in result.operations]
        assert "listUsers" in op_ids
        assert "createUser" in op_ids
        assert "getUser" in op_ids

    @pytest.mark.asyncio
    async def test_list_operations_by_tag(self, client):
        """Test filtering operations by tag."""
        result = client.list_operations(tag="users")
        assert result.total_count == 3

    @pytest.mark.asyncio
    async def test_list_operations_by_search(self, client):
        """Test searching operations."""
        result = client.list_operations(search="list")
        assert result.total_count == 1
        assert result.operations[0].operation_id == "listUsers"

    @pytest.mark.asyncio
    async def test_get_operation(self, client):
        """Test getting a specific operation."""
        op = client.get_operation("getUser")
        assert op is not None
        assert op.operation_id == "getUser"
        assert op.method == "GET"
        assert op.path == "/users/{id}"
        assert len(op.parameters) == 1
        assert op.parameters[0].name == "id"
        assert op.parameters[0].required

    @pytest.mark.asyncio
    async def test_path_param_substitution(self, client):
        """Test path parameter substitution."""
        path, remaining = client._substitute_path_params(
            "/users/{id}/posts/{post_id}",
            {"id": "123", "post_id": "456", "extra": "value"},
        )
        assert path == "/users/123/posts/456"
        assert remaining == {"extra": "value"}


class TestAPIClient:
    """Tests for the main APIClient."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def api_client(self, temp_config_dir):
        """Create APIClient with temp directory."""
        return APIClient(config_dir=temp_config_dir)

    @pytest.mark.asyncio
    async def test_list_providers(self, api_client):
        """Test listing providers."""
        result = await api_client.list_providers()
        assert result.total_count > 0

        provider_names = [p.name for p in result.providers]
        assert "cloudflare" in provider_names
        assert "github" in provider_names

    @pytest.mark.asyncio
    async def test_config_and_get_credentials(self, api_client):
        """Test configuring and retrieving credentials."""
        await api_client.config("test-api", api_key="my-key")

        effective = await api_client.get_effective_credentials("test-api")
        assert effective.has_credentials
        assert effective.credential.api_key == "my-key"

    @pytest.mark.asyncio
    async def test_delete_config(self, api_client):
        """Test deleting configuration."""
        await api_client.config("test-api", api_key="my-key")
        assert await api_client.delete_config("test-api")
        assert not await api_client.delete_config("test-api")  # Already deleted


class TestAPITool:
    """Tests for APITool."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def tool(self, temp_config_dir):
        """Create APITool with mocked client."""
        client = APIClient(config_dir=temp_config_dir)
        return APITool(client=client)

    @pytest.mark.asyncio
    async def test_list_action(self, tool):
        """Test list action."""
        ctx = AsyncMock()
        result = await tool.call(ctx, action="list")
        assert "API Providers" in result
        assert "cloudflare" in result.lower()

    @pytest.mark.asyncio
    async def test_config_action(self, tool):
        """Test config action."""
        ctx = AsyncMock()

        # Configure
        result = await tool.call(
            ctx,
            action="config",
            provider="test-api",
            api_key="my-key",
        )
        assert "Configured" in result

    @pytest.mark.asyncio
    async def test_config_requires_provider(self, tool):
        """Test that config action requires provider."""
        ctx = AsyncMock()
        result = await tool.call(ctx, action="config", api_key="key")
        assert "Error" in result
        assert "provider" in result.lower()

    @pytest.mark.asyncio
    async def test_config_requires_api_key(self, tool):
        """Test that config action requires api_key."""
        ctx = AsyncMock()
        result = await tool.call(ctx, action="config", provider="test")
        assert "Error" in result
        assert "api_key" in result.lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self, tool):
        """Test unknown action."""
        ctx = AsyncMock()
        result = await tool.call(ctx, action="invalid")
        assert "Unknown action" in result

    def test_tool_name(self, tool):
        """Test tool name."""
        assert tool.name == "api"

    def test_tool_description(self, tool):
        """Test tool description."""
        desc = tool.description
        assert "API" in desc
        assert "OpenAPI" in desc
        assert "credential" in desc.lower()


class TestIntegration:
    """Integration tests (require network, skip by default)."""

    @pytest.mark.skip(reason="Requires network and API keys")
    @pytest.mark.asyncio
    async def test_github_api(self):
        """Test calling GitHub API."""
        # This would require GITHUB_TOKEN to be set
        async with APIClient() as client:
            await client.spec("github")
            result = await client.ops("github", search="user")
            assert result.total_count > 0

    @pytest.mark.skip(reason="Requires network and API keys")
    @pytest.mark.asyncio
    async def test_cloudflare_api(self):
        """Test calling Cloudflare API."""
        # This would require CLOUDFLARE_API_TOKEN to be set
        async with APIClient() as client:
            await client.spec("cloudflare")
            result = await client.call("cloudflare", "listZones")
            assert result.success
