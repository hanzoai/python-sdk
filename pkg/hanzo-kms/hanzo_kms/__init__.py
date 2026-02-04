"""
Hanzo KMS - Secret Management SDK for Python

A pure Python SDK for Hanzo/Lux KMS (compatible with Infisical API).

Usage:
    from hanzo_kms import KMSClient, ClientSettings, UniversalAuthMethod, AuthenticationOptions

    client = KMSClient(ClientSettings(
        site_url="https://kms.hanzo.ai",
        auth=AuthenticationOptions(
            universal_auth=UniversalAuthMethod(
                client_id="your-client-id",
                client_secret="your-client-secret",
            )
        )
    ))

    # List all secrets
    secrets = client.list_secrets(project_id="my-project", environment="production")

    # Get a specific secret
    secret = client.get_secret(
        project_id="my-project",
        environment="production",
        secret_name="DATABASE_URL"
    )
    print(secret.secret_value)

    # Inject secrets into environment
    client.inject_env(project_id="my-project", environment="production")
"""

__version__ = "1.0.0"

from .client import KMSClient
from .async_client import AsyncKMSClient
from .models import (
    AuthenticationOptions,
    AWSIamAuthMethod,
    AzureAuthMethod,
    ClientSettings,
    CreateSecretOptions,
    DeleteSecretOptions,
    GCPIamAuthMethod,
    GCPIDTokenAuthMethod,
    GetSecretOptions,
    KubernetesAuthMethod,
    ListSecretsOptions,
    SecretElement,
    UniversalAuthMethod,
    UpdateSecretOptions,
)

# Aliases for compatibility with infisical-python
InfisicalClient = KMSClient
AsyncInfisicalClient = AsyncKMSClient

__all__ = [
    # Main clients
    "KMSClient",
    "AsyncKMSClient",
    "InfisicalClient",  # Alias for compatibility
    "AsyncInfisicalClient",  # Async alias
    # Settings
    "ClientSettings",
    "AuthenticationOptions",
    # Auth methods
    "UniversalAuthMethod",
    "AWSIamAuthMethod",
    "AzureAuthMethod",
    "GCPIamAuthMethod",
    "GCPIDTokenAuthMethod",
    "KubernetesAuthMethod",
    # Options
    "GetSecretOptions",
    "ListSecretsOptions",
    "CreateSecretOptions",
    "UpdateSecretOptions",
    "DeleteSecretOptions",
    # Response types
    "SecretElement",
]
