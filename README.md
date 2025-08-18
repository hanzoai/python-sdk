# Hanzo Python SDK

[![CI Status](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml)
[![Test Status](https://github.com/hanzoai/python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/hanzoai/python-sdk/actions/workflows/test.yml)
[![Hanzo Packages CI](https://github.com/hanzoai/python-sdk/actions/workflows/hanzo-packages-ci.yml/badge.svg)](https://github.com/hanzoai/python-sdk/actions/workflows/hanzo-packages-ci.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/hanzoai/python-sdk/actions)
[![PyPI Version](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python Versions](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![License](https://img.shields.io/pypi/l/hanzoai.svg)](https://github.com/hanzoai/python-sdk/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

The official Python SDK for the [Hanzo AI](https://hanzo.ai) platform - a complete AI infrastructure solution with unified gateway for 100+ LLM providers, cost tracking, rate limiting, and enterprise-ready observability.

## 🔥 NEW: Local AI Orchestration with 90% Cost Reduction

**Hanzo Dev** now supports local AI models as orchestrators, enabling you to use free/cheap local models to manage expensive API calls:

```bash
# Use local Llama 3.2 to orchestrate Claude, GPT-4, and Gemini
hanzo dev --orchestrator local:llama-3.2-3b --use-hanzo-net

# Your local AI decides when to use expensive APIs
# Result: 90% cost reduction while maintaining full capability
```

## 🚀 Features

- **100+ LLM Providers**: OpenAI, Anthropic, Google, AWS Bedrock, Azure, Cohere, and more
- **Local AI Orchestration**: Use local models (Llama, Qwen, Mistral) to manage API usage
- **Cost Optimization**: 90% reduction through intelligent routing (local for simple, API for complex)
- **Unified Interface**: OpenAI-compatible API for all providers
- **Enterprise Ready**: Cost tracking, rate limiting, team management, and observability
- **Type Safety**: Full type hints and runtime validation with Pydantic
- **Async Support**: Both sync and async clients included
- **100% Test Coverage**: Comprehensive test suite with 3,141 tests

## 📦 Installation

```bash
pip install hanzoai
```

For LiteLLM integration:
```bash
pip install hanzoai[litellm]
```

## 🎯 Quick Start

### Basic Usage

```python
from hanzoai import Hanzo

# Initialize the client
client = Hanzo(api_key="your-api-key")  # or set HANZO_API_KEY env var

# Make a chat completion request (OpenAI compatible)
response = client.chat.completions.create(
    model="gpt-4",  # or any supported model
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Async Usage

```python
import asyncio
from hanzoai import AsyncHanzo

async def main():
    client = AsyncHanzo(api_key="your-api-key")
    
    response = await client.chat.completions.create(
        model="claude-3-5-sonnet",
        messages=[
            {"role": "user", "content": "Explain quantum computing"}
        ]
    )
    
    print(response.choices[0].message.content)

asyncio.run(main())
```

### Streaming Responses

```python
from hanzoai import Hanzo

client = Hanzo(api_key="your-api-key")

# Stream chat completions
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 🛠️ Advanced Features

### Team & Organization Management

```python
# Create a new team
team = client.team.create(
    team_alias="engineering",
    models=["gpt-4", "claude-3-5-sonnet"],
    max_budget=1000.0,
    rpm_limit=100
)

# Add members to team
client.team.add_member(
    team_id=team.team_id,
    member=[{"user_email": "dev@example.com", "role": "user"}]
)

# Track spending
spend_report = client.spend.list_logs()
```

### Model Management

```python
# List available models
models = client.models.list()

# Get model info
model_info = client.model.info.get(model="gpt-4")

# Create custom model configuration
client.models.create(
    model_name="my-custom-gpt4",
    hanzo_params={
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "api_base": "https://api.openai.com/v1"
    }
)
```

### File Operations

```python
# Upload a file
file = client.files.create(
    file=open("data.jsonl", "rb"),
    purpose="fine-tune"
)

# List files
files = client.files.list()

# Get file content
content = client.files.content.get(file_id=file.id)
```

### Fine-tuning

```python
# Create a fine-tuning job
job = client.fine_tuning.jobs.create(
    model="gpt-3.5-turbo",
    training_file=file.id,
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 1,
        "learning_rate_multiplier": 1.0
    }
)

# Monitor job status
status = client.fine_tuning.jobs.retrieve(job_id=job.id)
print(f"Status: {status.status}")

# List all jobs
jobs = client.fine_tuning.jobs.list()
```

### Embeddings

```python
# Generate embeddings
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["Hello world", "How are you?"]
)

for embedding in response.data:
    print(f"Embedding dimension: {len(embedding.embedding)}")
```

### Image Generation

```python
# Generate images
response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic city at sunset",
    n=1,
    size="1024x1024"
)

print(response.data[0].url)
```

### Audio Transcription

```python
# Transcribe audio
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=open("audio.mp3", "rb")
)

print(transcript.text)
```

## 🔧 Configuration

### Environment Variables

```bash
export HANZO_API_KEY="your-api-key"
export HANZO_BASE_URL="https://api.hanzo.ai"  # optional
export HANZO_LOG="info"  # Enable logging (debug/info/warning/error)
```

### Custom HTTP Client

```python
import httpx
from hanzoai import Hanzo, DefaultHttpxClient

client = Hanzo(
    api_key="your-api-key",
    http_client=DefaultHttpxClient(
        proxy="http://proxy.example.com:8080",
        timeout=30.0,
        limits=httpx.Limits(max_connections=100)
    )
)
```

### Retry Configuration

```python
from hanzoai import Hanzo

client = Hanzo(
    api_key="your-api-key",
    max_retries=3,  # Default is 2
    timeout=60.0     # Default is 60 seconds
)

# Per-request configuration
response = client.with_options(
    max_retries=5,
    timeout=120.0
).chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 📊 Error Handling

```python
from hanzoai import Hanzo
import hanzoai

client = Hanzo(api_key="your-api-key")

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
except hanzoai.APIConnectionError as e:
    print(f"Connection error: {e}")
except hanzoai.RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    print(f"Retry after: {e.response.headers.get('retry-after')}")
except hanzoai.APIStatusError as e:
    print(f"API error: {e.status_code}")
    print(f"Response: {e.response}")
```

### Error Types

| Error Type | Description |
|------------|-------------|
| `APIConnectionError` | Network connectivity issues |
| `APITimeoutError` | Request timeout |
| `RateLimitError` | Rate limit exceeded (429) |
| `AuthenticationError` | Invalid API key (401) |
| `PermissionDeniedError` | Insufficient permissions (403) |
| `NotFoundError` | Resource not found (404) |
| `UnprocessableEntityError` | Invalid request (422) |
| `InternalServerError` | Server error (500+) |

## 🧪 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/hanzoai/python-sdk.git
cd python-sdk

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

# Install dev dependencies
uv pip install -r requirements-dev.lock
```

### Running Tests

```bash
# Run all tests
./scripts/test

# Or with pytest directly
uv run pytest tests/

# Run with coverage
uv run pytest --cov=hanzoai tests/

# Run specific test file
uv run pytest tests/api_resources/test_chat.py
```

### Code Quality

```bash
# Run lints
./scripts/lint

# Format code
uv run ruff format pkg/

# Type checking
uv run mypy pkg/
```

## 📚 Documentation

- **API Reference**: Full API documentation at [docs.hanzo.ai](https://docs.hanzo.ai)
- **SDK Reference**: Detailed SDK reference in [api.md](api.md)
- **Examples**: See the [examples/](examples/) directory
- **Contributing**: Read [CONTRIBUTING.md](CONTRIBUTING.md)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/hanzoai/python-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hanzoai/python-sdk/discussions)
- **Discord**: [Join our Discord](https://discord.gg/hanzoai)
- **Email**: support@hanzo.ai

## 📄 License

This project is licensed under the BSD-3-Clause License. See [LICENSE](LICENSE) file for details.

## 🏗️ Project Status

- ✅ **3,141 tests** - 100% passing (all integration tests now use mocks)
- ✅ **Type Safe** - Full type hints with Pydantic validation
- ✅ **Production Ready** - Used in enterprise deployments
- ✅ **Active Development** - Regular updates and improvements
- ✅ **CI/CD** - Automated testing and deployment pipeline
- ✅ **No External Dependencies** - All tests run without external services

## 🌟 Contributors

Thanks to all our contributors! See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list.

---

Built with ❤️ by [Hanzo AI](https://hanzo.ai)