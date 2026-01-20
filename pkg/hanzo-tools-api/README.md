# hanzo-tools-api

Generic API tool for calling any REST API via OpenAPI specs.

## Features

- **Credential Management**: Securely store and manage API keys with env var fallback
- **OpenAPI Support**: Parse OpenAPI 3.x specs to discover and call operations
- **Auto-Detection**: Automatically detects credentials from environment variables
- **Multi-Provider**: Built-in support for 30+ cloud providers
- **Raw Requests**: Make raw HTTP requests when you need more control

## Installation

```bash
pip install hanzo-tools-api
```

## Quick Start

### Using Environment Variables (Recommended)

Set your API keys as environment variables:

```bash
export CLOUDFLARE_API_TOKEN=your-token
export GITHUB_TOKEN=ghp_xxx
export STRIPE_API_KEY=sk_xxx
```

The tool automatically detects these when you make calls.

### Using the Tool

```python
from hanzo_tools.api import APITool

tool = APITool()

# List available providers and their status
await tool.call(ctx, action="list")

# Configure a provider manually
await tool.call(ctx, 
    action="config",
    provider="cloudflare",
    api_key="your-key"
)

# Load OpenAPI spec for a provider
await tool.call(ctx, action="spec", provider="cloudflare")

# List available operations
await tool.call(ctx, action="ops", provider="cloudflare", search="zones")

# Call an operation
await tool.call(ctx,
    action="call",
    provider="cloudflare",
    operation="listZones"
)

# Make a raw request
await tool.call(ctx,
    action="raw",
    provider="github",
    method="GET",
    path="/user/repos"
)
```

### MCP Tool Usage

When registered with hanzo-mcp, use like:

```
api                                    # List all providers
api --action config --provider github --api_key ghp_xxx
api --action ops --provider cloudflare --search zones
api --action call --provider cloudflare --operation listZones
api --action raw --provider github --method GET --path /user/repos
```

## Supported Providers

Built-in configurations for:

| Provider | Env Variables |
|----------|---------------|
| Cloudflare | `CLOUDFLARE_API_TOKEN`, `CF_API_TOKEN` |
| GitHub | `GITHUB_TOKEN`, `GH_TOKEN` |
| Stripe | `STRIPE_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Vercel | `VERCEL_TOKEN` |
| DigitalOcean | `DIGITALOCEAN_TOKEN`, `DO_TOKEN` |
| Fly.io | `FLY_API_TOKEN` |
| Supabase | `SUPABASE_API_KEY` |
| AWS | `AWS_ACCESS_KEY_ID` |
| GCP | `GOOGLE_API_KEY` |
| Azure | `AZURE_API_KEY` |
| Slack | `SLACK_TOKEN` |
| Discord | `DISCORD_TOKEN` |
| ... and more |

## API Reference

### Actions

- **list**: Show all providers and their configuration status
- **config**: Set credentials for a provider
- **delete**: Remove credentials for a provider  
- **spec**: Load/refresh OpenAPI spec for a provider
- **ops**: List available operations for a provider
- **call**: Call an API operation by operation ID
- **raw**: Make a raw HTTP request to any endpoint

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | Action to perform (default: "list") |
| `provider` | str | Provider name (e.g., "cloudflare") |
| `api_key` | str | API key for config action |
| `api_secret` | str | API secret (if needed) |
| `account_id` | str | Account/org ID |
| `base_url` | str | Override base URL |
| `spec_url` | str | URL to OpenAPI spec |
| `operation` | str | Operation ID for call action |
| `params` | str | JSON parameters |
| `body` | str | JSON request body |
| `method` | str | HTTP method for raw action |
| `path` | str | URL path for raw action |
| `search` | str | Search filter for ops action |
| `tag` | str | Tag filter for ops action |

## Credential Storage

Credentials are stored in `~/.hanzo/api/credentials.json` with basic obfuscation.
For production use, consider using system keyring or a secrets manager.

OpenAPI specs are cached in `~/.hanzo/api/specs/`.

## Adding Custom Providers

You can add any provider by providing a base URL and API key:

```python
from hanzo_tools.api import get_credential_manager

cred_manager = get_credential_manager()
cred_manager.set_credential(
    provider="custom-api",
    api_key="your-key",
    base_url="https://api.custom.com/v1"
)
```

Then load a spec:

```python
from hanzo_tools.api import get_client

client = await get_client(
    "custom-api",
    spec_url="https://api.custom.com/openapi.json"
)
```

## Security Notes

- API keys are stored with basic base64 obfuscation (not encryption)
- Credentials file has restrictive permissions (0600)
- Environment variables are preferred for sensitive credentials
- Never commit credentials to version control

## License

MIT
