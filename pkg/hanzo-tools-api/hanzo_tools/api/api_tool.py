"""Unified API tool for calling any REST API.

This is a thin MCP wrapper over APIClient. The real logic lives in client.py.

Provides a single tool interface for:
- Managing API credentials
- Loading OpenAPI specs
- Calling API operations
- Making raw HTTP requests
"""

import json
import logging
from typing import Annotated, Any, Optional, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

from .client import APIClient, get_api_client
from .models import APICallResult, OperationListResult, ProviderListResult
from .errors import APIError

logger = logging.getLogger(__name__)


def _format_provider_list(result: ProviderListResult) -> str:
    """Format provider list for display."""
    lines = ["=== API Providers ===", ""]

    configured = [p for p in result.providers if p.configured]
    unconfigured = [p for p in result.providers if not p.configured]

    if configured:
        lines.append("Configured:")
        for p in sorted(configured, key=lambda x: x.name):
            source = f"[{p.source.value}]" if p.source else ""
            lines.append(f"  {p.name}: {p.display_name} {source}")

    if unconfigured:
        lines.append("\nAvailable (not configured):")
        for p in sorted(unconfigured, key=lambda x: x.name)[:20]:  # Limit display
            lines.append(f"  {p.name}: {p.display_name}")
        if len(unconfigured) > 20:
            lines.append(f"  ... and {len(unconfigured) - 20} more")

    lines.append("")
    lines.append(f"Total: {result.total_count} providers, {result.configured_count} configured")
    lines.append("")
    lines.append("Use 'api --provider <name>' for details")
    lines.append("Use 'api --action config --provider <name> --api_key <key>' to configure")

    return "\n".join(lines)


def _format_operation_list(result: OperationListResult, provider: str) -> str:
    """Format operation list for display."""
    if not result.operations:
        return f"No operations found for {provider}. Try loading the spec first."

    lines = [f"=== {provider} Operations ==="]

    # Group by tag
    tags: dict[str, list] = {}
    for op in result.operations:
        for t in op.tags or ["untagged"]:
            if t not in tags:
                tags[t] = []
            tags[t].append(op)

    for tag_name, tag_ops in sorted(tags.items()):
        lines.append(f"\n[{tag_name}]")
        for op in tag_ops[:10]:  # Limit per tag
            lines.append(f"  {op.operation_id}: {op.method} {op.path}")
            if op.summary:
                lines.append(f"    {op.summary[:80]}")
        if len(tag_ops) > 10:
            lines.append(f"  ... and {len(tag_ops) - 10} more")

    lines.append(f"\nTotal: {result.total_count} operations")
    if tags:
        lines.append(f"Tags: {', '.join(sorted(tags.keys()))}")

    return "\n".join(lines)


def _format_api_result(result: APICallResult) -> str:
    """Format API call result for display."""
    lines = [f"Status: {result.status_code} {'✓' if result.success else '✗'}"]

    if result.body is not None:
        if isinstance(result.body, dict):
            formatted = json.dumps(result.body, indent=2)
        else:
            formatted = str(result.body)

        # Truncate if too long
        if len(formatted) > 5000:
            formatted = formatted[:5000] + "\n... (truncated)"

        lines.append("")
        lines.append(formatted)

    return "\n".join(lines)


@final
class APITool(BaseTool):
    """Unified tool for calling any REST API.

    This is a thin wrapper over APIClient. See client.py for the real logic.

    Actions:
    - list: List available/configured providers
    - config: Configure credentials for a provider
    - delete: Remove stored credentials
    - spec: Load/refresh OpenAPI spec
    - ops: List available operations for a provider
    - call: Call an API operation
    - raw: Make a raw HTTP request
    """

    name = "api"

    def __init__(self, client: Optional[APIClient] = None):
        """Initialize with optional client."""
        self._client = client

    @property
    def client(self) -> APIClient:
        """Get the API client (lazy initialization)."""
        if self._client is None:
            self._client = get_api_client()
        return self._client

    @property
    @override
    def description(self) -> str:
        return """Generic API tool for calling any REST API via OpenAPI specs.

Supports searching, exploring, and dynamically using ANY public API.

Actions:
- list: Show all providers and their configuration status
- config: Set credentials for a provider
- delete: Remove credentials for a provider
- spec: Load/refresh OpenAPI spec for a provider
- ops: List available operations for a provider
- call: Call an API operation by ID
- raw: Make a raw HTTP request to any endpoint
- search: Search for APIs in public registries (openapisearch.com)
- register: Register a custom API from any OpenAPI spec URL
- overview: Get agent-friendly overview of an API
- preload: Download and cache common OpenAPI specs

DISCOVER ANY API:
  api --action search --search notion
  api --action register --provider notion --spec_url <url>
  api --action overview --provider notion
  api --action call --provider notion --operation <op>

BUILT-IN PROVIDERS:
Auto-detects credentials from environment variables:
- Cloudflare: CLOUDFLARE_API_TOKEN, CF_API_TOKEN, CLOUDFLARE_API_KEY
- GitHub: GITHUB_TOKEN, GH_TOKEN
- Stripe: STRIPE_API_KEY, STRIPE_SECRET_KEY
- OpenAI: OPENAI_API_KEY
- Anthropic: ANTHROPIC_API_KEY
- etc. (26+ providers)

Configure manually:
  api --action config --provider cloudflare --api_key "your-key"

MAKING CALLS:
  api --action call --provider cloudflare --operation zones-get
  api --action raw --provider github --method GET --path /user

Examples:
  api                                         # List all providers
  api --action search --search weather        # Search for weather APIs
  api --action register --provider petstore --spec_url https://petstore.swagger.io/v2/swagger.json
  api --action overview --provider cloudflare # Agent-friendly summary
  api --action ops --provider cloudflare --search zones
  api --action call --provider cloudflare --operation zones-get
"""

    @override
    @auto_timeout("api")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "list",
        provider: Optional[str] = None,
        # Config params
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: Optional[str] = None,
        # Spec params
        spec_url: Optional[str] = None,
        force_refresh: bool = False,
        # Operation params
        operation: Optional[str] = None,
        params: Optional[str] = None,  # JSON string
        body: Optional[str] = None,  # JSON string
        # Raw call params
        method: str = "GET",
        path: Optional[str] = None,
        # List/search params
        search: Optional[str] = None,
        tag: Optional[str] = None,
        configured_only: bool = False,
        **kwargs,
    ) -> str:
        """Execute API action."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        try:
            if action == "list":
                return await self._handle_list(provider, configured_only)

            elif action == "config":
                return await self._handle_config(
                    provider, api_key, api_secret, account_id, base_url
                )

            elif action == "delete":
                return await self._handle_delete(provider)

            elif action == "spec":
                return await self._handle_spec(provider, spec_url, force_refresh)

            elif action == "ops":
                return await self._handle_ops(provider, search, tag)

            elif action == "call":
                return await self._handle_call(provider, operation, params, body)

            elif action == "raw":
                return await self._handle_raw(provider, method, path, params, body)

            elif action == "search":
                return await self._handle_search(search)

            elif action == "register":
                return await self._handle_register(
                    provider, spec_url, base_url, api_key, kwargs.get("auth_type", "bearer")
                )

            elif action == "overview":
                return await self._handle_overview(provider)

            elif action == "preload":
                return await self._handle_preload()

            else:
                return f"Unknown action: {action}. Valid: list, config, delete, spec, ops, call, raw, search, register, overview, preload"

        except APIError as e:
            # Structured error with hints
            return str(e)
        except Exception as e:
            logger.exception(f"API tool error: {e}")
            return f"Error: {e}"

    async def _handle_list(self, provider: Optional[str], configured_only: bool) -> str:
        """List providers and their status."""
        if provider:
            # Show details for specific provider
            try:
                status = await self.client.get_provider(provider)
                lines = [f"=== {provider} ==="]
                lines.append(f"Display name: {status.display_name}")
                lines.append(f"Configured: {status.configured}")
                if status.source:
                    lines.append(f"Source: {status.source.value}")
                if status.base_url:
                    lines.append(f"Base URL: {status.base_url}")
                if status.auth_type:
                    lines.append(f"Auth type: {status.auth_type}")
                if status.spec_url:
                    lines.append(f"Spec URL: {status.spec_url}")
                if status.env_vars:
                    lines.append(f"Env vars: {', '.join(status.env_vars)}")
                return "\n".join(lines)
            except Exception as e:
                return f"Error getting provider info: {e}"

        # List all providers
        result = await self.client.list_providers(configured_only=configured_only)
        return _format_provider_list(result)

    async def _handle_config(
        self,
        provider: Optional[str],
        api_key: Optional[str],
        api_secret: Optional[str],
        account_id: Optional[str],
        base_url: Optional[str],
    ) -> str:
        """Configure credentials for a provider."""
        if not provider:
            return "Error: --provider required for config action"

        if not api_key:
            return "Error: --api_key required for config action"

        await self.client.config(
            provider=provider,
            api_key=api_key,
            api_secret=api_secret,
            account_id=account_id,
            base_url=base_url,
        )

        return f"Configured credentials for {provider}"

    async def _handle_delete(self, provider: Optional[str]) -> str:
        """Delete credentials for a provider."""
        if not provider:
            return "Error: --provider required for delete action"

        if await self.client.delete_config(provider):
            return f"Deleted credentials for {provider}"
        return f"No stored credentials for {provider}"

    async def _handle_spec(
        self,
        provider: Optional[str],
        spec_url: Optional[str],
        force_refresh: bool,
    ) -> str:
        """Load or refresh OpenAPI spec."""
        if not provider:
            return "Error: --provider required for spec action"

        try:
            count = await self.client.spec(
                provider=provider,
                spec_url=spec_url,
                force_refresh=force_refresh,
            )
            return f"Loaded spec for {provider}: {count} operations"
        except Exception as e:
            return f"Error loading spec: {e}"

    async def _handle_ops(
        self,
        provider: Optional[str],
        search: Optional[str],
        tag: Optional[str],
    ) -> str:
        """List operations for a provider."""
        if not provider:
            return "Error: --provider required for ops action"

        try:
            result = await self.client.ops(
                provider=provider,
                search=search,
                tag=tag,
            )
            return _format_operation_list(result, provider)
        except Exception as e:
            return f"Error listing operations: {e}"

    async def _handle_call(
        self,
        provider: Optional[str],
        operation: Optional[str],
        params: Optional[str],
        body: Optional[str],
    ) -> str:
        """Call an API operation."""
        if not provider:
            return "Error: --provider required for call action"
        if not operation:
            return "Error: --operation required for call action"

        try:
            # Parse params and body
            parsed_params = json.loads(params) if params else None
            parsed_body = json.loads(body) if body else None

            result = await self.client.call(
                provider=provider,
                operation_id=operation,
                params=parsed_params,
                body=parsed_body,
            )

            return _format_api_result(result)

        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"
        except Exception as e:
            return f"Error calling operation: {e}"

    async def _handle_raw(
        self,
        provider: Optional[str],
        method: str,
        path: Optional[str],
        params: Optional[str],
        body: Optional[str],
    ) -> str:
        """Make a raw API request."""
        if not provider:
            return "Error: --provider required for raw action"
        if not path:
            return "Error: --path required for raw action"

        try:
            # Parse params and body
            parsed_params = json.loads(params) if params else None
            parsed_body = json.loads(body) if body else None

            result = await self.client.raw(
                provider=provider,
                method=method,
                path=path,
                params=parsed_params,
                body=parsed_body,
            )

            return _format_api_result(result)

        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"
        except Exception as e:
            return f"Error making request: {e}"

    async def _handle_search(self, query: Optional[str]) -> str:
        """Search for APIs in public registries."""
        if not query:
            return "Error: --search <query> required for search action"

        try:
            results = await self.client.search(query)

            if not results:
                return f"No APIs found matching '{query}'"

            lines = [f"=== API Search: {query} ===", ""]
            for r in results[:20]:  # Limit results
                name = r.get("name") or r.get("id", "Unknown")
                desc = r.get("description", "")[:60]
                spec_url = r.get("spec_url", "")
                lines.append(f"  {r.get('id', name)}: {name}")
                if desc:
                    lines.append(f"    {desc}")
                if spec_url:
                    lines.append(f"    Spec: {spec_url}")
                lines.append("")

            lines.append(f"Found {len(results)} API(s)")
            lines.append("")
            lines.append("To use an API:")
            lines.append("  api --action register --provider <id> --spec_url <url>")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching: {e}"

    async def _handle_register(
        self,
        name: Optional[str],
        spec_url: Optional[str],
        base_url: Optional[str],
        api_key: Optional[str],
        auth_type: str,
    ) -> str:
        """Register a custom API provider."""
        if not name:
            return "Error: --provider <name> required for register action"

        if not spec_url:
            return "Error: --spec_url required for register action"

        try:
            count = await self.client.register(
                name=name,
                spec_url=spec_url,
                base_url=base_url,
                api_key=api_key,
                auth_type=auth_type,
            )

            lines = [
                f"Registered API: {name}",
                f"Loaded {count} operations from spec",
                "",
                "Next steps:",
                f"  api --action overview --provider {name}",
                f"  api --action ops --provider {name}",
            ]

            if not api_key:
                lines.append(f"  api --action config --provider {name} --api_key <your-key>")

            return "\n".join(lines)

        except Exception as e:
            return f"Error registering API: {e}"

    async def _handle_overview(self, provider: Optional[str]) -> str:
        """Get API overview."""
        if not provider:
            return "Error: --provider required for overview action"

        try:
            return await self.client.overview(provider)
        except Exception as e:
            return f"Error getting overview: {e}"

    async def _handle_preload(self) -> str:
        """Preload and cache common OpenAPI specs."""
        try:
            results = await self.client.preload_specs()

            lines = ["=== Preloading OpenAPI Specs ===", ""]

            success = []
            failed = []
            for name, count in sorted(results.items()):
                if count >= 0:
                    success.append(f"  {name}: {count} operations")
                else:
                    failed.append(f"  {name}: failed")

            if success:
                lines.append("Loaded:")
                lines.extend(success)

            if failed:
                lines.append("\nFailed:")
                lines.extend(failed)

            lines.append(f"\nTotal: {len(success)} loaded, {len(failed)} failed")
            lines.append(f"Cache: ~/.hanzo/api/specs/")

            return "\n".join(lines)

        except Exception as e:
            return f"Error preloading specs: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def api(
            action: Annotated[
                str,
                Field(
                    description="Action: list, config, delete, spec, ops, call, raw",
                    default="list",
                ),
            ] = "list",
            provider: Annotated[
                Optional[str],
                Field(description="Provider name (e.g., cloudflare, github)"),
            ] = None,
            api_key: Annotated[
                Optional[str],
                Field(description="API key or token for config action"),
            ] = None,
            api_secret: Annotated[
                Optional[str],
                Field(description="API secret (if needed) for config action"),
            ] = None,
            account_id: Annotated[
                Optional[str],
                Field(description="Account/org ID for config action"),
            ] = None,
            base_url: Annotated[
                Optional[str],
                Field(description="Override base URL for provider"),
            ] = None,
            spec_url: Annotated[
                Optional[str],
                Field(description="URL to OpenAPI spec for spec action"),
            ] = None,
            force_refresh: Annotated[
                bool,
                Field(description="Force refresh cached spec"),
            ] = False,
            operation: Annotated[
                Optional[str],
                Field(description="Operation ID for call action"),
            ] = None,
            params: Annotated[
                Optional[str],
                Field(description="JSON parameters for call/raw action"),
            ] = None,
            body: Annotated[
                Optional[str],
                Field(description="JSON body for call/raw action"),
            ] = None,
            method: Annotated[
                str,
                Field(description="HTTP method for raw action"),
            ] = "GET",
            path: Annotated[
                Optional[str],
                Field(description="URL path for raw action"),
            ] = None,
            search: Annotated[
                Optional[str],
                Field(description="Search filter for ops action"),
            ] = None,
            tag: Annotated[
                Optional[str],
                Field(description="Tag filter for ops action"),
            ] = None,
            configured_only: Annotated[
                bool,
                Field(description="Only list configured providers"),
            ] = False,
            ctx: MCPContext = None,
        ) -> str:
            """Generic API tool for calling any REST API via OpenAPI specs.

            Manage credentials and call APIs for various cloud providers.
            Auto-detects credentials from environment variables.

            Actions:
            - list: Show all providers and their status
            - config: Set credentials for a provider
            - delete: Remove credentials for a provider
            - spec: Load/refresh OpenAPI spec for a provider
            - ops: List available operations for a provider
            - call: Call an API operation by operation ID
            - raw: Make a raw HTTP request
            """
            return await tool_instance.call(
                ctx,
                action=action,
                provider=provider,
                api_key=api_key,
                api_secret=api_secret,
                account_id=account_id,
                base_url=base_url,
                spec_url=spec_url,
                force_refresh=force_refresh,
                operation=operation,
                params=params,
                body=body,
                method=method,
                path=path,
                search=search,
                tag=tag,
                configured_only=configured_only,
            )
