"""OpenAPI client with smart caching and spec normalization.

Provides:
- Spec fetching with ETag/Last-Modified caching
- Robust spec normalization (handles messy specs)
- Operation discovery with filtering
- Parameter validation
"""

from __future__ import annotations

import json
import logging
import re
import time
import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlencode

import httpx
import yaml
import aiofiles

from .models import (
    APICallResult,
    Credential,
    Operation,
    OperationSummary,
    OperationListResult,
    Parameter,
    ParameterLocation,
    ProviderConfig,
    SpecCacheEntry,
)
from .credentials import CredentialManager, get_credential_manager
from .providers import get_provider_config
from .errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    OperationNotFoundError,
    ParameterValidationError,
    RateLimitError,
    SpecNotLoadedError,
    SpecParseError,
)

logger = logging.getLogger(__name__)


class SpecCache:
    """Smart OpenAPI spec caching with ETag support."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize spec cache.

        Args:
            cache_dir: Directory for cached specs. Defaults to ~/.hanzo/api/specs/
        """
        self.cache_dir = cache_dir or Path.home() / ".hanzo" / "api" / "specs"
        self._memory_cache: dict[str, SpecCacheEntry] = {}

    def _ensure_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, provider: str) -> Path:
        """Get cache file path for provider."""
        return self.cache_dir / f"{provider}.json"

    def _meta_path(self, provider: str) -> Path:
        """Get metadata file path for provider."""
        return self.cache_dir / f"{provider}.meta.json"

    def has_spec(self, provider: str) -> bool:
        """Check if spec is cached for provider."""
        if provider in self._memory_cache:
            return True
        return self._cache_path(provider).exists()

    def spec_age(self, provider: str) -> Optional[float]:
        """Get age of cached spec in seconds."""
        if provider in self._memory_cache:
            return self._memory_cache[provider].age_seconds

        cache_path = self._cache_path(provider)
        if cache_path.exists():
            return time.time() - cache_path.stat().st_mtime
        return None

    def is_stale(self, provider: str, max_age: float = 86400) -> bool:
        """Check if spec is stale (default: 24 hours)."""
        age = self.spec_age(provider)
        if age is None:
            return True
        return age > max_age

    async def get(self, provider: str) -> Optional[SpecCacheEntry]:
        """Get cached spec entry."""
        # Check memory cache
        if provider in self._memory_cache:
            return self._memory_cache[provider]

        # Check file cache
        cache_path = self._cache_path(provider)
        meta_path = self._meta_path(provider)

        if cache_path.exists():
            try:
                async with aiofiles.open(cache_path, "r") as f:
                    spec = json.loads(await f.read())

                # Load metadata
                etag = None
                last_modified = None
                source_url = None
                fetched_at = datetime.fromtimestamp(cache_path.stat().st_mtime)

                if meta_path.exists():
                    async with aiofiles.open(meta_path, "r") as f:
                        meta = json.loads(await f.read())
                        etag = meta.get("etag")
                        last_modified = meta.get("last_modified")
                        source_url = meta.get("source_url")
                        if meta.get("fetched_at"):
                            fetched_at = datetime.fromisoformat(meta["fetched_at"])

                entry = SpecCacheEntry(
                    provider=provider,
                    spec=spec,
                    fetched_at=fetched_at,
                    etag=etag,
                    last_modified=last_modified,
                    source_url=source_url,
                )

                self._memory_cache[provider] = entry
                return entry

            except Exception as e:
                logger.warning(f"Failed to load cached spec for {provider}: {e}")

        return None

    async def set(
        self,
        provider: str,
        spec: dict,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> SpecCacheEntry:
        """Cache a spec."""
        self._ensure_dir()

        entry = SpecCacheEntry(
            provider=provider,
            spec=spec,
            fetched_at=datetime.now(),
            etag=etag,
            last_modified=last_modified,
            source_url=source_url,
        )

        # Save spec
        cache_path = self._cache_path(provider)
        async with aiofiles.open(cache_path, "w") as f:
            await f.write(json.dumps(spec, indent=2))

        # Save metadata
        meta_path = self._meta_path(provider)
        meta = {
            "etag": etag,
            "last_modified": last_modified,
            "source_url": source_url,
            "fetched_at": entry.fetched_at.isoformat(),
        }
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(meta, indent=2))

        self._memory_cache[provider] = entry
        return entry

    def invalidate(self, provider: str) -> None:
        """Remove cached spec for provider."""
        if provider in self._memory_cache:
            del self._memory_cache[provider]

        cache_path = self._cache_path(provider)
        meta_path = self._meta_path(provider)

        if cache_path.exists():
            cache_path.unlink()
        if meta_path.exists():
            meta_path.unlink()


class OpenAPIClient:
    """Client for making API calls based on OpenAPI specs."""

    def __init__(
        self,
        provider: str,
        base_url: Optional[str] = None,
        credential_manager: Optional[CredentialManager] = None,
        spec_cache: Optional[SpecCache] = None,
    ):
        """Initialize OpenAPI client.

        Args:
            provider: Provider name (e.g., 'cloudflare')
            base_url: Override base URL from spec
            credential_manager: Credential manager instance
            spec_cache: Spec cache instance
        """
        self.provider = provider
        self._base_url_override = base_url
        self._spec: Optional[dict] = None
        self._operations: dict[str, Operation] = {}
        self._parsed = False

        # Dependencies
        self.cred_manager = credential_manager or get_credential_manager()
        self.spec_cache = spec_cache or SpecCache()
        self.config = get_provider_config(provider)

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        if self._base_url_override:
            return self._base_url_override
        if self._spec:
            servers = self._spec.get("servers", [])
            if servers:
                return servers[0].get("url", "")
        if self.config:
            return self.config.base_url
        return ""

    @property
    def spec_loaded(self) -> bool:
        """Check if spec is loaded."""
        return self._spec is not None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # Spec Management
    # =========================================================================

    def has_spec(self) -> bool:
        """Check if spec is available (loaded or cached)."""
        return self._spec is not None or self.spec_cache.has_spec(self.provider)

    def spec_age(self) -> Optional[float]:
        """Get age of spec in seconds."""
        return self.spec_cache.spec_age(self.provider)

    async def refresh_spec(self, force: bool = False) -> bool:
        """Refresh the OpenAPI spec.

        Args:
            force: Force refresh even if not stale

        Returns:
            True if spec was refreshed, False if using cache
        """
        # Check if refresh needed
        if not force and not self.spec_cache.is_stale(self.provider):
            cached = await self.spec_cache.get(self.provider)
            if cached:
                self._spec = cached.spec
                self._parse_spec()
                return False

        # Get spec URL
        spec_url = self.config.spec_url if self.config else None
        if not spec_url:
            # Try to load from cache
            cached = await self.spec_cache.get(self.provider)
            if cached:
                self._spec = cached.spec
                self._parse_spec()
                return False
            return False

        # Fetch with conditional request
        client = await self._get_client()
        headers = {}

        cached = await self.spec_cache.get(self.provider)
        if cached and not force:
            if cached.etag:
                headers["If-None-Match"] = cached.etag
            if cached.last_modified:
                headers["If-Modified-Since"] = cached.last_modified

        try:
            response = await client.get(spec_url, headers=headers)

            if response.status_code == 304:
                # Not modified, use cache
                if cached:
                    self._spec = cached.spec
                    self._parse_spec()
                return False

            response.raise_for_status()

            # Parse spec
            content = response.text
            if spec_url.endswith((".yaml", ".yml")):
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            # Cache it
            await self.spec_cache.set(
                self.provider,
                spec,
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                source_url=spec_url,
            )

            self._spec = spec
            self._parsed = False
            self._parse_spec()
            return True

        except Exception as e:
            logger.warning(f"Failed to fetch spec for {self.provider}: {e}")
            # Fall back to cache
            if cached:
                self._spec = cached.spec
                self._parse_spec()
            raise NetworkError(
                message=f"Failed to fetch OpenAPI spec: {e}",
                provider=self.provider,
                url=spec_url,
                original_error=e,
            )

    async def load_spec(self, spec_source: Optional[str] = None) -> None:
        """Load OpenAPI spec from various sources.

        Args:
            spec_source: URL or file path to spec. If None, uses provider config.
        """
        # If already loaded
        if self._spec:
            return

        # Try cache first
        cached = await self.spec_cache.get(self.provider)
        if cached and not self.spec_cache.is_stale(self.provider):
            self._spec = cached.spec
            self._parse_spec()
            return

        # Load from source
        if spec_source:
            if spec_source.startswith(("http://", "https://")):
                await self._load_spec_from_url(spec_source)
            else:
                await self._load_spec_from_file(spec_source)
        elif self.config and self.config.spec_url:
            await self.refresh_spec(force=True)
        elif cached:
            # Use stale cache if no other option
            self._spec = cached.spec
            self._parse_spec()

    async def _load_spec_from_url(self, url: str) -> None:
        """Load spec from URL."""
        client = await self._get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()

            content = response.text
            if url.endswith((".yaml", ".yml")):
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            await self.spec_cache.set(
                self.provider,
                spec,
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                source_url=url,
            )

            self._spec = spec
            self._parse_spec()

        except Exception as e:
            raise NetworkError(
                message=f"Failed to load spec from {url}: {e}",
                provider=self.provider,
                url=url,
                original_error=e,
            )

    async def _load_spec_from_file(self, path: str) -> None:
        """Load spec from local file."""
        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()

            if path.endswith((".yaml", ".yml")):
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            await self.spec_cache.set(self.provider, spec, source_url=f"file://{path}")
            self._spec = spec
            self._parse_spec()

        except Exception as e:
            raise SpecParseError(
                message=f"Failed to load spec from {path}: {e}",
                provider=self.provider,
            )

    def set_spec(self, spec: dict) -> None:
        """Set spec directly (for testing or inline specs)."""
        self._spec = spec
        self._parsed = False
        self._parse_spec()

    # =========================================================================
    # Spec Parsing
    # =========================================================================

    def _parse_spec(self) -> None:
        """Parse OpenAPI spec to extract operations."""
        if self._parsed or not self._spec:
            return

        self._operations.clear()
        paths = self._spec.get("paths", {})
        seen_ids: set[str] = set()

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Handle $ref at path level
            if "$ref" in path_item:
                resolved = self._resolve_ref(path_item["$ref"])
                if resolved:
                    path_item = resolved
                else:
                    continue

            # Common parameters for all methods in this path
            common_params = path_item.get("parameters", [])

            for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if method not in path_item:
                    continue

                op_data = path_item[method]
                if not isinstance(op_data, dict):
                    continue

                try:
                    operation = self._parse_operation(
                        path=path,
                        method=method,
                        op_data=op_data,
                        common_params=common_params,
                        seen_ids=seen_ids,
                    )
                    if operation:
                        self._operations[operation.operation_id] = operation
                        seen_ids.add(operation.operation_id)

                except Exception as e:
                    logger.warning(f"Failed to parse operation {method} {path}: {e}")

        self._parsed = True
        logger.debug(f"Parsed {len(self._operations)} operations for {self.provider}")

    def _parse_operation(
        self,
        path: str,
        method: str,
        op_data: dict,
        common_params: list,
        seen_ids: set[str],
    ) -> Optional[Operation]:
        """Parse a single operation."""
        # Generate unique operation ID
        op_id = op_data.get("operationId")

        if not op_id:
            # Generate deterministic ID from path and method
            clean_path = re.sub(r"[{}]", "", path)
            clean_path = re.sub(r"[^a-zA-Z0-9/]", "", clean_path)
            clean_path = clean_path.replace("/", "_").strip("_")
            op_id = f"{method}_{clean_path}" if clean_path else f"{method}_root"

        # Ensure uniqueness
        base_id = op_id
        counter = 1
        while op_id in seen_ids:
            op_id = f"{base_id}_{counter}"
            counter += 1

        # Parse parameters
        params = []
        all_params = common_params + op_data.get("parameters", [])

        for param_data in all_params:
            if "$ref" in param_data:
                param_data = self._resolve_ref(param_data["$ref"])
                if not param_data:
                    continue

            schema = param_data.get("schema", {})
            try:
                location = ParameterLocation(param_data.get("in", "query"))
            except ValueError:
                location = ParameterLocation.QUERY

            params.append(
                Parameter(
                    name=param_data.get("name", ""),
                    location=location,
                    required=param_data.get("required", False),
                    schema_type=schema.get("type", "string"),
                    description=param_data.get("description", ""),
                    default=schema.get("default"),
                    enum=schema.get("enum", []),
                    json_schema=schema if schema else None,
                )
            )

        # Parse request body
        request_body = op_data.get("requestBody", {})
        body_schema = None
        body_required = request_body.get("required", False)

        if request_body:
            content = request_body.get("content", {})
            # Prefer JSON
            json_content = content.get("application/json") or content.get("application/json; charset=utf-8")
            if json_content:
                body_schema = json_content.get("schema")
                if body_schema and "$ref" in body_schema:
                    body_schema = self._resolve_ref(body_schema["$ref"])

        # Parse response schema (200 response)
        response_schema = None
        responses = op_data.get("responses", {})
        for status in ["200", "201", "default"]:
            if status in responses:
                resp = responses[status]
                if "$ref" in resp:
                    resp = self._resolve_ref(resp["$ref"])
                if resp:
                    resp_content = resp.get("content", {})
                    json_resp = resp_content.get("application/json", {})
                    response_schema = json_resp.get("schema")
                    if response_schema and "$ref" in response_schema:
                        response_schema = self._resolve_ref(response_schema["$ref"])
                    break

        return Operation(
            operation_id=op_id,
            method=method.upper(),
            path=path,
            summary=op_data.get("summary", ""),
            description=op_data.get("description", ""),
            parameters=params,
            request_body_schema=body_schema,
            request_body_required=body_required,
            response_schema=response_schema,
            tags=op_data.get("tags", []),
            deprecated=op_data.get("deprecated", False),
        )

    def _resolve_ref(self, ref: str) -> Optional[dict]:
        """Resolve a JSON reference in the spec."""
        if not ref.startswith("#/"):
            return None

        parts = ref[2:].split("/")
        current = self._spec

        for part in parts:
            # Handle URL-encoded parts
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current if isinstance(current, dict) else None

    # =========================================================================
    # Operation Discovery
    # =========================================================================

    def list_operations(
        self,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        method: Optional[str] = None,
        path_contains: Optional[str] = None,
        operation_id_prefix: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> OperationListResult:
        """List available operations with filtering.

        Args:
            search: Search in operation ID, summary, description
            tag: Filter by tag
            method: Filter by HTTP method
            path_contains: Filter by path substring
            operation_id_prefix: Filter by operation ID prefix
            include_deprecated: Include deprecated operations

        Returns:
            OperationListResult with matching operations
        """
        ops = list(self._operations.values())

        # Apply filters
        if tag:
            tag_lower = tag.lower()
            ops = [op for op in ops if any(tag_lower in t.lower() for t in op.tags)]

        if method:
            method_upper = method.upper()
            ops = [op for op in ops if op.method == method_upper]

        if path_contains:
            ops = [op for op in ops if path_contains in op.path]

        if operation_id_prefix:
            ops = [op for op in ops if op.operation_id.startswith(operation_id_prefix)]

        if not include_deprecated:
            ops = [op for op in ops if not op.deprecated]

        if search:
            search_lower = search.lower()
            ops = [
                op
                for op in ops
                if search_lower in op.operation_id.lower()
                or search_lower in op.summary.lower()
                or search_lower in op.description.lower()
                or search_lower in op.path.lower()
            ]

        # Convert to summaries
        summaries = [OperationSummary.from_operation(op) for op in ops]

        filter_desc = None
        filters = []
        if search:
            filters.append(f"search={search}")
        if tag:
            filters.append(f"tag={tag}")
        if method:
            filters.append(f"method={method}")
        if path_contains:
            filters.append(f"path_contains={path_contains}")
        if filters:
            filter_desc = ", ".join(filters)

        return OperationListResult(
            provider=self.provider,
            operations=summaries,
            total_count=len(summaries),
            filter_applied=filter_desc,
        )

    def get_operation(self, operation_id: str) -> Operation:
        """Get a specific operation by ID.

        Args:
            operation_id: Operation ID

        Returns:
            Operation object

        Raises:
            OperationNotFoundError: If operation not found
        """
        op = self._operations.get(operation_id)
        if op:
            return op

        # Find similar operations
        similar = self._find_similar_operations(operation_id)
        raise OperationNotFoundError(
            operation_id=operation_id,
            provider=self.provider,
            similar_operations=similar,
        )

    def _find_similar_operations(self, operation_id: str, limit: int = 5) -> list[str]:
        """Find operations with similar IDs."""
        similarities = []
        for op_id in self._operations:
            ratio = SequenceMatcher(None, operation_id.lower(), op_id.lower()).ratio()
            similarities.append((op_id, ratio))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [op_id for op_id, _ in similarities[:limit] if _ > 0.3]

    # =========================================================================
    # API Calls
    # =========================================================================

    def _build_auth_headers(self, credential: Credential) -> dict[str, str]:
        """Build authentication headers based on provider config."""
        headers = {}

        if not credential.api_key:
            return headers

        config = self.config

        if config:
            auth_type = config.auth_type

            if auth_type.value == "bearer":
                prefix = config.auth_prefix or "Bearer"
                headers["Authorization"] = f"{prefix} {credential.api_key}".strip()

            elif auth_type.value == "basic":
                import base64

                secret = credential.api_secret or ""
                creds = base64.b64encode(f"{credential.api_key}:{secret}".encode()).decode()
                headers["Authorization"] = f"Basic {creds}"

            elif auth_type.value == "header":
                header_name = config.auth_header or "X-API-Key"
                prefix = config.auth_prefix or ""
                headers[header_name] = f"{prefix}{credential.api_key}".strip()

            elif auth_type.value == "api_key":
                headers["X-API-Key"] = credential.api_key

            # Add extra headers from config
            if config.extra_headers:
                headers.update(config.extra_headers)

        else:
            # Default to bearer token
            headers["Authorization"] = f"Bearer {credential.api_key}"

        return headers

    def _substitute_path_params(self, path: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Substitute path parameters and return remaining params."""
        remaining = dict(params)
        path_params = re.findall(r"\{(\w+)\}", path)

        for param in path_params:
            if param in remaining:
                path = path.replace(f"{{{param}}}", str(remaining.pop(param)))

        return path, remaining

    async def call(
        self,
        operation_id: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> APICallResult:
        """Call an API operation.

        Args:
            operation_id: Operation to call
            params: Path, query, and header parameters
            body: Request body (for POST/PUT/PATCH)
            headers: Additional headers
            dry_run: If True, don't actually make the request

        Returns:
            APICallResult with response data
        """
        if not self._spec:
            raise SpecNotLoadedError(self.provider)

        operation = self.get_operation(operation_id)

        # Validate required parameters
        params = params or {}
        self._validate_params(operation, params, body)

        # Get credentials
        credential = await self.cred_manager.require_credential(self.provider)

        # Build request
        request_headers = self._build_auth_headers(credential)
        request_headers["Content-Type"] = "application/json"
        request_headers["Accept"] = "application/json"
        if headers:
            request_headers.update(headers)

        # Process path parameters
        path, remaining_params = self._substitute_path_params(operation.path, params)

        # Separate query params
        query_params = {}
        for param in operation.parameters:
            if param.name in remaining_params:
                if param.location == ParameterLocation.QUERY:
                    query_params[param.name] = remaining_params[param.name]
                elif param.location == ParameterLocation.HEADER:
                    request_headers[param.name] = str(remaining_params[param.name])

        # Build URL
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        if dry_run:
            return APICallResult(
                success=True,
                status_code=0,
                headers={},
                body={"dry_run": True, "url": url, "method": operation.method},
                provider=self.provider,
                operation_id=operation_id,
                method=operation.method,
                url=url,
            )

        # Make request
        return await self._make_request(
            method=operation.method,
            url=url,
            headers=request_headers,
            body=body,
            operation_id=operation_id,
        )

    async def call_raw(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> APICallResult:
        """Make a raw API call without using operation definitions.

        Args:
            method: HTTP method
            path: URL path
            params: Query parameters
            body: Request body
            headers: Additional headers
            dry_run: If True, don't actually make the request

        Returns:
            APICallResult with response data
        """
        credential = await self.cred_manager.require_credential(self.provider)

        # Build headers
        request_headers = self._build_auth_headers(credential)
        request_headers["Content-Type"] = "application/json"
        request_headers["Accept"] = "application/json"
        if headers:
            request_headers.update(headers)

        # Build URL
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        if params:
            url = f"{url}?{urlencode(params)}"

        if dry_run:
            return APICallResult(
                success=True,
                status_code=0,
                headers={},
                body={"dry_run": True, "url": url, "method": method},
                provider=self.provider,
                method=method,
                url=url,
            )

        return await self._make_request(
            method=method,
            url=url,
            headers=request_headers,
            body=body,
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Optional[dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> APICallResult:
        """Make the actual HTTP request."""
        client = await self._get_client()
        method_lower = method.lower()

        start_time = time.time()

        try:
            request_kwargs: dict[str, Any] = {"headers": headers}
            if body and method_lower in ("post", "put", "patch"):
                request_kwargs["json"] = body

            response = await getattr(client, method_lower)(url, **request_kwargs)
            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                response_body = response.text

            result = APICallResult(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response_body,
                raw_body=response.text,
                elapsed_ms=elapsed_ms,
                request_id=response.headers.get("x-request-id"),
                provider=self.provider,
                operation_id=operation_id,
                method=method,
                url=url,
            )

            # Handle common error statuses
            if response.status_code == 401:
                raise AuthenticationError(
                    provider=self.provider,
                    status_code=401,
                    env_vars=self.config.env_vars if self.config else [],
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                raise RateLimitError(
                    provider=self.provider,
                    retry_after=int(retry_after) if retry_after else None,
                )

            return result

        except httpx.RequestError as e:
            raise NetworkError(
                message=f"Request failed: {e}",
                provider=self.provider,
                url=url,
                original_error=e,
            )

    def _validate_params(
        self,
        operation: Operation,
        params: dict[str, Any],
        body: Optional[dict[str, Any]],
    ) -> None:
        """Validate parameters against operation schema."""
        missing = []

        # Check required parameters
        for param in operation.parameters:
            if param.required and param.name not in params:
                # Check if it has a default
                if param.default is None:
                    missing.append(param.name)

        # Check required body
        if operation.request_body_required and not body:
            missing.append("request_body")

        if missing:
            raise ParameterValidationError(
                message=f"Missing required parameters: {', '.join(missing)}",
                provider=self.provider,
                operation_id=operation.operation_id,
                missing_params=missing,
            )


# =============================================================================
# Module-level helpers
# =============================================================================

_clients: dict[str, OpenAPIClient] = {}


async def get_client(provider: str, spec_url: Optional[str] = None) -> OpenAPIClient:
    """Get or create an OpenAPI client for a provider.

    Args:
        provider: Provider name
        spec_url: Optional URL to OpenAPI spec

    Returns:
        OpenAPIClient instance with spec loaded
    """
    if provider not in _clients:
        client = OpenAPIClient(provider)
        await client.load_spec(spec_url)
        _clients[provider] = client
    return _clients[provider]


def clear_clients() -> None:
    """Clear cached clients (for testing)."""
    _clients.clear()
