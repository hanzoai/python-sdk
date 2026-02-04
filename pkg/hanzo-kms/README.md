# Hanzo KMS - Python SDK

Official Python SDK for [Hanzo KMS](https://kms.hanzo.ai) - Secret management for your applications.

## Installation

```bash
pip install hanzo-kms
```

Or with uv:

```bash
uv add hanzo-kms
```

## Quick Start

```python
from hanzo_kms import KMSClient, ClientSettings, AuthenticationOptions, UniversalAuthMethod

# Initialize client
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
secrets = client.list_secrets(
    project_id="my-project",
    environment="production"
)

for secret in secrets:
    print(f"{secret.secret_key}: {secret.secret_value}")

# Get a specific secret
db_url = client.get_value(
    project_id="my-project",
    environment="production",
    secret_name="DATABASE_URL"
)

# Inject all secrets into environment
client.inject_env(
    project_id="my-project",
    environment="production"
)
```

## Environment Variables

The client can be configured via environment variables:

```bash
export HANZO_KMS_URL="https://kms.hanzo.ai"
export HANZO_KMS_CLIENT_ID="your-client-id"
export HANZO_KMS_CLIENT_SECRET="your-client-secret"
```

Then simply:

```python
from hanzo_kms import KMSClient

client = KMSClient()  # Uses environment variables
secrets = client.list_secrets("my-project", "production")
```

## Authentication Methods

### Universal Auth (Recommended)

```python
from hanzo_kms import KMSClient, ClientSettings, AuthenticationOptions, UniversalAuthMethod

client = KMSClient(ClientSettings(
    auth=AuthenticationOptions(
        universal_auth=UniversalAuthMethod(
            client_id="...",
            client_secret="...",
        )
    )
))
```

### Kubernetes Auth

For workloads running in Kubernetes:

```python
from hanzo_kms import KMSClient, ClientSettings, AuthenticationOptions, KubernetesAuthMethod

client = KMSClient(ClientSettings(
    auth=AuthenticationOptions(
        kubernetes=KubernetesAuthMethod(
            identity_id="your-identity-id",
            # Uses default service account token path
        )
    )
))
```

### AWS IAM Auth

```python
from hanzo_kms import KMSClient, ClientSettings, AuthenticationOptions, AWSIamAuthMethod

client = KMSClient(ClientSettings(
    auth=AuthenticationOptions(
        aws_iam=AWSIamAuthMethod(
            identity_id="your-identity-id",
        )
    )
))
```

## API Reference

### KMSClient

| Method | Description |
|--------|-------------|
| `list_secrets(project_id, environment, path="/")` | List all secrets |
| `get_secret(project_id, environment, secret_name)` | Get a single secret |
| `get_value(project_id, environment, secret_name, default=None)` | Get just the value |
| `create_secret(project_id, environment, secret_name, secret_value)` | Create a secret |
| `update_secret(project_id, environment, secret_name, secret_value)` | Update a secret |
| `delete_secret(project_id, environment, secret_name)` | Delete a secret |
| `inject_env(project_id, environment, overwrite=False)` | Inject into os.environ |

## Compatibility

This SDK is compatible with:
- Hanzo KMS (https://kms.hanzo.ai)
- Lux KMS (https://kms.lux.network)
- Infisical (https://infisical.com)

The `InfisicalClient` alias is provided for drop-in compatibility:

```python
from hanzo_kms import InfisicalClient  # Same as KMSClient
```

## License

MIT License - see [LICENSE](LICENSE) for details.
