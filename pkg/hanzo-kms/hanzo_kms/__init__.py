"""Hanzo KMS - Secret Management SDK for Python

A pure Python SDK for the canonical luxfi/kms surface (kms.hanzo.ai,
kms.lux.network). A secret is identified by (org, path, name, env).

Usage:
    from hanzo_kms import KMSClient, ClientSettings

    client = KMSClient(ClientSettings(
        org="lux",
        client_id="your-client-id",
        client_secret="your-client-secret",
    ))

    # List the secret names at a path
    names = client.list_secrets("providers/lux", env="prod")

    # Read one value
    mnemonic = client.get_secret("providers/lux", "deploy-mnemonic", env="prod")

    # Create or replace (one upsert — KMS holds one value per path/name/env)
    client.put_secret("providers/lux", "deploy-mnemonic", mnemonic, env="prod")

    # Load a whole path into os.environ
    client.inject_env("providers/lux", env="prod")

With HANZO_KMS_ORG / HANZO_KMS_CLIENT_ID / HANZO_KMS_CLIENT_SECRET set,
`KMSClient()` configures itself.
"""

__version__ = "1.1.1"

from .async_client import AsyncKMSClient
from .client import KMSClient
from .models import ClientSettings, TokenResponse, settings_from_env
from .routes import DEFAULT_ENV, VersionUnsupportedError

__all__ = [
    "KMSClient",
    "AsyncKMSClient",
    "ClientSettings",
    "settings_from_env",
    "TokenResponse",
    "DEFAULT_ENV",
    "VersionUnsupportedError",
]
