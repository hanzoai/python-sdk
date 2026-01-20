"""Main API client with explicit typed methods.

Provides a clean, agent-friendly interface for API operations:

    from hanzo_tools.api import APIClient

    client = APIClient()

    # Discover providers
    providers = await client.list_providers()

    # Configure credentials
    await client.config("cloudflare", api_key="...")

    # Load spec and discover operations
    await client.spec("cloudflare")
    ops = await client.ops("cloudflare", search="zones")

    # Call operations
    result = await client.call("cloudflare", "listZones", params={"page": 1})

    # Raw requests
    result = await client.raw("github", "GET", "/user/repos")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from .models import (
    APICallResult,
    Credential,
    CredentialSource,
    EffectiveCredential,
    Operation,
    OperationListResult,
    ProviderListResult,
    ProviderStatus,
    ToolSchema,
    ToolParameter,
)
from .credentials import CredentialManager, get_credential_manager, reset_credential_manager
from .openapi_client import OpenAPIClient, SpecCache, get_client, clear_clients
from .providers import PROVIDER_CONFIGS, get_provider_config, list_providers as _list_provider_names
from .errors import (
    APIError,
    CredentialError,
    OperationNotFoundError,
    ProviderNotFoundError,
    SpecNotLoadedError,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Main API client with explicit typed methods.

    This is the primary interface for agent integration. Each method
    has explicit parameters with type hints for easy auto-completion
    and validation.

    Example:
        client = APIClient()

        # List and configure providers
        providers = await client.list_providers()
        await client.config("cloudflare", api_key="my-token")

        # Load spec and call operations
        await client.spec("cloudflare")
        result = await client.call("cloudflare", "listZones")

        # Or make raw requests
        result = await client.raw("github", "GET", "/user/repos")
    """

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        credential_manager: Optional[CredentialManager] = None,
    ):
        """Initialize API client.

        Args:
            config_dir: Directory for credentials and specs
            credential_manager: Custom credential manager
        """
        self._config_dir = config_dir or Path.home() / ".hanzo" / "api"
        self._cred_manager = credential_manager or get_credential_manager()
        self._spec_cache = SpecCache(self._config_dir / "specs")
        self._clients: dict[str, OpenAPIClient] = {}

    async def _get_openapi_client(self, provider: str) -> OpenAPIClient:
        """Get or create OpenAPI client for provider."""
        if provider not in self._clients:
            self._clients[provider] = OpenAPIClient(
                provider=provider,
                credential_manager=self._cred_manager,
                spec_cache=self._spec_cache,
            )
        return self._clients[provider]

    # =========================================================================
    # Provider Discovery
    # =========================================================================

    async def list_providers(self, configured_only: bool = False) -> ProviderListResult:
        """List all available providers and their status.

        Args:
            configured_only: Only return providers with credentials configured

        Returns:
            ProviderListResult with provider statuses

        Example:
            result = await client.list_providers()
            for p in result.configured:
                print(f"{p.name}: {p.source}")
        """
        statuses = await self._cred_manager.list_providers()

        if configured_only:
            statuses = [s for s in statuses if s.configured]

        return ProviderListResult(
            providers=statuses,
            configured_count=sum(1 for s in statuses if s.configured),
            total_count=len(statuses),
        )

    async def get_provider(self, provider: str) -> ProviderStatus:
        """Get detailed status for a specific provider.

        Args:
            provider: Provider name

        Returns:
            ProviderStatus with configuration details

        Raises:
            ProviderNotFoundError: If provider is unknown
        """
        providers = await self.list_providers()

        for p in providers.providers:
            if p.name == provider:
                return p

        raise ProviderNotFoundError(
            provider=provider,
            available_providers=[p.name for p in providers.providers],
        )

    # =========================================================================
    # Credential Management
    # =========================================================================

    async def config(
        self,
        provider: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra,
    ) -> None:
        """Configure credentials for a provider.

        Args:
            provider: Provider name (e.g., 'cloudflare', 'github')
            api_key: API key or token
            api_secret: API secret (for providers that need it)
            account_id: Account/organization ID
            base_url: Custom base URL override
            **extra: Additional provider-specific fields

        Example:
            await client.config("cloudflare", api_key="my-token")
            await client.config("stripe", api_key="sk_xxx", api_secret="whsec_xxx")
        """
        await self._cred_manager.set_credential(
            provider=provider,
            api_key=api_key,
            api_secret=api_secret,
            account_id=account_id,
            base_url=base_url,
            **extra,
        )
        logger.info(f"Configured credentials for {provider}")

    async def delete_config(self, provider: str) -> bool:
        """Delete stored credentials for a provider.

        Args:
            provider: Provider name

        Returns:
            True if deleted, False if not found
        """
        return await self._cred_manager.delete_credential(provider)

    async def get_effective_credentials(self, provider: str) -> EffectiveCredential:
        """Get credential with full resolution info.

        Shows exactly where the credential came from, useful for
        debugging authentication issues.

        Args:
            provider: Provider name

        Returns:
            EffectiveCredential with source information

        Example:
            effective = await client.get_effective_credentials("cloudflare")
            print(f"Source: {effective.source}")  # e.g., "environment"
            print(f"Env var: {effective.env_var_used}")  # e.g., "CLOUDFLARE_API_TOKEN"
        """
        return await self._cred_manager.get_effective_credentials(provider)

    # =========================================================================
    # OpenAPI Spec Management
    # =========================================================================

    async def spec(
        self,
        provider: str,
        spec_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> int:
        """Load or refresh OpenAPI spec for a provider.

        Args:
            provider: Provider name
            spec_url: Custom URL to OpenAPI spec
            force_refresh: Force refresh even if cached

        Returns:
            Number of operations discovered

        Example:
            count = await client.spec("cloudflare")
            print(f"Loaded {count} operations")

            # Load custom spec
            await client.spec("custom-api", spec_url="https://api.example.com/openapi.json")
        """
        openapi_client = await self._get_openapi_client(provider)

        if spec_url:
            await openapi_client.load_spec(spec_url)
        elif force_refresh:
            await openapi_client.refresh_spec(force=True)
        else:
            await openapi_client.load_spec()

        return len(openapi_client._operations)

    async def has_spec(self, provider: str) -> bool:
        """Check if spec is available for provider.

        Args:
            provider: Provider name

        Returns:
            True if spec is loaded or cached
        """
        openapi_client = await self._get_openapi_client(provider)
        return openapi_client.has_spec()

    async def spec_age(self, provider: str) -> Optional[float]:
        """Get age of cached spec in seconds.

        Args:
            provider: Provider name

        Returns:
            Age in seconds, or None if no spec
        """
        openapi_client = await self._get_openapi_client(provider)
        return openapi_client.spec_age()

    async def refresh_spec(self, provider: str, force: bool = False) -> bool:
        """Refresh the OpenAPI spec.

        Args:
            provider: Provider name
            force: Force refresh even if not stale

        Returns:
            True if spec was refreshed, False if using cache
        """
        openapi_client = await self._get_openapi_client(provider)
        return await openapi_client.refresh_spec(force=force)

    # =========================================================================
    # Operation Discovery
    # =========================================================================

    async def ops(
        self,
        provider: str,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        method: Optional[str] = None,
        path_contains: Optional[str] = None,
        operation_id_prefix: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> OperationListResult:
        """List available operations for a provider.

        Args:
            provider: Provider name
            search: Search in operation ID, summary, description
            tag: Filter by tag
            method: Filter by HTTP method (GET, POST, etc.)
            path_contains: Filter by path substring
            operation_id_prefix: Filter by operation ID prefix
            include_deprecated: Include deprecated operations

        Returns:
            OperationListResult with matching operations

        Example:
            # List all operations
            result = await client.ops("cloudflare")

            # Search for zone operations
            result = await client.ops("cloudflare", search="zone")

            # Filter by tag
            result = await client.ops("cloudflare", tag="Zones")

            # Filter by method
            result = await client.ops("cloudflare", method="POST")
        """
        openapi_client = await self._get_openapi_client(provider)

        if not openapi_client.spec_loaded:
            await openapi_client.load_spec()

        return openapi_client.list_operations(
            search=search,
            tag=tag,
            method=method,
            path_contains=path_contains,
            operation_id_prefix=operation_id_prefix,
            include_deprecated=include_deprecated,
        )

    async def get_operation(self, provider: str, operation_id: str) -> Operation:
        """Get detailed information about a specific operation.

        Args:
            provider: Provider name
            operation_id: Operation ID

        Returns:
            Operation with full details including parameter schemas

        Example:
            op = await client.get_operation("cloudflare", "listZones")
            print(op.params_schema)  # JSON schema for parameters
            print(op.request_body_schema)  # JSON schema for body
        """
        openapi_client = await self._get_openapi_client(provider)

        if not openapi_client.spec_loaded:
            await openapi_client.load_spec()

        return openapi_client.get_operation(operation_id)

    # =========================================================================
    # API Calls
    # =========================================================================

    async def call(
        self,
        provider: str,
        operation_id: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> APICallResult:
        """Call an API operation by ID.

        Args:
            provider: Provider name
            operation_id: Operation ID from the OpenAPI spec
            params: Path, query, and header parameters
            body: Request body (for POST/PUT/PATCH)
            headers: Additional headers
            dry_run: If True, return request details without making call

        Returns:
            APICallResult with response data

        Example:
            # Simple call
            result = await client.call("cloudflare", "listZones")

            # With parameters
            result = await client.call(
                "cloudflare",
                "getZone",
                params={"zone_id": "abc123"}
            )

            # With body
            result = await client.call(
                "cloudflare",
                "createDNSRecord",
                params={"zone_id": "abc123"},
                body={"type": "A", "name": "test", "content": "1.2.3.4"}
            )
        """
        openapi_client = await self._get_openapi_client(provider)

        if not openapi_client.spec_loaded:
            await openapi_client.load_spec()

        return await openapi_client.call(
            operation_id=operation_id,
            params=params,
            body=body,
            headers=headers,
            dry_run=dry_run,
        )

    async def raw(
        self,
        provider: str,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> APICallResult:
        """Make a raw HTTP request.

        Useful for endpoints not in the spec or custom calls.

        Args:
            provider: Provider name (for authentication)
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: URL path
            params: Query parameters
            body: Request body
            headers: Additional headers
            dry_run: If True, return request details without making call

        Returns:
            APICallResult with response data

        Example:
            # GET request
            result = await client.raw("github", "GET", "/user")

            # POST with body
            result = await client.raw(
                "github",
                "POST",
                "/repos/owner/repo/issues",
                body={"title": "Bug report", "body": "..."}
            )
        """
        openapi_client = await self._get_openapi_client(provider)

        return await openapi_client.call_raw(
            method=method,
            path=path,
            params=params,
            body=body,
            headers=headers,
            dry_run=dry_run,
        )

    # =========================================================================
    # Tool Schemas (for agent integration)
    # =========================================================================

    def get_tool_schemas(self) -> list[ToolSchema]:
        """Get machine-readable schemas for all client methods.

        Returns tool schemas that can be used by agents for
        function calling with strict argument validation.

        Returns:
            List of ToolSchema objects for each method
        """
        return [
            ToolSchema(
                name="list_providers",
                description="List all available API providers and their configuration status",
                parameters=[
                    ToolParameter(
                        name="configured_only",
                        type="boolean",
                        description="Only return providers with credentials configured",
                        default=False,
                    ),
                ],
                returns="ProviderListResult with provider statuses",
                examples=["await client.list_providers()", "await client.list_providers(configured_only=True)"],
            ),
            ToolSchema(
                name="config",
                description="Configure credentials for a provider",
                parameters=[
                    ToolParameter(
                        name="provider",
                        type="string",
                        description="Provider name (e.g., 'cloudflare', 'github')",
                        required=True,
                    ),
                    ToolParameter(
                        name="api_key",
                        type="string",
                        description="API key or token",
                    ),
                    ToolParameter(
                        name="api_secret",
                        type="string",
                        description="API secret (for providers that need it)",
                    ),
                    ToolParameter(
                        name="base_url",
                        type="string",
                        description="Custom base URL override",
                    ),
                ],
                returns="None",
                examples=["await client.config('cloudflare', api_key='my-token')"],
            ),
            ToolSchema(
                name="spec",
                description="Load or refresh OpenAPI spec for a provider",
                parameters=[
                    ToolParameter(
                        name="provider",
                        type="string",
                        description="Provider name",
                        required=True,
                    ),
                    ToolParameter(
                        name="spec_url",
                        type="string",
                        description="Custom URL to OpenAPI spec",
                    ),
                    ToolParameter(
                        name="force_refresh",
                        type="boolean",
                        description="Force refresh even if cached",
                        default=False,
                    ),
                ],
                returns="Number of operations discovered",
                examples=["await client.spec('cloudflare')", "await client.spec('custom', spec_url='...')"],
            ),
            ToolSchema(
                name="ops",
                description="List available operations for a provider",
                parameters=[
                    ToolParameter(
                        name="provider",
                        type="string",
                        description="Provider name",
                        required=True,
                    ),
                    ToolParameter(
                        name="search",
                        type="string",
                        description="Search in operation ID, summary, description",
                    ),
                    ToolParameter(
                        name="tag",
                        type="string",
                        description="Filter by tag",
                    ),
                    ToolParameter(
                        name="method",
                        type="string",
                        description="Filter by HTTP method",
                        enum=["GET", "POST", "PUT", "PATCH", "DELETE"],
                    ),
                ],
                returns="OperationListResult with matching operations",
                examples=["await client.ops('cloudflare', search='zone')"],
            ),
            ToolSchema(
                name="call",
                description="Call an API operation by ID",
                parameters=[
                    ToolParameter(
                        name="provider",
                        type="string",
                        description="Provider name",
                        required=True,
                    ),
                    ToolParameter(
                        name="operation_id",
                        type="string",
                        description="Operation ID from the OpenAPI spec",
                        required=True,
                    ),
                    ToolParameter(
                        name="params",
                        type="object",
                        description="Path, query, and header parameters",
                    ),
                    ToolParameter(
                        name="body",
                        type="object",
                        description="Request body (for POST/PUT/PATCH)",
                    ),
                    ToolParameter(
                        name="dry_run",
                        type="boolean",
                        description="Return request details without making call",
                        default=False,
                    ),
                ],
                returns="APICallResult with response data",
                examples=["await client.call('cloudflare', 'listZones')"],
            ),
            ToolSchema(
                name="raw",
                description="Make a raw HTTP request to any endpoint",
                parameters=[
                    ToolParameter(
                        name="provider",
                        type="string",
                        description="Provider name (for authentication)",
                        required=True,
                    ),
                    ToolParameter(
                        name="method",
                        type="string",
                        description="HTTP method",
                        required=True,
                        enum=["GET", "POST", "PUT", "PATCH", "DELETE"],
                    ),
                    ToolParameter(
                        name="path",
                        type="string",
                        description="URL path",
                        required=True,
                    ),
                    ToolParameter(
                        name="params",
                        type="object",
                        description="Query parameters",
                    ),
                    ToolParameter(
                        name="body",
                        type="object",
                        description="Request body",
                    ),
                ],
                returns="APICallResult with response data",
                examples=["await client.raw('github', 'GET', '/user')"],
            ),
        ]

    # =========================================================================
    # API Discovery & Registration
    # =========================================================================

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for APIs in public registries.

        Searches openapisearch.com for publicly available APIs.

        Args:
            query: Search query (e.g., 'weather', 'spotify', 'notion')

        Returns:
            List of API results with id, name, description, spec_url

        Example:
            results = await client.search("weather")
            for api in results:
                print(f"{api['id']}: {api['name']}")
        """
        import httpx

        async with httpx.AsyncClient(timeout=30) as http:
            # Search openapisearch.com
            try:
                response = await http.get(
                    f"https://openapisearch.com/api/search",
                    params={"q": query},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
            except Exception as e:
                logger.warning(f"openapisearch.com search failed: {e}")

            # Fallback: search handmade OpenAPIs on GitHub
            try:
                response = await http.get(
                    "https://api.github.com/repos/janwilmake/handmade-openapis/contents"
                )
                if response.status_code == 200:
                    files = response.json()
                    results = []
                    for f in files:
                        if f["name"].endswith(".json"):
                            name = f["name"].replace(".json", "")
                            if query.lower() in name.lower():
                                results.append({
                                    "id": name,
                                    "name": name.replace("-", " ").title(),
                                    "spec_url": f["download_url"],
                                })
                    return results
            except Exception as e:
                logger.warning(f"GitHub fallback search failed: {e}")

            return []

    async def register(
        self,
        name: str,
        spec_url: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_type: str = "bearer",
        auth_header: str = "Authorization",
        auth_prefix: str = "Bearer",
        api_key: Optional[str] = None,
    ) -> int:
        """Register a custom API provider dynamically.

        Allows using any OpenAPI spec without pre-configuration.

        Args:
            name: Unique name for this API (e.g., 'my-api')
            spec_url: URL to OpenAPI spec (JSON or YAML)
            base_url: Base URL for API calls (extracted from spec if not provided)
            auth_type: Authentication type ('bearer', 'header', 'basic', 'api_key', 'query')
            auth_header: Header name for auth (default: 'Authorization')
            auth_prefix: Prefix for auth value (default: 'Bearer')
            api_key: API key (optional, can also use config() later)

        Returns:
            Number of operations discovered

        Example:
            # Register from OpenAPI search
            results = await client.search("notion")
            count = await client.register("notion", spec_url=results[0]["spec_url"])

            # Register custom API
            await client.register(
                "my-api",
                spec_url="https://api.example.com/openapi.json",
                api_key="secret"
            )
        """
        from .models import AuthType, ProviderConfig
        from .providers import PROVIDER_CONFIGS

        # Create dynamic provider config
        auth_type_enum = AuthType(auth_type) if auth_type in [e.value for e in AuthType] else AuthType.BEARER

        config = ProviderConfig(
            name=name,
            display_name=name.replace("-", " ").replace("_", " ").title(),
            base_url=base_url or "",
            auth_type=auth_type_enum,
            auth_header=auth_header,
            auth_prefix=auth_prefix,
            spec_url=spec_url,
            env_vars=[],
        )

        # Add to provider configs
        PROVIDER_CONFIGS[name] = config

        # Set credentials if provided
        if api_key:
            await self.config(name, api_key=api_key, base_url=base_url)

        # Load spec
        if spec_url:
            return await self.spec(name, spec_url=spec_url)

        return 0

    async def overview(self, provider: str, compact: bool = True) -> str:
        """Get a human-readable overview of an API.

        Generates agent-friendly, token-efficient summaries. For large APIs,
        automatically minifies output to reduce token usage.

        Args:
            provider: Provider name (must have spec loaded)
            compact: Use compact format (default True for token efficiency)

        Returns:
            Formatted overview of all endpoints

        Example:
            await client.spec("cloudflare")
            print(await client.overview("cloudflare"))
        """
        openapi_client = await self._get_openapi_client(provider)

        if not openapi_client.spec_loaded:
            await openapi_client.load_spec()

        result = openapi_client.list_operations()
        base_url = openapi_client.base_url or ""

        # Build operation items
        items = []
        for op in result.operations:
            # Get full operation for parameters
            try:
                full_op = openapi_client.get_operation(op.operation_id)
                # Build query params string
                query_params = [
                    f"{p.name}={p.schema_type}"
                    for p in full_op.parameters
                    if p.location.value == "query"
                ]
                query_string = f"?{'&'.join(query_params)}" if query_params else ""
            except Exception:
                query_string = ""

            items.append({
                "operation_id": op.operation_id,
                "method": op.method,
                "path": op.path,
                "query_string": query_string,
                "summary": op.summary or "",
            })

        # Check if we need minified output (>10k chars ≈ 2500 tokens)
        is_large = len(str(items)) > 10000

        lines = []

        # Header
        lines.append(f"# {provider.upper()} API")
        if base_url:
            lines.append(f"Base: {base_url}")
        lines.append(f"Endpoints: {result.total_count}")
        lines.append("")

        if compact or is_large:
            # Minified format for agents
            for item in items:
                if is_large:
                    # Super compact: just operation_id and summary
                    summary_part = f" - {item['summary']}" if item['summary'] else ""
                    lines.append(f"- {item['operation_id']}{summary_part}")
                else:
                    # Compact: include method and path
                    summary_part = f" - {item['summary']}" if item['summary'] else ""
                    lines.append(
                        f"- {item['operation_id']}: {item['method']} {item['path']}{item['query_string']}{summary_part}"
                    )
        else:
            # Full format grouped by tag
            tags: dict[str, list] = {}
            for op in result.operations:
                for tag in op.tags or ["Other"]:
                    if tag not in tags:
                        tags[tag] = []
                    tags[tag].append(op)

            for tag_name in sorted(tags.keys()):
                tag_ops = tags[tag_name]
                lines.append(f"## {tag_name}")
                lines.append("")
                for op in tag_ops:
                    lines.append(f"- **{op.method}** `{op.path}` - {op.summary or op.operation_id}")
                lines.append("")

        # Footer with help
        lines.append("")
        lines.append(f"Use 'api ops {provider} --search <term>' for filtered list")
        lines.append(f"Use 'api call {provider} <operation_id>' to call an endpoint")

        return "\n".join(lines)

    # =========================================================================
    # Preloading
    # =========================================================================

    async def preload_specs(
        self,
        providers: list[str] | None = None,
        concurrent: int = 5,
    ) -> dict[str, int]:
        """Preload and cache OpenAPI specs for faster first use.

        Args:
            providers: List of provider names to preload. If None, preloads
                      all providers with spec_url configured.
            concurrent: Max concurrent downloads (default 5)

        Returns:
            Dict mapping provider name to operation count (or -1 if failed)

        Example:
            # Preload all configured specs
            results = await client.preload_specs()
            print(f"Preloaded {len(results)} specs")

            # Preload specific providers
            await client.preload_specs(["cloudflare", "github", "openai"])
        """
        import asyncio
        from .providers import PROVIDER_CONFIGS

        # Determine which providers to preload
        if providers is None:
            providers = [
                name for name, config in PROVIDER_CONFIGS.items()
                if config.spec_url
            ]

        results: dict[str, int] = {}
        semaphore = asyncio.Semaphore(concurrent)

        async def preload_one(provider: str) -> tuple[str, int]:
            async with semaphore:
                try:
                    count = await self.spec(provider)
                    logger.info(f"Preloaded {provider}: {count} operations")
                    return (provider, count)
                except Exception as e:
                    logger.warning(f"Failed to preload {provider}: {e}")
                    return (provider, -1)

        tasks = [preload_one(p) for p in providers]
        completed = await asyncio.gather(*tasks)

        for name, count in completed:
            results[name] = count

        return results

    @classmethod
    async def preload_common(cls) -> "APIClient":
        """Create a client with common specs preloaded.

        Returns a client with cloudflare, github, stripe, openai, notion
        specs already cached.

        Example:
            client = await APIClient.preload_common()
            # Now all common specs are cached
        """
        client = cls()
        await client.preload_specs([
            "cloudflare",
            "github",
            "stripe",
            "openai",
            "notion",
            "groq",
        ])
        return client

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def close(self) -> None:
        """Close all HTTP clients."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    async def __aenter__(self) -> "APIClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


# =============================================================================
# Module-level singleton
# =============================================================================

_default_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get the default API client instance."""
    global _default_client
    if _default_client is None:
        _default_client = APIClient()
    return _default_client


def reset_api_client() -> None:
    """Reset the default API client (for testing)."""
    global _default_client
    _default_client = None
