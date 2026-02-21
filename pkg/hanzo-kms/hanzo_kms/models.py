"""
Hanzo KMS - Data models for the SDK

Pydantic models for API requests and responses.
Compatible with Infisical API schema.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Authentication Models
# =============================================================================


class UniversalAuthMethod(BaseModel):
    """Universal authentication using client credentials."""

    client_id: str = Field(..., description="Client ID from KMS")
    client_secret: str = Field(..., description="Client secret from KMS")


class AWSIamAuthMethod(BaseModel):
    """AWS IAM authentication."""

    identity_id: str = Field(..., description="Identity ID in KMS")


class AzureAuthMethod(BaseModel):
    """Azure AD authentication."""

    identity_id: str = Field(..., description="Identity ID in KMS")
    resource: Optional[str] = Field(None, description="Azure resource")


class GCPIamAuthMethod(BaseModel):
    """GCP IAM authentication."""

    identity_id: str = Field(..., description="Identity ID in KMS")
    service_account_key_file_path: str = Field(..., description="Path to service account key")


class GCPIDTokenAuthMethod(BaseModel):
    """GCP ID Token authentication."""

    identity_id: str = Field(..., description="Identity ID in KMS")


class KubernetesAuthMethod(BaseModel):
    """Kubernetes service account authentication."""

    identity_id: str = Field(..., description="Identity ID in KMS")
    service_account_token_path: str = Field(
        "/var/run/secrets/kubernetes.io/serviceaccount/token",
        description="Path to service account token",
    )


class AuthenticationOptions(BaseModel):
    """Authentication configuration - use one method."""

    universal_auth: Optional[UniversalAuthMethod] = None
    aws_iam: Optional[AWSIamAuthMethod] = None
    azure: Optional[AzureAuthMethod] = None
    gcp_iam: Optional[GCPIamAuthMethod] = None
    gcp_id_token: Optional[GCPIDTokenAuthMethod] = None
    kubernetes: Optional[KubernetesAuthMethod] = None


# =============================================================================
# Client Settings
# =============================================================================


class ClientSettings(BaseModel):
    """Client configuration settings."""

    site_url: str = Field("https://kms.hanzo.ai", description="KMS API URL")
    organization: str = Field("hanzo", description="Organization name for multi-tenancy")
    auth: Optional[AuthenticationOptions] = Field(None, description="Authentication options")
    user_agent: str = Field("hanzo-kms-python", description="User agent string")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")


# =============================================================================
# Secret Models
# =============================================================================


class SecretElement(BaseModel):
    """A secret from KMS."""

    id: str = Field(..., description="Secret ID")
    secret_key: str = Field(..., alias="secretKey", description="Secret key/name")
    secret_value: str = Field(..., alias="secretValue", description="Secret value")
    secret_comment: Optional[str] = Field(None, alias="secretComment", description="Comment")
    version: int = Field(1, description="Secret version")
    type: str = Field("shared", description="Secret type")
    environment: str = Field(..., description="Environment slug")
    workspace: str = Field(..., description="Workspace/project ID")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True


# =============================================================================
# Request Options
# =============================================================================


class GetSecretOptions(BaseModel):
    """Options for getting a single secret."""

    project_id: str = Field(..., description="Project ID or slug")
    environment: str = Field(..., description="Environment slug")
    secret_name: str = Field(..., description="Secret key/name")
    path: str = Field("/", description="Secret path")
    type: str = Field("shared", description="Secret type")
    include_imports: bool = Field(True, description="Include imported secrets")


class ListSecretsOptions(BaseModel):
    """Options for listing secrets."""

    project_id: str = Field(..., description="Project ID or slug")
    environment: str = Field(..., description="Environment slug")
    path: str = Field("/", description="Secret path")
    include_imports: bool = Field(True, description="Include imported secrets")
    recursive: bool = Field(False, description="Recursively fetch from subpaths")
    expand_secret_references: bool = Field(True, description="Expand ${} references")
    attach_to_process_env: bool = Field(False, description="Set as environment variables")


class CreateSecretOptions(BaseModel):
    """Options for creating a secret."""

    project_id: str = Field(..., description="Project ID or slug")
    environment: str = Field(..., description="Environment slug")
    secret_name: str = Field(..., description="Secret key/name")
    secret_value: str = Field(..., description="Secret value")
    secret_comment: Optional[str] = Field(None, description="Comment")
    path: str = Field("/", description="Secret path")
    type: str = Field("shared", description="Secret type")


class UpdateSecretOptions(BaseModel):
    """Options for updating a secret."""

    project_id: str = Field(..., description="Project ID or slug")
    environment: str = Field(..., description="Environment slug")
    secret_name: str = Field(..., description="Secret key/name")
    secret_value: str = Field(..., description="New secret value")
    secret_comment: Optional[str] = Field(None, description="Comment")
    path: str = Field("/", description="Secret path")
    type: str = Field("shared", description="Secret type")


class DeleteSecretOptions(BaseModel):
    """Options for deleting a secret."""

    project_id: str = Field(..., description="Project ID or slug")
    environment: str = Field(..., description="Environment slug")
    secret_name: str = Field(..., description="Secret key/name")
    path: str = Field("/", description="Secret path")
    type: str = Field("shared", description="Secret type")


# =============================================================================
# Response Models
# =============================================================================


class TokenResponse(BaseModel):
    """Access token response from authentication."""

    access_token: str = Field(..., alias="accessToken")
    expires_in: int = Field(..., alias="expiresIn")
    token_type: str = Field("Bearer", alias="tokenType")

    class Config:
        populate_by_name = True


class SecretsResponse(BaseModel):
    """Response containing list of secrets."""

    secrets: list[SecretElement]
    imports: Optional[list[Any]] = None


class SecretResponse(BaseModel):
    """Response containing a single secret."""

    secret: SecretElement
