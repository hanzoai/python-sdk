# Hanzo AI Client Library

[![PyPI version](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)

A unified AI client library providing access to 100+ LLM providers through a single OpenAI-compatible interface. Part of the [Hanzo AI SDK ecosystem](https://github.com/hanzoai/python-sdk).

## Features

- **100+ LLM Providers**: OpenAI, Anthropic, Google, AWS Bedrock, Azure, and more
- **OpenAI-Compatible**: Drop-in replacement for `openai` package
- **Unified Gateway**: Route requests through Hanzo LLM proxy for cost optimization
- **Type Safety**: Full TypeScript-style type hints for all APIs
- **Async Support**: Both sync and async clients
- **Cost Tracking**: Built-in usage monitoring and rate limiting

## Installation

```sh
pip install hanzoai
```

## Quick Start

```python
from hanzoai import Hanzo

# Initialize client (uses HANZO_API_KEY env var by default)
client = Hanzo()

# Chat completions (OpenAI-compatible)
response = client.chat.completions.create(
    model="gpt-4",  # or any supported model
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)

print(response.choices[0].message.content)
```

## Supported Models

### OpenAI
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`
- `gpt-3.5-turbo`

### Anthropic
- `claude-3-5-sonnet`, `claude-3-opus`, `claude-3-haiku`

### Google
- `gemini-pro`, `gemini-1.5-pro`

### Open Source
- `llama-3-70b`, `llama-3-8b`
- `mixtral-8x7b`, `mixtral-8x22b`
- `qwen-2-72b`

And 90+ more models from providers like AWS Bedrock, Azure, Together AI, Replicate, and others.

## Usage Examples

### Basic Chat
```python
from hanzoai import Hanzo

client = Hanzo(api_key="your-hanzo-api-key")

response = client.chat.completions.create(
    model="claude-3-5-sonnet",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    max_tokens=1000,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### Streaming Responses
```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### Async Client
```python
import asyncio
from hanzoai import AsyncHanzo

async def main():
    client = AsyncHanzo(api_key="your-api-key")
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello async world!"}]
    )
    
    print(response.choices[0].message.content)

asyncio.run(main())
```

### Multiple Providers
```python
# Route different models through the same interface
responses = []

for model in ["gpt-4", "claude-3-5-sonnet", "llama-3-70b"]:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "What is AI?"}],
        max_tokens=100
    )
    responses.append((model, response.choices[0].message.content))

for model, answer in responses:
    print(f"\n{model}:")
    print(answer)
```

## Configuration

### Environment Variables
```bash
export HANZO_API_KEY="your-api-key"
export HANZO_BASE_URL="https://api.hanzo.ai"  # Optional, defaults to hanzo.ai
```

### Client Configuration
```python
client = Hanzo(
    api_key="your-api-key",
    base_url="https://api.hanzo.ai",  # Custom endpoint
    timeout=60.0,                     # Request timeout
    max_retries=3                     # Retry failed requests
)
```

## Advanced Features

### Cost Tracking
```python
# Get usage statistics
usage = client.usage.get()
print(f"Total tokens: {usage.total_tokens}")
print(f"Total cost: ${usage.total_cost}")

# Set budget limits
client.budget.create(
    limit=100.0,  # $100 monthly limit
    period="monthly"
)
```

### Custom Headers
```python
client = Hanzo(
    default_headers={
        "User-Agent": "MyApp/1.0",
        "X-Custom-Header": "value"
    }
)
```

### Error Handling
```python
from hanzoai import APIError, RateLimitError, AuthenticationError

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except APIError as e:
    print(f"API error: {e}")
```

## Drop-in OpenAI Replacement

Replace `openai` imports with `hanzoai` for instant access to 100+ models:

```python
# Before
from openai import OpenAI
client = OpenAI(api_key="...")

# After  
from hanzoai import Hanzo as OpenAI  # Alias for compatibility
client = OpenAI(api_key="...")

# Same interface, 100x more models!
```

## Integration with Hanzo Ecosystem

This package integrates seamlessly with other Hanzo AI components:

```python
# Use with Hanzo CLI
import hanzo
client = hanzo.Client()  # Auto-configured from CLI

# Use with Hanzo MCP tools
from hanzo.mcp import llm_tool
llm_tool.set_client(client)

# Use with Hanzo Agents
from hanzo.agents import Agent
agent = Agent(llm_client=client)
```

## API Compatibility

The `hanzoai` package implements the OpenAI API specification:
- Chat Completions (`/v1/chat/completions`)
- Embeddings (`/v1/embeddings`) 
- Images (`/v1/images/generations`)
- Audio (`/v1/audio/transcriptions`, `/v1/audio/speech`)
- Files (`/v1/files`)
- Fine-tuning (`/v1/fine_tuning/jobs`)

Plus Hanzo-specific extensions:
- Multi-provider routing
- Cost optimization
- Usage analytics
- Model switching

## Documentation

- **[Full API Reference](api.md)** - Complete API documentation
- **[Hanzo AI Docs](https://docs.hanzo.ai)** - Official documentation  
- **[Model Provider Guide](https://docs.hanzo.ai/providers)** - Supported models
- **[Migration Guide](https://docs.hanzo.ai/migration)** - Migrate from OpenAI

## Related Packages

- **[hanzo](https://pypi.org/project/hanzo/)** - CLI and network tools
- **[hanzo-mcp](https://pypi.org/project/hanzo-mcp/)** - MCP development environment
- **[hanzo-agents](https://pypi.org/project/hanzo-agents/)** - Multi-agent workflows

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 - see [LICENSE](../../LICENSE) for details.