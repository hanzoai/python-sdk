"""Pydantic models for hanzo-tools-api.

Provides strongly-typed, structured data objects for:
- API call results
- Operations and parameters
- Credentials and provider configs
- Tool schemas for agent integration
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums
# =============================================================================


class AuthType(str, Enum):
    """Authentication type for API providers."""

    BEARER = "bearer"  # Authorization: Bearer <token>
    BASIC = "basic"  # Basic auth (username:password)
    HEADER = "header"  # Custom header (e.g., x-api-key)
    API_KEY = "api_key"  # X-API-Key header
    QUERY = "query"  # Query parameter


class CredentialSource(str, Enum):
    """Source of credential resolution."""

    OVERRIDE = "override"  # Per-call override
    MEMORY = "memory"  # In-memory config
    STORED = "stored"  # File storage
    ENVIRONMENT = "environment"  # Environment variable
    NONE = "none"  # Not found


class ParameterLocation(str, Enum):
    """Location of API parameter."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


# =============================================================================
# Credential Models
# =============================================================================


class Credential(BaseModel):
    """API credential for a provider."""

    model_config = ConfigDict(frozen=False)

    provider: str = Field(description="Provider name")
    api_key: Optional[str] = Field(default=None, description="API key or token")
    api_secret: Optional[str] = Field(default=None, description="API secret (if needed)")
    account_id: Optional[str] = Field(default=None, description="Account/organization ID")
    base_url: Optional[str] = Field(default=None, description="Custom base URL override")
    extra: dict[str, Any] = Field(default_factory=dict, description="Provider-specific fields")

    @property
    def has_credentials(self) -> bool:
        """Check if credential has at least an API key."""
        return bool(self.api_key)


class EffectiveCredential(BaseModel):
    """Resolved credential with source information."""

    model_config = ConfigDict(frozen=True)

    credential: Credential
    source: CredentialSource = Field(description="Where the credential was resolved from")
    env_var_used: Optional[str] = Field(default=None, description="Environment variable used (if any)")

    @property
    def has_credentials(self) -> bool:
        return self.credential.has_credentials


class ProviderConfig(BaseModel):
    """Provider-specific configuration."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Provider identifier")
    display_name: str = Field(description="Human-readable name")
    base_url: str = Field(description="Default base URL")
    auth_type: AuthType = Field(default=AuthType.BEARER, description="Authentication method")
    auth_header: str = Field(default="Authorization", description="Header name for auth")
    auth_prefix: str = Field(default="Bearer", description="Prefix for auth value")
    auth_query_param: str = Field(default="api_key", description="Query param for auth")
    spec_url: Optional[str] = Field(default=None, description="URL to OpenAPI spec")
    env_vars: list[str] = Field(default_factory=list, description="Environment variables to check")
    extra_headers: dict[str, str] = Field(default_factory=dict, description="Additional headers")


class ProviderStatus(BaseModel):
    """Status of a provider configuration."""

    model_config = ConfigDict(frozen=True)

    name: str
    display_name: str
    configured: bool = Field(description="Whether credentials are available")
    source: Optional[CredentialSource] = Field(default=None, description="Credential source")
    base_url: str
    has_spec: bool = Field(description="Whether OpenAPI spec is available")
    spec_cached: bool = Field(default=False, description="Whether spec is cached locally")
    spec_age_seconds: Optional[float] = Field(default=None, description="Age of cached spec")


# =============================================================================
# OpenAPI Operation Models
# =============================================================================


class Parameter(BaseModel):
    """API operation parameter."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Parameter name")
    location: ParameterLocation = Field(description="Where the parameter goes")
    required: bool = Field(default=False, description="Whether parameter is required")
    schema_type: str = Field(default="string", description="Parameter data type")
    description: str = Field(default="", description="Parameter description")
    default: Any = Field(default=None, description="Default value")
    enum: list[Any] = Field(default_factory=list, description="Allowed values")
    json_schema: Optional[dict[str, Any]] = Field(default=None, description="Full JSON schema")


class Operation(BaseModel):
    """API operation definition."""

    model_config = ConfigDict(frozen=True)

    operation_id: str = Field(description="Unique operation identifier")
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    path: str = Field(description="URL path pattern")
    summary: str = Field(default="", description="Short description")
    description: str = Field(default="", description="Detailed description")
    parameters: list[Parameter] = Field(default_factory=list, description="Operation parameters")
    request_body_schema: Optional[dict[str, Any]] = Field(default=None, description="Request body JSON schema")
    request_body_required: bool = Field(default=False, description="Whether request body is required")
    response_schema: Optional[dict[str, Any]] = Field(default=None, description="Response JSON schema")
    tags: list[str] = Field(default_factory=list, description="Operation tags")
    deprecated: bool = Field(default=False, description="Whether operation is deprecated")

    @property
    def params_schema(self) -> dict[str, Any]:
        """Get JSON schema for parameters."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.schema_type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            if param.json_schema:
                prop.update(param.json_schema)

            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def compact_repr(self) -> str:
        """Get compact representation for agent prompts."""
        return f"{self.operation_id}: {self.method} {self.path} - {self.summary}"


class OperationSummary(BaseModel):
    """Compact operation summary for agent discovery."""

    model_config = ConfigDict(frozen=True)

    operation_id: str
    method: str
    path: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    deprecated: bool = False

    @classmethod
    def from_operation(cls, op: Operation) -> "OperationSummary":
        return cls(
            operation_id=op.operation_id,
            method=op.method,
            path=op.path,
            summary=op.summary,
            tags=op.tags,
            deprecated=op.deprecated,
        )


# =============================================================================
# API Call Result Models
# =============================================================================


class APICallResult(BaseModel):
    """Structured result from an API call."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(description="Whether the call succeeded (2xx status)")
    status_code: int = Field(description="HTTP status code")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    body: Any = Field(default=None, description="Response body (parsed JSON or raw text)")
    raw_body: Optional[str] = Field(default=None, description="Raw response body")
    elapsed_ms: Optional[float] = Field(default=None, description="Request duration in milliseconds")
    request_id: Optional[str] = Field(default=None, description="Request ID from headers")

    # Metadata
    provider: str = Field(description="Provider that was called")
    operation_id: Optional[str] = Field(default=None, description="Operation ID (if using spec)")
    method: str = Field(description="HTTP method used")
    url: str = Field(description="Full URL that was called")

    @property
    def data(self) -> Any:
        """Alias for body for backwards compatibility."""
        return self.body

    @property
    def is_error(self) -> bool:
        """Check if response indicates an error."""
        return self.status_code >= 400

    def raise_for_status(self) -> None:
        """Raise APIError if response indicates an error."""
        if self.is_error:
            from .errors import APIError

            raise APIError(
                message=f"API call failed with status {self.status_code}",
                status_code=self.status_code,
                body=self.body,
                provider=self.provider,
            )


# =============================================================================
# Spec Cache Models
# =============================================================================


class SpecCacheEntry(BaseModel):
    """Cached OpenAPI spec entry."""

    model_config = ConfigDict(frozen=False)

    provider: str
    spec: dict[str, Any]
    fetched_at: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    source_url: Optional[str] = None

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.fetched_at).total_seconds()

    @property
    def is_stale(self) -> bool:
        """Check if cache is stale (>24 hours)."""
        return self.age_seconds > 86400


# =============================================================================
# Tool Schema Models (for agent integration)
# =============================================================================


class ToolParameter(BaseModel):
    """Parameter definition for tool schema."""

    model_config = ConfigDict(frozen=True)

    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[list[str]] = None


class ToolSchema(BaseModel):
    """Machine-readable tool schema for agent integration."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Tool/method name")
    description: str = Field(description="What the tool does")
    parameters: list[ToolParameter] = Field(default_factory=list)
    returns: str = Field(description="Return type description")
    examples: list[str] = Field(default_factory=list, description="Example usage")

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON schema format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


# =============================================================================
# List/Discovery Results
# =============================================================================


class ProviderListResult(BaseModel):
    """Result of listing providers."""

    model_config = ConfigDict(frozen=True)

    providers: list[ProviderStatus]
    configured_count: int
    total_count: int

    @property
    def configured(self) -> list[ProviderStatus]:
        """Get only configured providers."""
        return [p for p in self.providers if p.configured]

    @property
    def unconfigured(self) -> list[ProviderStatus]:
        """Get only unconfigured providers."""
        return [p for p in self.providers if not p.configured]


class OperationListResult(BaseModel):
    """Result of listing operations."""

    model_config = ConfigDict(frozen=True)

    provider: str
    operations: list[OperationSummary]
    total_count: int
    filter_applied: Optional[str] = None

    def by_tag(self) -> dict[str, list[OperationSummary]]:
        """Group operations by tag."""
        result: dict[str, list[OperationSummary]] = {}
        for op in self.operations:
            for tag in op.tags or ["untagged"]:
                if tag not in result:
                    result[tag] = []
                result[tag].append(op)
        return result
