# hanzoai-iam

Identity and Access Management SDK for the Hanzo ecosystem. Organization-aware multi-tenant IAM.

The PyPI distribution is `hanzoai-iam`; the import path is `hanzo_iam`.

## Installation

```bash
pip install hanzoai-iam
```

With FastAPI integration:

```bash
pip install hanzoai-iam[fastapi]
```

With KMS support for certificate management:

```bash
pip install hanzoai-iam[kms]
```

## The organization is never assumed

Every entry point names the tenant it serves, or refuses. There is no default:
a process that cannot say which organization it belongs to must not fall back
to another one — that is how a Zoo deployment ends up reading Hanzo's users.

```python
from hanzo_iam import IAMConfig

config = IAMConfig.from_env()          # raises unless IAM_ORG is set
config = IAMConfig(                    # or name it directly
    server_url="https://zoo.id",
    client_id="zoo-app",
    client_secret="...",
    organization="zoo",
)
```

## Quick Start

```python
from hanzo_iam import IAMClient, IAMConfig, verify

client = IAMClient(IAMConfig.from_env())

# Send the user to sign in
url = client.get_authorization_url(redirect_uri="https://yourapp.com/callback")

# Exchange the code for tokens
tokens = client.exchange_code(code, redirect_uri="https://yourapp.com/callback")

# Judge the token — signature, expiry and issuer, failing closed
result = verify(
    tokens.access_token,
    jwks_uri=client.config.jwks_uri,
    issuer=client.config.base_url,
)
if not result:
    raise SystemExit(f"{result.reason}: {result.detail}")
```

## Organizations

Each brand runs its own issuer. `Organization` maps the name to the host.

| Organization | Issuer | Description |
|-------------|--------|-------------|
| HANZO | https://hanzo.id | Hanzo AI platform |
| ZOO | https://zoo.id | Zoo Labs Foundation |
| LUX | https://lux.id | Lux blockchain network |
| PARS | https://pars.id | Pars development platform |

## Environment Variables

One canonical prefix — `IAM_*`. No upstream-brand aliases, no per-org variants.

```bash
# Required
IAM_ORG=zoo                  # the organization this process serves
IAM_ENDPOINT=https://zoo.id
IAM_CLIENT_ID=your-client-id
IAM_CLIENT_SECRET=your-client-secret

# Optional (defaults shown)
IAM_APP=app
IAM_CERT=path/to/cert.pem    # PEM file or inline PEM content
```

## Verifying a token

`hanzo_iam.tokens.verify` is the one place a credential is judged. It fails
closed: an unreachable JWKS is not a pass, and an opaque (non-JWT) credential
reports `OPAQUE` rather than pretending to be valid.

```python
from hanzo_iam import verify

result = verify(token, jwks_uri=..., issuer=..., audience=...)
result.valid     # bool — True only if a published key signed it
result.reason    # ok | expired | bad_signature | wrong_issuer | jwks_unreachable | opaque | ...
result.claims    # decoded claims, only when valid
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends
from hanzo_iam import IAMConfig, JWTClaims, UserInfo
from hanzo_iam.fastapi import configure, require_auth, get_current_user

app = FastAPI()
configure(IAMConfig.from_env())   # or configure() to read IAM_* directly

@app.get("/protected")
async def protected(claims: JWTClaims = Depends(require_auth)):
    return {"user": claims.sub}

@app.get("/me")
async def me(user: UserInfo = Depends(get_current_user)):
    return {"email": user.email, "org": user.owner}
```

Also available: `get_token`, `require_token`, `get_token_claims`,
`get_optional_user`, `require_org`, `require_admin`, `require_role`.

## Browser Login (CLI)

`hanzo_iam.oauth.login` runs the loopback + PKCE flow; `hanzo_iam.store`
persists the result to the OS keyring, falling back to a 0600 file.

```python
from hanzo_iam import login, store

token_data = login(server_url="https://hanzo.id", client_id="hanzo-app", organization="hanzo")
store.save(token_data)
```

## Client Credentials Flow

For service-to-service authentication. The confidential-client pair is sent as
RFC 6749 §2.3.1 `client_secret_basic` — never in a query string.

```python
from hanzo_iam import IAMClient, IAMConfig

client = IAMClient(IAMConfig.from_env())
tokens = client.client_credentials()
headers = {"Authorization": f"Bearer {tokens.access_token}"}
```

## API Reference

`IAMClient` — one HTTP client, talking to the issuer directly.

| Method | Description |
|--------|-------------|
| `get_authorization_url(redirect_uri, state, scope, ...)` | Build the OAuth2 authorization URL |
| `exchange_code(code, redirect_uri, code_verifier)` | Exchange an authorization code for tokens |
| `refresh_token(refresh_token)` | Refresh an access token |
| `client_credentials(scope)` | Get a token via the client credentials flow |
| `introspect_token(token)` | Introspect a token at the server (RFC 7662) |
| `get_openid_configuration()` / `get_jwks()` | OIDC discovery and signing keys |
| `get_user_info(access_token)` | OIDC UserInfo for the bearer |
| `get_user(user_id)` / `get_users(owner=None)` | Read one user, or list a tenant's users |
| `create_user(user)` / `update_user(user)` / `delete_user(user)` | User writes |
| `get_organizations(owner="admin")` / `get_organization(name)` | Organizations |
| `get_applications(owner="admin")` / `get_application()` / `update_application(app)` | Applications |
| `get_providers(owner="admin")` / `get_roles(owner=None)` | Providers and roles |
| `login(username, password)` | Password sign-in |
| `close()` | Release the HTTP connection pool |

Every org-scoped read takes an `owner`. IAM honours it or refuses it — a named
owner is never silently reinterpreted into a different tenant.

## License

Apache-2.0
