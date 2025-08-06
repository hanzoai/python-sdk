# Hanzo Router

<h1 align="center">
        🚅 Hanzo Router
    </h1>
    <p align="center">
        <p align="center">Unified LLM Gateway for the Hanzo AI Platform</p>
        <p align="center">Call all LLM APIs using the OpenAI format [Bedrock, Huggingface, VertexAI, TogetherAI, Azure, OpenAI, Groq etc.]
        <br>
    </p>

<h4 align="center"><a href="https://docs.hanzo.ai/router" target="_blank">Hanzo Router Docs</a> | <a href="https://hanzo.ai/enterprise"target="_blank">Enterprise Tier</a></h4>

Hanzo Router is a unified LLM gateway based on Router v1.74.3, providing:

- **Unified Interface**: Translate inputs to 100+ provider endpoints (completion, embedding, image generation)
- **Consistent Output**: Text responses always available at `['choices'][0]['message']['content']`
- **Intelligent Routing**: Retry/fallback logic across multiple deployments
- **Enterprise Features**: Set budgets & rate limits per project, API key, or model
- **MCP Integration**: Full Model Context Protocol support for enhanced AI capabilities

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/hanzoai/router
cd router

# Set up environment
export ANTHROPIC_API_KEY=your-key-here
# Optional: export OPENAI_API_KEY=...

# Start Hanzo Router
docker compose up
```

### Local Development

```bash
# Install dependencies
pip install -e ".[proxy]"

# Start the router
router --config config.yaml --port 4000
```

## Configuration

Create a `config.yaml` file:

```yaml
model_list:
  - model_name: gpt-4
    router_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY
      
  - model_name: claude-3-opus
    router_params:
      model: anthropic/claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: ${ROUTER_MASTER_KEY:-sk-router-master-key}
  database_url: ${DATABASE_URL}
```

## Usage Examples

### OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-router-master-key",
    base_url="http://localhost:4000/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### cURL

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-router-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Features

### 🔄 Load Balancing & Failover
- Automatic retry logic with exponential backoff
- Intelligent routing between providers
- Health checks for model availability

### 💰 Cost Management
- Track spending per API key, user, or team
- Set budgets with automatic cutoffs
- Detailed cost analytics and reporting

### 🔐 Security & Auth
- API key management with scopes
- JWT authentication support
- Team-based access control

### 📊 Observability
- OpenTelemetry integration
- Prometheus metrics
- Custom callbacks for logging

### 🛡️ Guardrails
- Content moderation (Azure, OpenAI)
- PII detection and redaction
- Custom guardrail support

### 🔧 MCP Support
- Full Model Context Protocol integration
- Tool calling across all providers
- Standardized tool response format

## Supported Providers

<details>
<summary>View all 100+ supported providers</summary>

- OpenAI
- Anthropic (Claude)
- Google (Gemini, Vertex AI)
- AWS Bedrock
- Azure OpenAI
- Cohere
- Hugging Face
- Together AI
- Replicate
- Groq
- Mistral AI
- Perplexity
- DeepInfra
- AI21
- NLP Cloud
- Voyage AI
- Xinference
- FriendliAI
- And many more...

</details>

## Deployment

### Production (Docker)

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
kubectl apply -f deploy/kubernetes/
```

### Hanzo Platform

```bash
hanzo deploy router
```

## Development

### Setup

```bash
# Clone and install
git clone https://github.com/hanzoai/router
cd router
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black .
ruff check --fix .
```

### Architecture

```
router/
├── router/           # Core library
│   ├── llms/         # Provider implementations
│   ├── router.py     # Load balancing logic
│   └── proxy/        # API gateway server
├── tests/            # Test suite
├── docs/             # Documentation
└── enterprise/       # Enterprise features
```

## Migration from Router

Hanzo Router is fully compatible with Router. To migrate:

1. Replace Router imports with Hanzo Router
2. Update configuration files to use Hanzo branding
3. Change environment variables (optional)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

## License

Hanzo Router is based on Router and maintains the same MIT license. See [LICENSE](LICENSE) for details.

## Support

- Documentation: https://docs.hanzo.ai/router
- GitHub Issues: https://github.com/hanzoai/router/issues
- Enterprise Support: enterprise@hanzo.ai

---

<p align="center">Built with ❤️ by Hanzo AI</p>