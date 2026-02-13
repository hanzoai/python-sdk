# hanzo-iam

Identity and Access Management SDK for the Hanzo ecosystem. Built on Casdoor with organization-aware multi-tenancy.

## Installation

```bash
pip install hanzo-iam
```

With FastAPI integration:

```bash
pip install hanzo-iam[fastapi]
```

With KMS support for certificate management:

```bash
pip install hanzo-iam[kms]
```

## Quick Start

```python
from hanzo_iam import IAMClient, IAMConfig

config = IAMConfig(
    endpoint="https://iam.hanzo.ai",
    client_id="your-client-id",
    client_secret="your-client-secret",
    org_name="HANZO",
)

client = IAMClient(config)

# Get authorization URL for user login
auth_url = client.get_auth_url(redirect_uri="https://yourapp.com/callback")

# Exchange code for tokens
tokens = client.get_token(code="auth-code-from-callback")

# Get user info
user = client.get_user_info(access_token=tokens.access_token)
```

## Organizations

| Organization | Endpoint | Description |
|-------------|----------|-------------|
| HANZO | https://iam.hanzo.ai | Hanzo AI platform |
| ZOO | https://iam.zoo.dev | Zoo Labs Foundation |
| LUX | https://iam.lux.network | Lux blockchain network |
| PARS | https://iam.pars.dev | Pars development platform |

## Environment Variables

```bash
# Required
HANZO_IAM_ENDPOINT=https://iam.hanzo.ai
HANZO_IAM_CLIENT_ID=your-client-id
HANZO_IAM_CLIENT_SECRET=your-client-secret
HANZO_IAM_ORG_NAME=HANZO

# Optional
HANZO_IAM_APP_NAME=your-app
HANZO_IAM_CERTIFICATE=path/to/cert.pem
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends
from hanzo_iam.fastapi import IAMAuth, get_current_user
from hanzo_iam import IAMConfig, User

app = FastAPI()

config = IAMConfig.from_env()
auth = IAMAuth(config)

@app.get("/protected")
async def protected_route(user: User = Depends(auth.require_user)):
    return {"user": user.name, "org": user.owner}

@app.get("/optional")
async def optional_auth(user: User | None = Depends(auth.optional_user)):
    if user:
        return {"message": f"Hello, {user.name}"}
    return {"message": "Hello, anonymous"}
```

## Client Credentials Flow

For service-to-service authentication:

```python
from hanzo_iam import IAMClient, IAMConfig

config = IAMConfig(
    endpoint="https://iam.hanzo.ai",
    client_id="service-client-id",
    client_secret="service-client-secret",
    org_name="HANZO",
)

client = IAMClient(config)

# Get service token
tokens = client.get_client_credentials_token()

# Use token for API calls
headers = {"Authorization": f"Bearer {tokens.access_token}"}
```

## Async Client

```python
import asyncio
from hanzo_iam import AsyncIAMClient, IAMConfig

async def main():
    config = IAMConfig.from_env()
    client = AsyncIAMClient(config)

    # All methods are async
    tokens = await client.get_client_credentials_token()
    user = await client.get_user_info(tokens.access_token)

    print(f"Authenticated as: {user.name}")

asyncio.run(main())
```

## API Reference

| Method | Description |
|--------|-------------|
| `get_auth_url(redirect_uri, state, scope)` | Generate OAuth authorization URL |
| `get_token(code)` | Exchange authorization code for tokens |
| `refresh_token(refresh_token)` | Refresh access token |
| `get_client_credentials_token()` | Get token via client credentials flow |
| `get_user_info(access_token)` | Get user info from access token |
| `parse_jwt(token)` | Parse and validate JWT claims |
| `get_user(user_id)` | Get user by ID |
| `get_users()` | List all users in organization |
| `create_user(user)` | Create new user |
| `update_user(user)` | Update existing user |
| `delete_user(user_id)` | Delete user |
| `get_organizations()` | List organizations |
| `get_organization(name)` | Get organization by name |

## License

Apache-2.0
