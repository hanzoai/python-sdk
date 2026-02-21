"""Structured errors for hanzo-tools-api.

Provides detailed error objects with hints for resolution,
making it easy for agents to understand and recover from errors.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class APIErrorInfo(BaseModel):
    """Structured error information."""

    error_type: str = Field(description="Error category")
    message: str = Field(description="Human-readable error message")
    provider: str | None = Field(default=None, description="Provider involved")
    operation_id: str | None = Field(default=None, description="Operation involved")
    status_code: int | None = Field(default=None, description="HTTP status code")
    missing_fields: list[str] = Field(default_factory=list, description="Required fields that are missing")
    hint: str | None = Field(default=None, description="Suggested fix")
    env_vars: list[str] = Field(default_factory=list, description="Environment variables to set")
    config_command: str | None = Field(default=None, description="CLI command to fix")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")


class APIError(Exception):
    """Base exception for API errors with structured info."""

    def __init__(
        self,
        message: str,
        error_type: str = "api_error",
        provider: str | None = None,
        operation_id: str | None = None,
        status_code: int | None = None,
        body: Any = None,
        hint: str | None = None,
        missing_fields: list[str] | None = None,
        env_vars: list[str] | None = None,
        config_command: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_type = error_type
        self.provider = provider
        self.operation_id = operation_id
        self.status_code = status_code
        self.body = body
        self.hint = hint
        self.missing_fields = missing_fields or []
        self.env_vars = env_vars or []
        self.config_command = config_command
        self.details = details

        super().__init__(message)

    @property
    def info(self) -> APIErrorInfo:
        """Get structured error info."""
        return APIErrorInfo(
            error_type=self.error_type,
            message=self.message,
            provider=self.provider,
            operation_id=self.operation_id,
            status_code=self.status_code,
            missing_fields=self.missing_fields,
            hint=self.hint,
            env_vars=self.env_vars,
            config_command=self.config_command,
            details=self.details,
        )

    def __str__(self) -> str:
        parts = [self.message]
        if self.hint:
            parts.append(f"Hint: {self.hint}")
        if self.env_vars:
            parts.append(f"Try setting: {', '.join(self.env_vars)}")
        if self.config_command:
            parts.append(f"Or run: {self.config_command}")
        return "\n".join(parts)


class CredentialError(APIError):
    """Error related to credentials."""

    def __init__(
        self,
        message: str,
        provider: str,
        missing_fields: list[str] | None = None,
        env_vars: list[str] | None = None,
    ):
        config_cmd = f'api config --provider {provider} --api_key "YOUR_KEY"'
        hint = f"Configure credentials for {provider}"

        super().__init__(
            message=message,
            error_type="credential_error",
            provider=provider,
            missing_fields=missing_fields or ["api_key"],
            hint=hint,
            env_vars=env_vars or [],
            config_command=config_cmd,
        )


class ProviderNotFoundError(APIError):
    """Provider is not recognized."""

    def __init__(self, provider: str, available_providers: list[str] | None = None):
        hint = None
        if available_providers:
            hint = f"Available providers: {', '.join(available_providers[:10])}"

        super().__init__(
            message=f"Unknown provider: {provider}",
            error_type="provider_not_found",
            provider=provider,
            hint=hint,
            details={"available_providers": available_providers} if available_providers else None,
        )


class OperationNotFoundError(APIError):
    """Operation is not found in the spec."""

    def __init__(
        self,
        operation_id: str,
        provider: str,
        similar_operations: list[str] | None = None,
    ):
        hint = None
        if similar_operations:
            hint = f"Similar operations: {', '.join(similar_operations[:5])}"
        else:
            hint = f"Run 'api ops --provider {provider}' to list available operations"

        super().__init__(
            message=f"Operation not found: {operation_id}",
            error_type="operation_not_found",
            provider=provider,
            operation_id=operation_id,
            hint=hint,
            details={"similar_operations": similar_operations} if similar_operations else None,
        )


class SpecNotLoadedError(APIError):
    """OpenAPI spec has not been loaded."""

    def __init__(self, provider: str):
        super().__init__(
            message=f"OpenAPI spec not loaded for {provider}",
            error_type="spec_not_loaded",
            provider=provider,
            hint=f"Load the spec first with 'api spec --provider {provider}'",
            config_command=f"api spec --provider {provider}",
        )


class SpecParseError(APIError):
    """Error parsing OpenAPI spec."""

    def __init__(
        self,
        message: str,
        provider: str,
        path_in_spec: str | None = None,
        parse_error: str | None = None,
    ):
        details = {}
        if path_in_spec:
            details["path_in_spec"] = path_in_spec
        if parse_error:
            details["parse_error"] = parse_error

        super().__init__(
            message=message,
            error_type="spec_parse_error",
            provider=provider,
            hint="The OpenAPI spec may be invalid or use unsupported features",
            details=details if details else None,
        )


class ParameterValidationError(APIError):
    """Parameter validation failed."""

    def __init__(
        self,
        message: str,
        provider: str,
        operation_id: str,
        missing_params: list[str] | None = None,
        invalid_params: dict[str, str] | None = None,
    ):
        details = {}
        if missing_params:
            details["missing_params"] = missing_params
        if invalid_params:
            details["invalid_params"] = invalid_params

        hint_parts = []
        if missing_params:
            hint_parts.append(f"Missing required params: {', '.join(missing_params)}")
        if invalid_params:
            for param, reason in invalid_params.items():
                hint_parts.append(f"{param}: {reason}")

        super().__init__(
            message=message,
            error_type="parameter_validation_error",
            provider=provider,
            operation_id=operation_id,
            missing_fields=missing_params or [],
            hint="; ".join(hint_parts) if hint_parts else None,
            details=details if details else None,
        )


class NetworkError(APIError):
    """Network-related error."""

    def __init__(
        self,
        message: str,
        provider: str,
        url: str | None = None,
        original_error: Exception | None = None,
    ):
        details = {}
        if url:
            details["url"] = url
        if original_error:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            error_type="network_error",
            provider=provider,
            hint="Check your network connection and the provider's API status",
            details=details if details else None,
        )


class RateLimitError(APIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: int | None = None,
        status_code: int = 429,
    ):
        hint = "Rate limit exceeded"
        if retry_after:
            hint = f"Rate limit exceeded. Retry after {retry_after} seconds"

        super().__init__(
            message=f"Rate limit exceeded for {provider}",
            error_type="rate_limit_error",
            provider=provider,
            status_code=status_code,
            hint=hint,
            details={"retry_after": retry_after} if retry_after else None,
        )


class AuthenticationError(APIError):
    """Authentication failed."""

    def __init__(
        self,
        provider: str,
        status_code: int = 401,
        env_vars: list[str] | None = None,
    ):
        super().__init__(
            message=f"Authentication failed for {provider}",
            error_type="authentication_error",
            provider=provider,
            status_code=status_code,
            hint="Check that your API key is valid and has the required permissions",
            env_vars=env_vars or [],
            config_command=f'api config --provider {provider} --api_key "YOUR_KEY"',
        )


class SpecLoadError(APIError):
    """Error loading OpenAPI spec."""

    def __init__(
        self,
        provider: str,
        spec_url: str | None = None,
        original_error: Exception | None = None,
    ):
        message = f"Failed to load OpenAPI spec for {provider}"
        if spec_url:
            message = f"Failed to load OpenAPI spec from {spec_url}"

        details = {}
        if spec_url:
            details["spec_url"] = spec_url
        if original_error:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            error_type="spec_load_error",
            provider=provider,
            hint="Check the spec URL is accessible and returns valid OpenAPI JSON/YAML",
            details=details if details else None,
        )


class ValidationError(APIError):
    """General validation error."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation_id: str | None = None,
        field: str | None = None,
        value: Any = None,
        expected: str | None = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if expected:
            details["expected"] = expected

        hint = None
        if field and expected:
            hint = f"Field '{field}' should be {expected}"
        elif field:
            hint = f"Invalid value for field '{field}'"

        super().__init__(
            message=message,
            error_type="validation_error",
            provider=provider,
            operation_id=operation_id,
            hint=hint,
            details=details if details else None,
        )
