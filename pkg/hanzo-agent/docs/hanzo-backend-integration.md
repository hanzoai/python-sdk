# Hanzo Agent SDK - Backend Integration Guide

This guide explains how to configure the Hanzo Agent SDK to work with your Hanzo AI infrastructure instead of calling OpenAI directly.

## Overview

The Hanzo Agent SDK can be configured to route all LLM requests through the Hanzo Router, which provides:

- **Unified Access**: Connect to 100+ LLM providers through a single API
- **Cost Management**: Track usage and costs across all models
- **Reliability**: Automatic fallbacks and load balancing
- **Observability**: Monitor all requests via the Cloud dashboard
- **Security**: Keep API keys secure in your infrastructure

## Quick Start

### 1. Install the SDK

```bash
pip install hanzoai
# or
uv pip install hanzoai
```

### 2. Configure Environment

```bash
# Local development
export HANZO_ROUTER_URL="http://localhost:4000/v1"
export HANZO_API_KEY="sk-1234"  # Get from Router dashboard

# Production
export HANZO_ROUTER_URL="https://router.your-domain.com/v1"
export HANZO_API_KEY="sk-production-key"
```

### 3. Basic Usage

```python
from openai import AsyncOpenAI
from agents import Agent, Runner, RunConfig, ModelProvider, Model
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

class HanzoModelProvider(ModelProvider):
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or "gpt-3.5-turbo",
            openai_client=self.client
        )

# Create provider
provider = HanzoModelProvider(
    base_url="http://localhost:4000/v1",
    api_key="your-router-api-key"
)

# Use with agents
agent = Agent(name="Assistant", instructions="Be helpful and concise.")
result = await Runner.run(
    agent,
    "Hello!",
    run_config=RunConfig(model_provider=provider)
)
```

## Supported Models

The Hanzo Router supports all major LLM providers:

### OpenAI Models
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`
- `gpt-3.5-turbo`
- `text-embedding-3-small`, `text-embedding-3-large`

### Anthropic Models
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### Open Models
- `meta-llama/Llama-3-70b-chat-hf`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`
- `google/gemma-7b-it`
- And many more...

## Advanced Configuration

### Custom Headers and Metadata

```python
class CustomHanzoProvider(ModelProvider):
    def __init__(self, base_url: str, api_key: str, user_id: str = None):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                "X-User-ID": user_id,
                "X-App-Name": "hanzo-agent-sdk"
            } if user_id else None
        )
```

### Model Routing Strategies

```python
# Use different models for different purposes
async def route_by_complexity(query: str) -> str:
    if len(query) < 50:  # Simple query
        model = "gpt-3.5-turbo"
    else:  # Complex query
        model = "gpt-4"
    
    result = await Runner.run(
        agent,
        query,
        run_config=RunConfig(
            model_provider=provider,
            model=model
        )
    )
    return result.final_output
```

### Error Handling and Fallbacks

```python
async def with_fallback(agent, query):
    providers = [
        ("gpt-4", primary_provider),
        ("claude-3-sonnet", fallback_provider),
        ("gpt-3.5-turbo", emergency_provider)
    ]
    
    for model, provider in providers:
        try:
            return await Runner.run(
                agent,
                query,
                run_config=RunConfig(
                    model_provider=provider,
                    model=model
                )
            )
        except Exception as e:
            print(f"Failed with {model}: {e}")
            continue
    
    raise Exception("All providers failed")
```

## Testing Your Integration

Run the test script to verify your setup:

```bash
# From the agent SDK directory
python test_hanzo_backend.py

# Or run the example
python examples/hanzo_backend_example.py
```

Expected output:
```
=== Checking Hanzo Router Health ===
✓ Router health check passed
✓ Available models: 150 found

=== Testing Basic Agent ===
✓ Basic test passed!
Response: 4

=== Testing Agent with Tools ===
✓ Tool test passed!
Response: The result of 15 * 23 is 345.
```

## Production Best Practices

### 1. API Key Management

Never hardcode API keys. Use environment variables or secret management:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HANZO_API_KEY")
if not api_key:
    raise ValueError("HANZO_API_KEY not found in environment")
```

### 2. Connection Pooling

Reuse the provider instance for better performance:

```python
# Create once
_hanzo_provider = None

def get_hanzo_provider():
    global _hanzo_provider
    if _hanzo_provider is None:
        _hanzo_provider = HanzoModelProvider(
            base_url=os.getenv("HANZO_ROUTER_URL"),
            api_key=os.getenv("HANZO_API_KEY")
        )
    return _hanzo_provider
```

### 3. Monitoring and Logging

```python
import logging

logger = logging.getLogger(__name__)

class MonitoredHanzoProvider(HanzoModelProvider):
    async def get_model(self, model_name: str | None) -> Model:
        start_time = time.time()
        try:
            model = await super().get_model(model_name)
            logger.info(f"Model {model_name} initialized in {time.time() - start_time:.2f}s")
            return model
        except Exception as e:
            logger.error(f"Failed to get model {model_name}: {e}")
            raise
```

### 4. Rate Limiting

The Router handles rate limiting, but you can add client-side controls:

```python
from asyncio import Semaphore

class RateLimitedProvider(HanzoModelProvider):
    def __init__(self, *args, max_concurrent=10, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore = Semaphore(max_concurrent)
    
    async def get_model(self, model_name: str | None) -> Model:
        async with self._semaphore:
            return await super().get_model(model_name)
```

## Troubleshooting

### Connection Errors

```
Cannot connect to Router: Cannot connect to host localhost:4000
```

**Solution**: Ensure the Router is running:
```bash
cd /path/to/hanzo/services
make start-router
# or
docker compose up router
```

### Authentication Errors

```
401 Unauthorized: Invalid API key
```

**Solution**: 
1. Generate a new API key from the Router dashboard
2. Update your environment variable: `export HANZO_API_KEY="new-key"`

### Model Not Found

```
404: Model 'gpt-5' not found
```

**Solution**: Check available models:
```bash
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer $HANZO_API_KEY"
```

## Integration with Other Hanzo Services

### Using with MCP (Model Context Protocol)

```python
# MCP tools can be integrated with agents
from hanzo_mcp import MCPClient

mcp_client = MCPClient()
tools = mcp_client.get_tools()

agent = Agent(
    name="MCPAgent",
    instructions="Use MCP tools to help users.",
    tools=tools
)
```

### Observability with Cloud Dashboard

All requests through the Router are automatically logged to the Cloud dashboard:

1. Access: http://localhost:3082 (local) or https://cloud.hanzo.ai (production)
2. View real-time metrics, costs, and traces
3. Set up alerts for errors or cost thresholds

## Next Steps

- Explore more [examples](../examples/)
- Read the [Agent SDK documentation](https://docs.hanzo.ai/agent-sdk)
- Join our [Discord community](https://discord.gg/hanzoai) for support

## Support

- GitHub Issues: https://github.com/hanzoai/agent/issues
- Documentation: https://docs.hanzo.ai
- Email: support@hanzo.ai