# Hanzo KMS - Python SDK

Official Python SDK for [Hanzo KMS](https://kms.hanzo.ai) — secret management for your applications.

The server is [luxfi/kms](https://github.com/luxfi/kms); this SDK speaks its
canonical `/v1/kms` surface and nothing else.

## Installation

```bash
pip install hanzo-kms
```

Or with uv:

```bash
uv add hanzo-kms
```

## Quick Start

A secret is identified by **(org, path, name, env)**. The org scopes both the
URL and the JWT; path, name and env identify the value.

```python
from hanzo_kms import ClientSettings, KMSClient

client = KMSClient(ClientSettings(
    org="lux",
    client_id="your-client-id",
    client_secret="your-client-secret",
))

# List the secret names at a path
names = client.list_secrets("providers/lux", env="prod")

# Read one value
mnemonic = client.get_secret("providers/lux", "deploy-mnemonic", env="prod")

# Create or replace — one upsert; KMS holds one value per (path, name, env)
client.put_secret("providers/lux", "deploy-mnemonic", mnemonic, env="prod")

# Delete
client.delete_secret("providers/lux", "deploy-mnemonic", env="prod")

# Load a whole path into os.environ, keyed by secret name
client.inject_env("providers/lux", env="prod")
```

`env` defaults to `"default"`.

## Async

`AsyncKMSClient` is the mirror image of `KMSClient` — same methods, same
arguments.

```python
from hanzo_kms import AsyncKMSClient

async with AsyncKMSClient() as client:
    names = await client.list_secrets("providers/lux", env="prod")
```

## Environment Variables

```bash
export HANZO_KMS_URL="https://kms.hanzo.ai"   # default
export HANZO_KMS_ORG="hanzo"                  # default
export HANZO_KMS_CLIENT_ID="your-client-id"
export HANZO_KMS_CLIENT_SECRET="your-client-secret"
# ...or a pre-issued IAM bearer token instead of client credentials:
export HANZO_KMS_TOKEN="eyJ..."
```

Then:

```python
from hanzo_kms import KMSClient

client = KMSClient()  # configures itself from the environment
```

## Authentication

Two ways, because the server has one login route:

| Setting | Behavior |
|---------|----------|
| `client_id` + `client_secret` | Exchanged at `POST /v1/kms/auth/login` for a bearer token |
| `access_token` | A pre-issued IAM bearer token, used as-is |

The AWS / Azure / GCP / Kubernetes / SRP methods this SDK used to advertise
were Infisical's. luxfi/kms has never served them.

## CLI

```bash
hanzo-kms list --path providers/lux --env prod
hanzo-kms get providers/lux deploy-mnemonic --env prod
hanzo-kms set providers/lux deploy-mnemonic "word word ..." --env prod
hanzo-kms delete providers/lux deploy-mnemonic --env prod
hanzo-kms export --path providers/lux --env prod --format json
```

## API Reference

### KMSClient

| Method | Description |
|--------|-------------|
| `list_secrets(path="", env="default")` | Secret **names** at a path |
| `get_secret(path, name, env="default")` | The secret's value |
| `put_secret(path, name, value, env="default")` | Create or replace |
| `delete_secret(path, name, env="default")` | Delete |
| `inject_env(path="", env="default", overwrite=False)` | Load a path into `os.environ` |
| `health()` | `{"service": "kms", "status": "ok"}` |

## Server surface

```
POST   /v1/kms/auth/login                            {clientId, clientSecret} -> {accessToken, expiresIn}
GET    /v1/kms/orgs/{org}/secrets?path=&env=         -> {"names": [...]}
GET    /v1/kms/orgs/{org}/secrets/{path}/{name}?env= -> {"secret": {"value": "..."}}
POST   /v1/kms/orgs/{org}/secrets                    {path, name, env, value}
DELETE /v1/kms/orgs/{org}/secrets/{path}/{name}?env=
GET    /healthz | /v1/kms/healthz                    -> {"service": "kms", "status": "ok"}
```

Two things follow from it:

- **The server splits the trailing path at its LAST slash** into `(path, name)`.
  A name may not contain `/` — this SDK rejects one rather than let a write
  land under a key the matching read can never find.
- **There is no versioned read.** KMS holds exactly one value per
  (path, name, env), so `get_secret(..., version=N)` raises
  `VersionUnsupportedError` instead of quietly handing back the current value.

## Compatibility

- Hanzo KMS — https://kms.hanzo.ai
- Lux KMS — https://kms.lux.cloud

## License

MIT License - see [LICENSE](LICENSE) for details.
