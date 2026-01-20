"""Hanzo API Tools - Generic API tool for calling any REST API.

This package provides a unified interface for calling any REST API
via OpenAPI specs with automatic credential management.

Key Features:
- Auto-detection of 30+ cloud provider credentials from environment
- OpenAPI spec parsing with smart caching (ETag support)
- Structured errors with recovery hints
- Pluggable credential storage (memory, file, environment)
- Agent-friendly typed interface

Quick Start:
    from hanzo_tools.api import APIClient

    async with APIClient() as client:
        # List providers (auto-detects CLOUDFLARE_API_TOKEN, etc.)
        providers = await client.list_providers()

        # Configure if needed
        await client.config("cloudflare", api_key="...")

        # Load spec and call operations
        await client.spec("cloudflare")
        result = await client.call("cloudflare", "listZones")

MCP Tool Usage:
    from hanzo_tools.api import APITool, TOOLS

    # The tool handles everything via actions
    tool = APITool()
    result = await tool.call(ctx, action="list")
    result = await tool.call(ctx, action="call", provider="cloudflare", operation="listZones")
"""

# Models (structured data types)
from .models import (
    AuthType,
    Credential,
    CredentialSource,
    EffectiveCredential,
    ProviderConfig,
    ProviderStatus,
    ProviderListResult,
    Operation,
    Parameter,
    OperationListResult,
    APICallResult,
    ToolSchema,
    ToolParameter,
)

# Errors (structured errors with hints)
from .errors import (
    APIError,
    CredentialError,
    OperationNotFoundError,
    ProviderNotFoundError,
    SpecNotLoadedError,
    SpecLoadError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
)

# Storage (pluggable credential storage)
from .storage import (
    CredentialStorage,
    MemoryCredentialStorage,
    FileCredentialStorage,
    EnvironmentCredentialStorage,
    ChainedCredentialStorage,
)

# Providers (provider configs and env var mappings)
from .providers import (
    PROVIDER_CONFIGS,
    ENV_VAR_MAPPINGS,
    get_provider_config,
    list_providers as list_provider_names,
)

# Credentials (credential management)
from .credentials import (
    CredentialManager,
    get_credential_manager,
    reset_credential_manager,
)

# OpenAPI (spec parsing and caching)
from .openapi_client import (
    OpenAPIClient,
    SpecCache,
    get_client,
    clear_clients,
)

# Main client (typed interface)
from .client import (
    APIClient,
    get_api_client,
    reset_api_client,
)

# MCP Tool
from .api_tool import APITool

# Tools list for entry point discovery - must be classes, not instances
TOOLS = [APITool]

__all__ = [
    # Models
    "AuthType",
    "Credential",
    "CredentialSource",
    "EffectiveCredential",
    "ProviderConfig",
    "ProviderStatus",
    "ProviderListResult",
    "Operation",
    "Parameter",
    "OperationListResult",
    "APICallResult",
    "ToolSchema",
    "ToolParameter",
    # Errors
    "APIError",
    "CredentialError",
    "OperationNotFoundError",
    "ProviderNotFoundError",
    "SpecNotLoadedError",
    "SpecLoadError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    # Storage
    "CredentialStorage",
    "MemoryCredentialStorage",
    "FileCredentialStorage",
    "EnvironmentCredentialStorage",
    "ChainedCredentialStorage",
    # Providers
    "PROVIDER_CONFIGS",
    "ENV_VAR_MAPPINGS",
    "get_provider_config",
    "list_provider_names",
    # Credentials
    "CredentialManager",
    "get_credential_manager",
    "reset_credential_manager",
    # OpenAPI
    "OpenAPIClient",
    "SpecCache",
    "get_client",
    "clear_clients",
    # Client
    "APIClient",
    "get_api_client",
    "reset_api_client",
    # Tool
    "APITool",
    "TOOLS",
]
