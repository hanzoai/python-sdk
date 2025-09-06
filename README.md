# Hanzo Python SDK

[![CI](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

The official Python SDK for the Hanzo AI platform, providing unified access to 100+ LLM providers through a single OpenAI-compatible API interface.

## 🚀 Features

- **Unified API**: Single interface for 100+ LLM providers (OpenAI, Anthropic, Google, Meta, etc.)
- **OpenAI Compatible**: Drop-in replacement for OpenAI SDK
- **Enterprise Features**: Cost tracking, rate limiting, observability
- **Local AI Support**: Run models locally with node infrastructure
- **Model Context Protocol (MCP)**: Advanced tool use and context management
- **Agent Framework**: Build and orchestrate AI agents
- **Memory Management**: Persistent memory and RAG capabilities
- **Network Orchestration**: Distributed AI compute capabilities

## 📦 Installation

### Basic Installation

```bash
pip install hanzoai
```

### Full Installation (All Features)

```bash
pip install "hanzoai[all]"
```

### Development Installation

```bash
git clone https://github.com/hanzoai/python-sdk.git
cd python-sdk
make setup
```

## 🎯 Quick Start

### Basic Usage

```python
from hanzoai import Hanzo

# Initialize client
client = Hanzo(api_key="your-api-key")

# Chat completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Using Different Providers

```python
# Use Claude
response = client.chat.completions.create(
    model="claude-3-opus-20240229",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Use local models
response = client.chat.completions.create(
    model="llama2:7b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## 🏗️ Architecture

### Package Structure

```
python-sdk/
├── pkg/
│   ├── hanzo/          # CLI and orchestration tools
│   ├── hanzo-mcp/      # Model Context Protocol implementation
│   ├── hanzo-agents/   # Agent framework
│   ├── hanzo-network/  # Distributed network capabilities
│   ├── hanzo-memory/   # Memory and RAG
│   ├── hanzo-aci/      # AI code intelligence
│   ├── hanzo-repl/     # Interactive REPL
│   └── hanzoai/        # Core SDK
```

### Core Components

#### 1. **Hanzo CLI** (`hanzo`)
Command-line interface for AI operations:

```bash
# Chat with AI
hanzo chat

# Start local node
hanzo node start

# Manage router
hanzo router start

# Interactive REPL
hanzo repl
```

#### 2. **Model Context Protocol** (`hanzo-mcp`)
Advanced tool use and context management:

```python
from hanzo_mcp import create_mcp_server

server = create_mcp_server()
server.register_tool(my_tool)
server.start()
```

#### 3. **Agent Framework** (`hanzo-agents`)
Build and orchestrate AI agents:

```python
from hanzo_agents import Agent, Swarm

agent = Agent(
    name="researcher",
    model="gpt-4",
    instructions="You are a research assistant"
)

swarm = Swarm([agent])
result = await swarm.run("Research quantum computing")
```

#### 4. **Network Orchestration** (`hanzo-network`)
Distributed AI compute:

```python
from hanzo_network import LocalComputeNode, DistributedNetwork

node = LocalComputeNode(node_id="node-001")
network = DistributedNetwork()
network.register_node(node)
```

#### 5. **Memory Management** (`hanzo-memory`)
Persistent memory and RAG:

```python
from hanzo_memory import MemoryService

memory = MemoryService()
await memory.store("key", "value")
result = await memory.retrieve("key")
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install Python 3.10+
make install-python

# Setup virtual environment
make setup

# Install development dependencies
make dev
```

### Running Tests

```bash
# Run all tests
make test

# Run specific package tests
make test-hanzo
make test-mcp
make test-agents

# Run with coverage
make test-coverage
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check
```

### Building Packages

```bash
# Build all packages
make build

# Build specific package
cd pkg/hanzo && uv build
```

## 📚 Documentation

### Package Documentation

- [Hanzo CLI Documentation](pkg/hanzo/README.md)
- [MCP Documentation](pkg/hanzo-mcp/README.md)
- [Agents Documentation](pkg/hanzo-agents/README.md)
- [Network Documentation](pkg/hanzo-network/README.md)
- [Memory Documentation](pkg/hanzo-memory/README.md)

### API Reference

See the [API documentation](https://docs.hanzo.ai/python-sdk) for detailed API reference.

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
HANZO_API_KEY=your-api-key
HANZO_BASE_URL=https://api.hanzo.ai

# Router Configuration
HANZO_ROUTER_URL=http://localhost:4000/v1

# Node Configuration
HANZO_NODE_URL=http://localhost:8000/v1

# Logging
HANZO_LOG_LEVEL=INFO
```

### Configuration File

Create `~/.hanzo/config.yaml`:

```yaml
api:
  key: your-api-key
  base_url: https://api.hanzo.ai

router:
  url: http://localhost:4000/v1
  
node:
  url: http://localhost:8000/v1
  workers: 4
  
logging:
  level: INFO
```

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t hanzo-sdk .

# Run container
docker run -p 8000:8000 hanzo-sdk
```

### Docker Compose

```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up router
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

### Code Standards

- Follow PEP 8
- Use type hints
- Write tests for new features
- Update documentation
- Run `make lint` before committing

## 📊 Performance

### Benchmarks

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Chat Completion | 50ms | 20 req/s |
| Embedding | 10ms | 100 req/s |
| Local Inference | 200ms | 5 req/s |

### Optimization Tips

- Use streaming for long responses
- Enable caching for repeated queries
- Use batch operations when possible
- Configure appropriate timeouts

## 🔒 Security

- API keys are encrypted at rest
- All communications use TLS 1.3+
- Regular security audits
- SOC 2 Type II certified

Report security issues to security@hanzo.ai

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the API specification
- Anthropic for Claude integration
- The open-source community

## 📞 Support

- Documentation: https://docs.hanzo.ai
- Discord: https://discord.gg/hanzo
- Email: support@hanzo.ai
- GitHub Issues: https://github.com/hanzoai/python-sdk/issues

## 🗺️ Roadmap

- [ ] Multi-modal support (images, audio, video)
- [ ] Enhanced caching strategies
- [ ] WebSocket streaming
- [ ] Browser SDK
- [ ] Mobile SDKs (iOS, Android)

---

Built with ❤️ by the Hanzo team